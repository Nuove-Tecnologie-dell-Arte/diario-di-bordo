"""Webserver del Diario di bordo: solo libreria standard (`http.server`).

Pagine statiche da `public/`, più queste API JSON:

    GET  /api/categorie                 elenco categorie con conteggi
    GET  /api/pensieri?categoria=&cerca=&pagina=&per_pagina=
                                        archivio paginato, dal più recente
                                        (anche /api/categorie accetta cerca=, e
                                        tutti e due dal=&al= AAAA-MM-GG inclusi)
    POST /api/pensieri                  {testo, categoria, sito}  (sito = campo esca)
    GET  /api/export?dal_id=N           tutto per altri progetti (header X-Api-Key)
    GET  /api/health                    stato del servizio
    GET  /testi.js                      testi dell'interfaccia (window.TESTI, window.T)

Più la plancia per modificare i testi (/plancia, vedi diario/plancia.py).
"""

import hmac
import json
import mimetypes
import re
import sys
from datetime import date
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from diario import config, db, limiti, plancia, testi

MAX_CORPO = 32 * 1024
mimetypes.add_type("font/woff2", ".woff2")
PAGINE = {"/": "index.html", "/archivio": "archivio.html"}


# Messaggi d'errore del filtro per data.
ERRORI_DATA = {
    "dal": "Data di inizio non valida: usa il formato AAAA-MM-GG.",
    "al": "Data di fine non valida: usa il formato AAAA-MM-GG.",
    "ordine": "La data di inizio viene dopo quella di fine.",
}
_RE_GIORNO = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def _giorni(dal: str | None, al: str | None) -> tuple[str | None, str | None, str | None]:
    """Valida `dal` e `al` (AAAA-MM-GG, giorni esistenti). Restituisce
    (dal, al, errore): vuoti diventano None, errore è None se tutto va bene."""
    valori = {}
    for nome, valore in (("dal", dal), ("al", al)):
        valore = (valore or "").strip()
        if not valore:
            valori[nome] = None
            continue
        try:
            if not _RE_GIORNO.fullmatch(valore):
                raise ValueError
            date.fromisoformat(valore)
        except ValueError:
            return None, None, testi.t(f"server.data_{nome}", ERRORI_DATA[nome])
        valori[nome] = valore
    if valori["dal"] and valori["al"] and valori["dal"] > valori["al"]:
        return None, None, testi.t("server.data_ordine", ERRORI_DATA["ordine"])
    return valori["dal"], valori["al"], None


def _e_plancia(percorso: str) -> bool:
    return percorso == plancia.PERCORSO or percorso.startswith(plancia.PERCORSO + "/")


def _int(valore: str | None, predefinito: int, minimo: int, massimo: int) -> int:
    try:
        return min(max(int(valore), minimo), massimo)
    except (TypeError, ValueError):
        return predefinito


