"""Testi mostrati all'utente, modificabili senza toccare il codice.

I predefiniti stanno in `diario/testi_predefiniti.json` (versionato).
Un file locale (`testi.json` nella root, o il percorso in DIARIO_TESTI) può
ridefinire solo alcune chiavi: le altre restano quelle predefinite.

I file si rileggono quando cambia la loro data di modifica, quindi basta
salvare `testi.json` perché il sito mostri i testi nuovi, senza riavvio.
Un JSON non valido produce un avviso nel log e si usano i predefiniti.

Chiavi piatte con namespace: `comune.*`, `home.*`, `archivio.*`, `server.*`.
Nei testi `{nome}` è un segnaposto, sostituito con i parametri passati.
"""

import html
import json
import re
import sys
import threading
from pathlib import Path

from diario import config

PREDEFINITI = Path(__file__).resolve().parent / "testi_predefiniti.json"

_lock = threading.Lock()
_firma: tuple | None = None
_testi: dict[str, str] = {}


def _mtime(percorso: Path) -> float | None:
    try:
        return percorso.stat().st_mtime_ns
    except OSError:
        return None


def _leggi(percorso: Path) -> dict[str, str]:
    """Le coppie chiave/testo del file, oppure {} (con avviso) se manca o è rotto."""
    if not percorso.is_file():
        return {}
    try:
        dati = json.loads(percorso.read_text(encoding="utf-8"))
        if not isinstance(dati, dict):
            raise ValueError("serve un oggetto JSON {\"chiave\": \"testo\"}")
    except (OSError, ValueError, UnicodeDecodeError) as e:
        sys.stderr.write(f"[testi] AVVISO: {percorso} non valido, lo ignoro ({e})\n")
        return {}
    return {str(k): str(v) for k, v in dati.items() if isinstance(v, (str, int, float))}


def tutti() -> dict[str, str]:
    """Tutti i testi correnti (predefiniti + override), riletti se cambiati."""
    global _firma, _testi
    firma = (_mtime(PREDEFINITI), _mtime(config.TESTI_PATH))
    with _lock:
        if firma != _firma:
            _testi = {**_leggi(PREDEFINITI), **_leggi(config.TESTI_PATH)}
            _firma = firma
        return _testi


def _riempi(testo: str, parametri: dict) -> str:
    if not parametri:
        return testo
    return re.sub(r"\{(\w+)\}", lambda m: str(parametri.get(m.group(1), m.group(0))), testo)


def t(chiave: str, riserva: str | None = None, **parametri) -> str:
    """Il testo per `chiave` (o `riserva`, o la chiave stessa), con i segnaposto riempiti."""
    testo = tutti().get(chiave)
    if testo is None:
        testo = riserva if riserva is not None else chiave
    return _riempi(testo, parametri)


# --- Per il frontend ---------------------------------------------------

def script_js() -> bytes:
    """Il contenuto di /testi.js: window.TESTI e window.T."""
    dati = json.dumps(tutti(), ensure_ascii=True, sort_keys=True).replace("</", "<\\/")
    return (
        "// Generato dal server da diario/testi_predefiniti.json + testi.json\n"
        f"window.TESTI = {dati};\n"
        "window.T = function (chiave, riserva, parametri) {\n"
        "  var testo = Object.prototype.hasOwnProperty.call(window.TESTI, chiave)\n"
        "    ? window.TESTI[chiave] : (riserva !== undefined ? riserva : chiave);\n"
        "  if (!parametri) return testo;\n"
        "  return String(testo).replace(/\\{(\\w+)\\}/g, function (tutto, nome) {\n"
        "    return Object.prototype.hasOwnProperty.call(parametri, nome) ? String(parametri[nome]) : tutto;\n"
        "  });\n"
        "};\n"
    ).encode("utf-8")


# Elemento con data-testo e contenuto di solo testo: <tag ... data-testo="k" ...>testo</tag>
_RE_ELEMENTO = re.compile(r'(<(\w+)\b[^>]*?\sdata-testo="([^"]+)"[^>]*>)[^<]*(</\2>)')
_RE_TAG = re.compile(r"<\w+\b[^>]*\sdata-testo-[\w-]+=\"[^\"]*\"[^>]*>")
_RE_ATTR_TESTO = re.compile(r'\sdata-testo-([\w-]+)="([^"]+)"')


def applica_html(pagina: str) -> str:
    """Mette i testi correnti nell'HTML prima di inviarlo, così non si vede
    mai il testo vecchio (e title/meta sono giusti anche senza JavaScript).
    comune.js riapplica gli stessi attributi lato browser."""
    testi = tutti()

    def elemento(m: re.Match) -> str:
        chiave = m.group(3)
        if chiave not in testi:
            return m.group(0)
        return m.group(1) + html.escape(testi[chiave], quote=False) + m.group(4)

    def tag(m: re.Match) -> str:
        s = m.group(0)
        for attr, chiave in _RE_ATTR_TESTO.findall(s):
            if chiave not in testi:
                continue
            valore = html.escape(testi[chiave], quote=True)
            nuovo = re.sub(rf'(\s{re.escape(attr)}=)"[^"]*"', lambda a: f'{a.group(1)}"{valore}"', s, count=1)
            if nuovo == s and f" {attr}=" not in s:
                nuovo = s[:-1].rstrip("/").rstrip() + f' {attr}="{valore}">'
            s = nuovo
        return s

    return _RE_TAG.sub(tag, _RE_ELEMENTO.sub(elemento, pagina))
