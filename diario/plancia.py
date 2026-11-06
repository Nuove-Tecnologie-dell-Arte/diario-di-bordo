"""La plancia: pagina riservata per cambiare i testi dell'interfaccia dal
browser, senza aprire `testi.json` a mano.

    GET  /plancia              accesso (form della password) oppure il pannello
    POST /plancia/entra        login
    POST /plancia/esci         logout
    POST /plancia/salva        salva i testi cambiati
    POST /plancia/ripristina   rimette il predefinito di una chiave

È accesa solo se in `.env` c'è DIARIO_PLANCIA_PASSWORD; altrimenti ogni
percorso /plancia risponde 404 come una pagina che non esiste.

Sicurezza:
- password confrontata a tempo costante; tentativi falliti limitati per IP
  (solo un'impronta, come in limiti.py) e in totale, in memoria;
- sessione in un cookie firmato con lo stesso HMAC dei gettoni dei browser
  (limiti._firma), con scadenza, HttpOnly, SameSite=Strict, Secure via HTTPS;
  la firma include un'impronta della password, quindi cambiarla chiude tutte
  le sessioni;
- ogni POST controlla l'Origin (se c'è) e, dopo il login, un token CSRF
  legato alla sessione;
- tutto ciò che si stampa nella pagina passa da html.escape; la pagina ha
  noindex e una Content-Security-Policy con nonce.

Il salvataggio scrive in testi.json solo le chiavi diverse dal predefinito
(più quelle sconosciute già presenti nel file, lasciate com'erano), in modo
atomico (file temporaneo nella stessa cartella + os.replace) e sotto un lock.
Se il file esistente non è JSON valido non lo si sovrascrive senza una
conferma esplicita, e prima se ne fa una copia .bak.

La plancia non legge né mostra mai pensieri o IP.
"""

import hashlib
import hmac
import html
import json
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse, urlencode

from diario import config, limiti, testi

PERCORSO = "/plancia"
NOME_COOKIE = "diario_plancia"
DURATA_SESSIONE_S = 8 * 3600
MAX_CORPO = 512 * 1024
MAX_VALORE = 5000

# Tentativi di login falliti: 5 ogni 15 minuti per IP, 30 in totale.
FINESTRA_TENTATIVI_S = 15 * 60
MAX_TENTATIVI_IP = 5
MAX_TENTATIVI_TOTALI = 30

ORDINE_NAMESPACE = ["comune", "home", "archivio", "server"]
_RE_SEGNAPOSTO = re.compile(r"\{(\w+)\}")

_lock_tentativi = threading.Lock()
_falliti_ip = limiti._Finestra(FINESTRA_TENTATIVI_S)
_falliti_tutti = limiti._Finestra(FINESTRA_TENTATIVI_S)
_lock_file = threading.Lock()
_lock_revocate = threading.Lock()
_revocate: dict[str, float] = {}  # nonce di sessione chiuse con Esci -> scadenza


def attiva() -> bool:
    return bool(config.PLANCIA_PASSWORD)


# --- Sessione e CSRF ------------------------------------------------------

def _impronta_password() -> str:
    return hashlib.sha256(b"plancia:" + config.PLANCIA_PASSWORD.encode()).hexdigest()[:12]


def _firma_sessione(nonce: str, emessa: str) -> str:
    return limiti._firma(f"plancia.{nonce}.{emessa}.{_impronta_password()}")


def nuova_sessione() -> str:
    nonce = secrets.token_hex(16)
    emessa = str(int(time.time()))
    return f"{nonce}.{emessa}.{_firma_sessione(nonce, emessa)}"


def leggi_sessione(valore: str | None) -> str | None:
    """Il nonce della sessione se il cookie è valido e non scaduto, altrimenti None."""
    if not valore or not attiva():
        return None
    parti = valore.split(".")
    if len(parti) != 3:
        return None
    nonce, emessa, firma = parti
    if not hmac.compare_digest(firma, _firma_sessione(nonce, emessa)):
        return None
    try:
        eta = time.time() - int(emessa)
    except ValueError:
        return None
    if eta < 0 or eta > DURATA_SESSIONE_S:
        return None
    with _lock_revocate:
        if nonce in _revocate:
            return None
    return nonce