class Gestore(BaseHTTPRequestHandler):
    server_version = "DiarioDiBordo/1.0"

    # --- utilità -------------------------------------------------------

    def log_message(self, formato, *args):  # niente IP nei log
        sys.stderr.write(f"[{self.log_date_time_string()}] {formato % args}\n")

    def _ip(self) -> str:
        diretto = self.client_address[0]
        if config.TRUST_PROXY and diretto in ("127.0.0.1", "::1"):
            cf = self.headers.get("CF-Connecting-IP")
            if cf:
                return cf.strip()
            xff = self.headers.get("X-Forwarded-For")
            if xff:
                return xff.split(",")[0].strip()
        return diretto

    def _gettone(self) -> str | None:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            return None
        m = cookie.get(limiti.NOME_COOKIE)
        return m.value if m else None

    def _intestazioni_sicurezza(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("X-Frame-Options", "DENY")

    def _json(self, stato: int, dati, extra: dict | None = None) -> None:
        corpo = json.dumps(dati, ensure_ascii=False).encode("utf-8")
        self.send_response(stato)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self._intestazioni_sicurezza()
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def _errore(self, stato: int, messaggio: str) -> None:
        self._json(stato, {"errore": messaggio})

    def _file(self, percorso: Path) -> None:
        tipo = mimetypes.guess_type(percorso.name)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo in ("application/javascript", "application/json"):
            tipo += "; charset=utf-8"
        corpo = percorso.read_bytes()
        if percorso.suffix == ".html":
            corpo = testi.applica_html(corpo.decode("utf-8")).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self._intestazioni_sicurezza()
        if percorso.suffix == ".html":
            self.send_header("Cache-Control", "no-cache")
            # Ogni pagina consegna un gettone se il browser non ne ha uno valido.
            if limiti.leggi_gettone(self._gettone()) is None:
                self.send_header(
                    "Set-Cookie",
                    f"{limiti.NOME_COOKIE}={limiti.nuovo_gettone()}; Path=/; "
                    f"Max-Age={limiti.DURATA_COOKIE_S}; HttpOnly; SameSite=Strict",
                )
        elif percorso.suffix == ".woff2":
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        else:
            self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(corpo)

    # --- GET -----------------------------------------------------------

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        primo = lambda nome: (q.get(nome) or [None])[0]

        if url.path == "/api/health":
            try:
                db.conteggi()
                return self._json(200, {"ok": True})
            except Exception as e:
                return self._json(500, {"ok": False, "errore": str(e)})

        if url.path == "/testi.js":
            corpo = testi.script_js()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-cache")
            self._intestazioni_sicurezza()
            self.end_headers()
            self.wfile.write(corpo)
            return None

        if url.path == "/api/categorie":
            dal, al, errore = _giorni(primo("dal"), primo("al"))
            if errore:
                return self._errore(400, errore)
            conti = db.conteggi((primo("cerca") or "").strip()[:200] or None, dal, al)
            return self._json(200, {
                "categorie": [
                    {"chiave": k, "nome": testi.t(f"comune.categoria.{k}", nome), "conteggio": conti[k]} for k, nome in db.CATEGORIE
                ],
                "testo_max": config.TESTO_MAX,
            })

        if url.path == "/api/pensieri":
            categoria = primo("categoria") or None
            if categoria and categoria not in db.CHIAVI_CATEGORIE:
                return self._errore(400, testi.t("server.categoria_sconosciuta"))
            cerca = (primo("cerca") or "").strip()[:200] or None
            pagina = _int(primo("pagina"), 1, 1, 100000)
            per_pagina = _int(primo("per_pagina"), 20, 1, 100)
            dal, al, errore = _giorni(primo("dal"), primo("al"))
            if errore:
                return self._errore(400, errore)
            return self._json(200, db.elenca(categoria, cerca, pagina, per_pagina, dal, al))

        if url.path == "/api/export":
            chiave = self.headers.get("X-Api-Key", "")
            if not config.EXPORT_API_KEY or not hmac.compare_digest(chiave, config.EXPORT_API_KEY):
                return self._errore(401, "unauthorized")
            return self._json(200, db.esporta(_int(primo("dal_id"), 0, 0, 2**62)))

        if url.path.startswith("/api/"):
            return self._errore(404, testi.t("server.non_trovato"))

        if _e_plancia(url.path):
            if not plancia.attiva():
                return self._errore(404, testi.t("server.pagina_non_trovata"))
            return plancia.get(self, url)

        nome = PAGINE.get(url.path.rstrip("/") or "/", url.path.lstrip("/"))
        percorso = (config.PUBLIC_DIR / nome).resolve()
        if config.PUBLIC_DIR.resolve() not in percorso.parents or not percorso.is_file():
            return self._errore(404, testi.t("server.pagina_non_trovata"))
        return self._file(percorso)

    # --- POST ----------------------------------------------------------

    def do_POST(self):
        url = urlparse(self.path)
        if _e_plancia(url.path) and plancia.attiva():
            return plancia.post(self, url)
        if url.path != "/api/pensieri":
            return self._errore(404, testi.t("server.non_trovato"))
        try:
            lunghezza = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            lunghezza = 0
        if lunghezza <= 0 or lunghezza > MAX_CORPO:
            return self._errore(413, testi.t("server.richiesta_troppo_grande"))
        try:
            dati = json.loads(self.rfile.read(lunghezza).decode("utf-8"))
            if not isinstance(dati, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            return self._errore(400, testi.t("server.richiesta_non_valida"))

        # Campo esca: invisibile agli umani, i bot lo compilano.
        if str(dati.get("sito") or "").strip():
            return self._json(201, {"ok": True})

        categoria = str(dati.get("categoria") or "")
        if categoria not in db.CHIAVI_CATEGORIE:
            return self._errore(400, testi.t("server.scegli_gruppo"))

        testo = db.normalizza_testo(str(dati.get("testo") or ""))
        if len(testo) < config.TESTO_MIN:
            return self._errore(400, testi.t("server.troppo_corto"))
        if len(testo) > config.TESTO_MAX:
            return self._errore(400, testi.t("server.troppo_lungo", max=config.TESTO_MAX))
        if db.e_duplicato(testo):
            return self._errore(409, testi.t("server.duplicato"))

        blocco = limiti.controlla(self._gettone(), self._ip())
        if blocco:
            return self._errore(429, blocco)

        pensiero = db.inserisci(testo, categoria)
        return self._json(201, {"ok": True, "pensiero": pensiero})


def avvia() -> None:
    db.init_db()
    server = ThreadingHTTPServer((config.HOST, config.PORT), Gestore)
    server.daemon_threads = True
    print(f"Diario di bordo su http://{config.HOST}:{config.PORT}/  (DB: {config.DB_PATH})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