def revoca(nonce: str) -> None:
    adesso = time.time()
    with _lock_revocate:
        for n, scade in list(_revocate.items()):
            if scade < adesso:
                del _revocate[n]
        _revocate[nonce] = adesso + DURATA_SESSIONE_S


def token_csrf(nonce: str) -> str:
    return limiti._firma(f"plancia-csrf.{nonce}")


def password_giusta(tentativo: str) -> bool:
    return hmac.compare_digest(tentativo.encode("utf-8"), config.PLANCIA_PASSWORD.encode("utf-8"))


# --- Limite dei tentativi -------------------------------------------------

def bloccato(ip: str) -> bool:
    adesso = time.time()
    chiave = limiti._ip_anonimo(ip)
    with _lock_tentativi:
        _falliti_ip.sfoltisci(adesso)
        _falliti_tutti.sfoltisci(adesso)
        return (_falliti_ip.conta(chiave, adesso) >= MAX_TENTATIVI_IP
                or _falliti_tutti.conta("tutti", adesso) >= MAX_TENTATIVI_TOTALI)


def registra_fallito(ip: str) -> None:
    adesso = time.time()
    with _lock_tentativi:
        _falliti_ip.registra(limiti._ip_anonimo(ip), adesso)
        _falliti_tutti.registra("tutti", adesso)


# --- File dei testi -------------------------------------------------------

def predefiniti() -> dict[str, str]:
    return json.loads(testi.PREDEFINITI.read_text(encoding="utf-8"))


def leggi_override() -> tuple[dict, str | None]:
    """(contenuto grezzo di testi.json, errore). Se manca: ({}, None).
    Se non è valido: ({}, descrizione dell'errore)."""
    percorso = config.TESTI_PATH
    if not percorso.exists():
        return {}, None
    try:
        dati = json.loads(percorso.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as e:
        return {}, f"non si legge ({e.__class__.__name__})"
    except ValueError as e:
        return {}, f"non è JSON valido ({e})"
    if not isinstance(dati, dict):
        return {}, "non è un oggetto JSON {\"chiave\": \"testo\"}"
    return dati, None


def _come_testo(v) -> str | None:
    # Stessa regola di testi._leggi: valgono stringhe e numeri.
    return str(v) if isinstance(v, (str, int, float)) else None


def valori_attuali(pred: dict[str, str], override: dict) -> dict[str, str]:
    attuali = dict(pred)
    for k, v in override.items():
        if k in pred and _come_testo(v) is not None:
            attuali[k] = _come_testo(v)
    return attuali


def segnaposto(testo: str) -> list[str]:
    return sorted(set(_RE_SEGNAPOSTO.findall(testo)))


def impronta(testo: str) -> str:
    return hashlib.sha256(testo.encode("utf-8")).hexdigest()[:20]


def _scrivi(dati: dict, pred: dict[str, str]) -> None:
    """Scrive in testi.json solo ciò che differisce dal predefinito, atomicamente."""
    uscita = {}
    for k, v in dati.items():
        if k in pred and _come_testo(v) == pred[k]:
            continue
        uscita[k] = v
    percorso = config.TESTI_PATH
    percorso.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{percorso.name}.", suffix=".tmp", dir=percorso.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(uscita.items())), f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        if percorso.exists():
            try:
                os.chmod(tmp, percorso.stat().st_mode & 0o777)
            except OSError:
                pass
        else:
            os.chmod(tmp, 0o644)
        os.replace(tmp, percorso)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _backup() -> str:
    percorso = config.TESTI_PATH
    nome = f"{percorso.name}.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
    shutil.copy2(percorso, percorso.with_name(nome))
    return nome


def salva(modulo: dict[str, str]) -> tuple[str, dict, dict[str, str]]:
    """Applica i campi del form. Restituisce (esito, parametri, errori per chiave).
    esito: 'salvato' | 'nessuna' | 'errori' | 'rotto'."""
    pred = predefiniti()
    with _lock_file:
        override, errore_file = leggi_override()
        if errore_file and modulo.get("sovrascrivi_rotto") != "1":
            return "rotto", {}, {}
        attuali = valori_attuali(pred, override)
        modifiche: dict[str, str] = {}
        errori: dict[str, str] = {}
        for k, predefinito in pred.items():
            if f"v:{k}" not in modulo or f"o:{k}" not in modulo:
                continue
            nuovo = modulo[f"v:{k}"].replace("\r\n", "\n").replace("\r", "\n")
            if impronta(nuovo) == modulo[f"o:{k}"]:
                continue  # campo non toccato: vale quello che c'è nel file adesso
            if len(nuovo) > MAX_VALORE:
                errori[k] = f"Troppo lungo: al massimo {MAX_VALORE} caratteri."
                continue
            attesi, trovati = segnaposto(predefinito), segnaposto(nuovo)
            if attesi != trovati:
                mancano = [f"{{{s}}}" for s in attesi if s not in trovati]
                in_piu = [f"{{{s}}}" for s in trovati if s not in attesi]
                parti = []
                if mancano:
                    parti.append("manca " + ", ".join(mancano))
                if in_piu:
                    parti.append("non previsto " + ", ".join(in_piu))
                errori[k] = "Segnaposto sbagliati: " + "; ".join(parti) + "."
                continue
            if nuovo != attuali[k]:
                modifiche[k] = nuovo
        if errori:
            return "errori", {}, errori
        if not modifiche:
            return "nessuna", {}, {}
        parametri = {"n": str(len(modifiche))}
        if errore_file:
            parametri["bak"] = _backup()
            override = {}
        override.update(modifiche)
        _scrivi(override, pred)
    return "salvato", parametri, {}


def ripristina(chiave: str) -> tuple[str, dict]:
    pred = predefiniti()
    if chiave not in pred:
        return "sconosciuta", {}
    with _lock_file:
        override, errore_file = leggi_override()
        if errore_file:
            return "rotto", {}
        if chiave not in override:
            return "nessuna", {}
        del override[chiave]
        _scrivi(override, pred)
    return "ripristinato", {"chiave": chiave}


# --- Pagine ---------------------------------------------------------------

def e(valore) -> str:
    return html.escape(str(valore), quote=True)


ESITI = {
    "salvato": "Salvato: {n} testi cambiati. Il sito li mostra già.",
    "nessuna": "Nessuna modifica da salvare.",
    "ripristinato": "Ripristinato il predefinito di {chiave}.",
    "rotto": "testi.json non è valido: niente è stato scritto. Per sovrascriverlo spunta la conferma qui sopra.",
    "sconosciuta": "Chiave sconosciuta.",
    "uscito": "Sei uscito dalla plancia.",
}

STILE = """
.plancia-colonna { max-width: 760px; }
.plancia-esci { margin: 0; }
.plancia-esci button {
  min-height: 44px; padding: 0 12px; font: inherit; font-weight: 600; color: var(--testo-2);
  background: none; border: 0; border-radius: var(--raggio-campo); cursor: pointer;
}
.plancia-esci button:hover { color: var(--testo); background: var(--fondo); }
.plancia-campo, .plancia textarea {
  width: 100%; font: inherit; color: var(--testo); background: var(--campo);
  border: 1px solid var(--bordo-campo); border-radius: var(--raggio-campo);
  transition: border-color .15s, box-shadow .15s;
}
.plancia-campo { min-height: 50px; padding: 0 16px; }
.plancia-campo:hover { border-color: var(--testo-2); }
.plancia-campo:focus-visible { outline: none; border-color: var(--accento); box-shadow: 0 0 0 1px var(--accento); }
.plancia textarea { min-height: 0; max-height: 50vh; font-size: 1rem; line-height: 1.5; padding: 10px 14px; }
.plancia-login { display: grid; gap: 18px; max-width: 420px; }
.plancia-avviso {
  margin: 0 0 20px; padding: 14px 16px; background: var(--scheda);
  border: 1px solid var(--linea); border-left: 4px solid var(--accento); border-radius: var(--raggio-campo);
}
.plancia-avviso.grave { border-left-color: var(--errore); }
.plancia-avviso p { margin: 0 0 8px; }
.plancia-avviso p:last-child { margin: 0; }
.plancia-avviso label { display: flex; gap: 10px; align-items: center; min-height: 44px; font-weight: 600; cursor: pointer; }
.plancia-strumenti { display: grid; gap: 10px; margin: 0 0 20px; }
.plancia-spunta { display: flex; gap: 10px; align-items: center; min-height: 44px; font-weight: 600; color: var(--testo-2); cursor: pointer; }
.plancia-spunta input, .plancia-avviso input { width: 20px; height: 20px; margin: 0; }
.plancia-gruppo { margin: 0 0 28px; }
.plancia-gruppo h2 { font-size: 1.375rem; margin: 0 0 12px; display: flex; gap: 10px; align-items: baseline; }
.plancia-gruppo h2 .n { font-size: .9375rem; font-weight: 500; color: var(--testo-2); font-variant-numeric: tabular-nums; }
.plancia-voci { display: grid; gap: 12px; }
.voce { background: var(--scheda); border: 1px solid var(--linea); border-radius: var(--raggio-campo); padding: 14px 16px; display: grid; gap: 8px; min-width: 0; }
.voce.modificata { border-left: 4px solid var(--accento); }
.voce.sbagliata { border-color: var(--errore); box-shadow: 0 0 0 1px var(--errore); }
.voce-testa { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; }
.voce-testa label { font-weight: 700; overflow-wrap: anywhere; }
.plancia code { font-family: var(--mono); font-size: .875rem; }
.stato { font-size: .875rem; font-weight: 600; padding: 1px 8px; border-radius: var(--raggio); border: 1px solid var(--bordo-campo); color: var(--testo-2); }
.modificata .stato { border-color: var(--accento); color: var(--accento); }
.voce-predefinito { margin: 0; font-size: .9375rem; color: var(--testo-2); white-space: pre-wrap; overflow-wrap: anywhere; }
.voce-predefinito b { font-weight: 600; }
.voce-sotto { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 12px; font-size: .9375rem; color: var(--testo-2); }
.voce-sotto .bottone { min-height: 44px; padding: 0 16px; font-size: .9375rem; }
.voce .errore-campo { margin: 0; }
.plancia-salva {
  position: sticky; bottom: 0; z-index: 2; margin: 8px -16px 0; padding: 12px 16px;
  background: var(--barra); border-top: 1px solid var(--linea);
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px;
}
.plancia-salva .bottone { flex: 1 1 auto; }
.plancia-salva p { margin: 0; font-size: .9375rem; color: var(--testo-2); }
.plancia-nascosto { position: absolute; width: 0; height: 0; overflow: hidden; }
@media (min-width: 760px) {
  .plancia-salva { margin: 8px 0 0; border: 1px solid var(--linea); border-radius: var(--raggio-campo); }
  .plancia-salva .bottone { flex: none; }
}
"""

SCRIPT = """
(function () {
  var cerca = document.getElementById("cerca-chiave");
  var solo = document.getElementById("solo-modificati");
  var conta = document.getElementById("conta-visibili");
  var voci = Array.prototype.slice.call(document.querySelectorAll(".voce"));
  var gruppi = Array.prototype.slice.call(document.querySelectorAll(".plancia-gruppo"));
  function filtra() {
    var q = cerca.value.trim().toLowerCase(), n = 0;
    voci.forEach(function (v) {
      var ok = (!q || v.getAttribute("data-cerca").indexOf(q) !== -1) && (!solo.checked || v.classList.contains("modificata"));
      v.hidden = !ok; if (ok) n++;
    });
    gruppi.forEach(function (g) { g.hidden = !g.querySelector(".voce:not([hidden])"); });
    conta.textContent = n === 1 ? "1 testo" : n + " testi";
  }
  if (cerca) {
    cerca.addEventListener("input", filtra);
    solo.addEventListener("change", filtra);
    document.getElementById("form-cerca").addEventListener("submit", function (ev) { ev.preventDefault(); filtra(); });
    filtra();
  }
  var principale = document.getElementById("form-testi"), sporco = false;
  if (principale) {
    principale.addEventListener("input", function () { sporco = true; });
    principale.addEventListener("submit", function () { sporco = false; });
    window.addEventListener("beforeunload", function (ev) { if (sporco) { ev.preventDefault(); ev.returnValue = ""; } });
    var rip = document.getElementById("form-ripristino");
    if (rip) rip.addEventListener("submit", function () { sporco = false; });
    var esci = document.getElementById("form-esci");
    if (esci) esci.addEventListener("submit", function () { sporco = false; });
  }
})();
"""


def _documento(titolo: str, corpo: str, nonce: str, barra_extra: str = "") -> bytes:
    pagina = f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <title>{e(titolo)}</title>
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#d6d8df" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#16161e" media="(prefers-color-scheme: dark)">
  <link rel="stylesheet" href="/style.css">
  <style nonce="{nonce}">{STILE}</style>
</head>
<body class="plancia">
  <a class="salta" href="#contenuto">Vai al contenuto</a>
  <header class="barra">
    <div class="barra-dentro">
      <a class="marchio" href="/">
        <span class="striscia" aria-hidden="true"><i data-gruppo="anno-1"></i><i data-gruppo="anno-2"></i><i data-gruppo="anno-3"></i><i data-gruppo="anno-4"></i><i data-gruppo="anno-5"></i><i data-gruppo="fuori-corso"></i><i data-gruppo="ex-allievi"></i><i data-gruppo="docenti"></i></span>
        <span>Plancia</span>
      </a>
      {barra_extra}
    </div>
  </header>
  <main id="contenuto" class="pagina">
{corpo}
  </main>
  <svg class="plancia-nascosto" aria-hidden="true">
    <symbol id="i-cerca" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></symbol>
    <symbol id="i-avviso" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.01"/></symbol>
  </svg>
  <script nonce="{nonce}">{SCRIPT}</script>
</body>
</html>
"""
    return pagina.encode("utf-8")


def pagina_login(nonce: str, messaggio: str = "") -> bytes:
    corpo = f"""    <section class="intestazione">
      <h1>Plancia</h1>
      <p>Accesso riservato a chi cura il diario.</p>
    </section>
    <form class="plancia-login" method="post" action="{PERCORSO}/entra">
      <div>
        <label class="etichetta" for="password">Password</label>
        <input class="plancia-campo" type="password" id="password" name="password" autocomplete="current-password" required autofocus>
      </div>
      <p class="messaggio" role="alert">{e(messaggio)}</p>
      <div><button class="bottone" type="submit">Entra</button></div>
    </form>"""
    return _documento("Plancia", corpo, nonce)


def pagina_pannello(nonce: str, sessione: str, esito: str = "", parametri: dict | None = None,
                    inviati: dict[str, str] | None = None, errori: dict[str, str] | None = None,
                    cerca: str = "", solo_modificati: bool = False) -> bytes:
    pred = predefiniti()
    override, errore_file = leggi_override()
    attuali = valori_attuali(pred, override)
    inviati = inviati or {}
    errori = errori or {}
    csrf = e(token_csrf(sessione))
    q = cerca.strip().lower()

    avvisi = []
    if esito in ESITI:
        testo = ESITI[esito].format_map({"n": "", "chiave": "", **(parametri or {})})
        grave = " grave" if esito in ("rotto", "sconosciuta") else ""
        extra = f"<p>Copia del file vecchio: <code>{e(parametri['bak'])}</code></p>" if (parametri or {}).get("bak") else ""
        avvisi.append(f'<div class="plancia-avviso{grave}" role="status"><p>{e(testo)}</p>{extra}</div>')
    if errori:
        avvisi.append(f'<div class="plancia-avviso grave" role="alert"><p>Niente è stato salvato: {len(errori)} testi da correggere, segnati qui sotto.</p></div>')

    avviso_rotto = ""
    if errore_file:
        avviso_rotto = f"""<div class="plancia-avviso grave" role="alert">
        <p><b>{e(config.TESTI_PATH.name)} {e(errore_file)}.</b> Il sito sta usando i testi predefiniti.</p>
        <p>Puoi correggerlo a mano, oppure salvare da qui: il file vecchio viene prima copiato in un <code>.bak</code> accanto, poi sostituito con i soli testi che salvi adesso.</p>
        <label><input type="checkbox" name="sovrascrivi_rotto" value="1" form="form-testi"> Fai la copia .bak e sovrascrivi il file</label>
      </div>"""

    sconosciute = sorted(k for k in override if k not in pred)
    nota_sconosciute = ""
    if sconosciute:
        elenco = ", ".join(f"<code>{e(k)}</code>" for k in sconosciute)
        nota_sconosciute = f'<div class="plancia-avviso"><p>Chiavi nel file che il sito non usa (restano come sono): {elenco}</p></div>'

    per_ns: dict[str, list[str]] = {}
    for k in pred:
        per_ns.setdefault(k.split(".", 1)[0], []).append(k)
    ordine = [n for n in ORDINE_NAMESPACE if n in per_ns] + sorted(n for n in per_ns if n not in ORDINE_NAMESPACE)

    sezioni = []
    visibili = 0
    for i_ns, ns in enumerate(ordine):
        voci = []
        for k in per_ns[ns]:
            predefinito, attuale = pred[k], attuali[k]
            modificata = attuale != predefinito
            valore = inviati.get(k, attuale)
            cercabile = f"{k}\n{predefinito}\n{attuale}".lower()
            if q and q not in cercabile:
                continue
            if solo_modificati and not modificata:
                continue
            visibili += 1
            ident = f"t{len(sezioni)}-{len(voci)}"
            sp = segnaposto(predefinito)
            sp_html = ("Segnaposto da lasciare: " + " ".join(f"<code>{e('{' + s + '}')}</code>" for s in sp)) if sp else "Nessun segnaposto"
            ripristino = (f'<button class="bottone secondario" type="submit" form="form-ripristino" name="chiave" value="{e(k)}">Ripristina il predefinito</button>'
                          if modificata else "")
            errore = ""
            if k in errori:
                errore = (f'<p class="errore-campo" id="{ident}-err"><svg class="icona" aria-hidden="true"><use href="#i-avviso"/></svg>'
                          f"<span>{e(errori[k])}</span></p>")
            righe = min(8, max(1, len(valore) // 60 + valore.count("\n") + 1))
            voci.append(f"""        <div class="voce{' modificata' if modificata else ''}{' sbagliata' if k in errori else ''}" data-cerca="{e(cercabile)}">
          <div class="voce-testa"><label for="{ident}"><code>{e(k)}</code></label><span class="stato">{'modificato' if modificata else 'predefinito'}</span></div>
          <textarea id="{ident}" name="v:{e(k)}" rows="{righe}" spellcheck="true"{f' aria-invalid="true" aria-describedby="{ident}-err"' if k in errori else ''}>
{e(valore)}</textarea>
          <input type="hidden" name="o:{e(k)}" value="{e(inviati.get('o:' + k) or impronta(attuale))}">
          {errore}
          <p class="voce-predefinito"><b>Predefinito:</b> {e(predefinito)}</p>
          <div class="voce-sotto"><span>{sp_html}</span>{ripristino}</div>
        </div>""")
        if voci:
            sezioni.append(f"""      <section class="plancia-gruppo" aria-labelledby="ns-{i_ns}">
        <h2 id="ns-{i_ns}"><span>{e(ns)}</span><span class="n">{len(voci)}</span></h2>
        <div class="plancia-voci">
{chr(10).join(voci)}
        </div>
      </section>""")
    if not sezioni:
        sezioni.append('<p class="vuoto">Nessun testo corrisponde alla ricerca.</p>')

    barra_extra = f"""<form class="plancia-esci" id="form-esci" method="post" action="{PERCORSO}/esci">
        <input type="hidden" name="csrf" value="{csrf}"><button type="submit">Esci</button>
      </form>"""
    corpo = f"""    <section class="intestazione">
      <h1>Plancia</h1>
      <p>I testi del sito. Si salvano in <code>{e(config.TESTI_PATH.name)}</code> solo quelli diversi dal predefinito, e il sito li mostra subito.</p>
    </section>
    <div class="plancia-colonna">
      {''.join(avvisi)}
      {avviso_rotto}
      {nota_sconosciute}
      <form class="plancia-strumenti" id="form-cerca" method="get" action="{PERCORSO}" role="search">
        <div class="ricerca">
          <label class="sr" for="cerca-chiave">Cerca tra i testi</label>
          <svg class="icona" aria-hidden="true"><use href="#i-cerca"/></svg>
          <input type="search" id="cerca-chiave" name="cerca" value="{e(cerca)}" placeholder="Cerca una chiave o un testo…" autocomplete="off" enterkeyhint="search">
        </div>
        <label class="plancia-spunta"><input type="checkbox" id="solo-modificati" name="modificati" value="1"{' checked' if solo_modificati else ''}> Solo i testi modificati</label>
        <noscript><button class="bottone secondario" type="submit">Filtra</button></noscript>
      </form>
      <form id="form-testi" method="post" action="{PERCORSO}/salva">
        <input type="hidden" name="csrf" value="{csrf}">
{chr(10).join(sezioni)}
        <div class="plancia-salva">
          <button class="bottone" type="submit">Salva le modifiche</button>
          <p aria-live="polite"><span id="conta-visibili">{visibili} testi</span> · si salvano solo quelli cambiati</p>
        </div>
      </form>
      <form id="form-ripristino" method="post" action="{PERCORSO}/ripristina">
        <input type="hidden" name="csrf" value="{csrf}">
      </form>
    </div>"""
    return _documento("Plancia · Diario di bordo", corpo, nonce, barra_extra)


# --- Richieste ------------------------------------------------------------

def _cookie_sessione(gestore) -> str | None:
    from http.cookies import SimpleCookie
    cookie = SimpleCookie()
    try:
        cookie.load(gestore.headers.get("Cookie", ""))
    except Exception:
        return None
    m = cookie.get(NOME_COOKIE)
    return m.value if m else None


def _da_proxy(gestore) -> bool:
    return config.TRUST_PROXY and gestore.client_address[0] in ("127.0.0.1", "::1")


def _via_https(gestore) -> bool:
    if not _da_proxy(gestore):
        return False
    proto = (gestore.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
    return proto == "https" or '"https"' in (gestore.headers.get("CF-Visitor") or "")


def _imposta_cookie(gestore, valore: str, max_age: int) -> str:
    sicuro = "; Secure" if _via_https(gestore) else ""
    return f"{NOME_COOKIE}={valore}; Path={PERCORSO}; Max-Age={max_age}; HttpOnly; SameSite=Strict{sicuro}"


def _origine_valida(gestore) -> bool:
    """Se il browser manda Origin (o in mancanza Referer), deve essere questo sito."""
    origine = gestore.headers.get("Origin")
    if origine is None:
        referer = gestore.headers.get("Referer")
        if not referer:
            return True  # niente da controllare: resta il token CSRF
        origine = referer
    host = urlparse(origine).netloc.lower()
    atteso = (gestore.headers.get("X-Forwarded-Host") if _da_proxy(gestore) else None) or gestore.headers.get("Host") or ""
    return bool(host) and host == atteso.split(",")[0].strip().lower()


def _invia(gestore, stato: int, corpo: bytes, nonce: str, extra: list[tuple[str, str]] | None = None) -> None:
    gestore.send_response(stato)
    gestore.send_header("Content-Type", "text/html; charset=utf-8")
    gestore.send_header("Content-Length", str(len(corpo)))
    gestore.send_header("Cache-Control", "no-store")
    gestore.send_header("X-Robots-Tag", "noindex, nofollow")
    gestore.send_header(
        "Content-Security-Policy",
        f"default-src 'self'; script-src 'nonce-{nonce}'; style-src 'self' 'nonce-{nonce}'; "
        "img-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'",
    )
    gestore._intestazioni_sicurezza()
    for k, v in extra or []:
        gestore.send_header(k, v)
    gestore.end_headers()
    gestore.wfile.write(corpo)


def _rimanda(gestore, parametri: dict | None = None, cookie: str | None = None) -> None:
    luogo = PERCORSO + ("?" + urlencode(parametri) if parametri else "")
    gestore.send_response(303)
    gestore.send_header("Location", luogo)
    gestore.send_header("Content-Length", "0")
    gestore.send_header("Cache-Control", "no-store")
    gestore.send_header("X-Robots-Tag", "noindex, nofollow")
    gestore._intestazioni_sicurezza()
    if cookie:
        gestore.send_header("Set-Cookie", cookie)
    gestore.end_headers()


def get(gestore, url) -> None:
    if url.path.rstrip("/") != PERCORSO:
        return gestore._errore(404, testi.t("server.pagina_non_trovata"))
    q = parse_qs(url.query)
    primo = lambda nome: (q.get(nome) or [""])[0]
    nonce = secrets.token_urlsafe(16)
    sessione = leggi_sessione(_cookie_sessione(gestore))
    if sessione is None:
        messaggio = ESITI["uscito"] if primo("esito") == "uscito" else ""
        return _invia(gestore, 200, pagina_login(nonce, messaggio), nonce)
    esito = primo("esito")
    parametri = {"n": primo("n")[:6], "chiave": primo("chiave")[:200], "bak": primo("bak")[:200]}
    corpo = pagina_pannello(nonce, sessione, esito if esito in ESITI else "", parametri,
                            cerca=primo("cerca")[:200], solo_modificati=primo("modificati") == "1")
    return _invia(gestore, 200, corpo, nonce)


def post(gestore, url) -> None:
    percorso = url.path.rstrip("/")
    if percorso not in (f"{PERCORSO}/entra", f"{PERCORSO}/esci", f"{PERCORSO}/salva", f"{PERCORSO}/ripristina"):
        return gestore._errore(404, testi.t("server.non_trovato"))
    nonce = secrets.token_urlsafe(16)
    try:
        lunghezza = int(gestore.headers.get("Content-Length", "0"))
    except ValueError:
        lunghezza = -1
    if lunghezza < 0 or lunghezza > MAX_CORPO:
        return gestore._errore(413, testi.t("server.richiesta_troppo_grande"))
    try:
        grezzo = gestore.rfile.read(lunghezza).decode("utf-8") if lunghezza else ""
        campi = parse_qs(grezzo, keep_blank_values=True, max_num_fields=2000)
    except (UnicodeDecodeError, ValueError):
        return gestore._errore(400, testi.t("server.richiesta_non_valida"))
    modulo = {k: v[0] for k, v in campi.items()}

    if not _origine_valida(gestore):
        return _invia(gestore, 403, pagina_login(nonce, "Richiesta rifiutata: arriva da un altro sito."), nonce)

    if percorso == f"{PERCORSO}/entra":
        ip = gestore._ip()
        if bloccato(ip):
            return _invia(gestore, 429, pagina_login(nonce, "Troppi tentativi sbagliati. Riprova tra un quarto d'ora."), nonce,
                          [("Retry-After", str(FINESTRA_TENTATIVI_S))])
        if not password_giusta(modulo.get("password", "")):
            registra_fallito(ip)
            return _invia(gestore, 401, pagina_login(nonce, "Password sbagliata."), nonce)
        return _rimanda(gestore, cookie=_imposta_cookie(gestore, nuova_sessione(), DURATA_SESSIONE_S))

    sessione = leggi_sessione(_cookie_sessione(gestore))
    if sessione is None:
        return _invia(gestore, 403, pagina_login(nonce, "Sessione scaduta: entra di nuovo."), nonce)
    if not hmac.compare_digest(modulo.get("csrf", ""), token_csrf(sessione)):
        return _invia(gestore, 403, pagina_login(nonce, "Richiesta rifiutata (token non valido). Ricarica la plancia."), nonce)

    if percorso == f"{PERCORSO}/esci":
        revoca(sessione)
        return _rimanda(gestore, {"esito": "uscito"}, _imposta_cookie(gestore, "", 0))

    if percorso == f"{PERCORSO}/ripristina":
        esito, parametri = ripristina(modulo.get("chiave", ""))
        return _rimanda(gestore, {"esito": esito, **parametri})

    esito, parametri, errori = salva(modulo)
    if esito == "errori":
        inviati = {}
        for k in predefiniti():
            if f"v:{k}" in modulo:
                inviati[k] = modulo[f"v:{k}"].replace("\r\n", "\n")
            if f"o:{k}" in modulo:
                inviati[f"o:{k}"] = modulo[f"o:{k}"]
        corpo = pagina_pannello(nonce, sessione, inviati=inviati, errori=errori)
        return _invia(gestore, 400, corpo, nonce)
    return _rimanda(gestore, {"esito": esito, **parametri})
