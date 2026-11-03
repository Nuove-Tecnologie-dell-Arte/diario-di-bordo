"""Limiti di invio contro spam e abusi, senza identificare nessuno.

L'IP non basta (una classe intera esce dalla stessa Wi-Fi) e il MAC address
non arriva al server. Si combinano quindi più freni:

1. **Gettone del browser**: un cookie firmato (HMAC) con un id casuale e
   l'ora di emissione, dato all'apertura della pagina. Senza gettone valido
   non si invia. Serve per:
   - tempo minimo tra apertura della pagina e primo invio (anti-bot);
   - pausa minima tra due invii dallo stesso browser;
   - massimo di invii all'ora per browser.
   Chi cancella i cookie ne ottiene uno nuovo, ma deve comunque riaprire la
   pagina e aspettare: abbastanza per fermare il "clicco Invia a raffica".
2. **Limite per IP** molto largo (200/ora di default): ferma solo flood
   automatici, non una classe che scrive dalla stessa rete.
3. **Tetto globale** all'ora su tutto il sito.
4. **Duplicati**: lo stesso testo non si reinvia entro 24 ore (in db.py).
5. **Campo esca** nel form (in server.py): se compilato, è un bot.

I contatori stanno in memoria: un riavvio li azzera, va bene così.
"""

import hashlib
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque

from diario import config

NOME_COOKIE = "diario_gettone"
DURATA_COOKIE_S = 60 * 60 * 24 * 365


def _firma(dato: str) -> str:
    return hmac.new(config.SEGRETO, dato.encode(), hashlib.sha256).hexdigest()[:32]


def nuovo_gettone() -> str:
    dato = f"{secrets.token_hex(12)}.{int(time.time())}"
    return f"{dato}.{_firma(dato)}"


def leggi_gettone(valore: str | None) -> tuple[str, int] | None:
    """(id, ora di emissione) se il gettone è valido, altrimenti None."""
    if not valore:
        return None
    parti = valore.split(".")
    if len(parti) != 3:
        return None
    ident, emesso, firma = parti
    if not hmac.compare_digest(firma, _firma(f"{ident}.{emesso}")):
        return None
    try:
        return ident, int(emesso)
    except ValueError:
        return None


class _Finestra:
    """Contatori a finestra scorrevole di un'ora, per chiave."""

    def __init__(self) -> None:
        self._eventi: dict[str, deque] = defaultdict(deque)

    def _pulisci(self, chiave: str, adesso: float) -> deque:
        coda = self._eventi[chiave]
        while coda and coda[0] <= adesso - 3600:
            coda.popleft()
        return coda

    def conta(self, chiave: str, adesso: float) -> int:
        return len(self._pulisci(chiave, adesso))

    def ultimo(self, chiave: str, adesso: float) -> float | None:
        coda = self._pulisci(chiave, adesso)
        return coda[-1] if coda else None

    def registra(self, chiave: str, adesso: float) -> None:
        self._eventi[chiave].append(adesso)

    def sfoltisci(self, adesso: float) -> None:
        for chiave in list(self._eventi):
            if not self._pulisci(chiave, adesso):
                del self._eventi[chiave]


_lock = threading.Lock()
_browser = _Finestra()
_ip = _Finestra()
_globale = _Finestra()
_ultima_pulizia = 0.0


def _ip_anonimo(ip: str) -> str:
    # In memoria teniamo solo un'impronta dell'IP, mai l'IP in chiaro.
    return hashlib.sha256(config.SEGRETO + ip.encode()).hexdigest()[:16]


def controlla(gettone: str | None, ip: str) -> str | None:
    """Messaggio d'errore per l'utente se l'invio va bloccato, None se può
    passare. Se passa, l'invio viene già conteggiato."""
    global _ultima_pulizia
    letto = leggi_gettone(gettone)
    if letto is None:
        return "Sessione non valida: ricarica la pagina e riprova."
    ident, emesso = letto
    adesso = time.time()
    if adesso - emesso < config.ATTESA_MINIMA_S:
        return "Un attimo di calma: aspetta qualche secondo e riprova."

    chiave_ip = _ip_anonimo(ip)
    with _lock:
        if adesso - _ultima_pulizia > 600:
            for f in (_browser, _ip, _globale):
                f.sfoltisci(adesso)
            _ultima_pulizia = adesso

        ultimo = _browser.ultimo(ident, adesso)
        if ultimo is not None and adesso - ultimo < config.PAUSA_BROWSER_S:
            attesa = int(config.PAUSA_BROWSER_S - (adesso - ultimo)) + 1
            return f"Hai appena scritto: aspetta {attesa} secondi prima del prossimo pensiero."
        if _browser.conta(ident, adesso) >= config.MAX_ORA_BROWSER:
            return "Hai scritto molto nell'ultima ora: riprova più tardi."
        if _ip.conta(chiave_ip, adesso) >= config.MAX_ORA_IP:
            return "Troppi invii da questa rete nell'ultima ora: riprova più tardi."
        if _globale.conta("tutti", adesso) >= config.MAX_ORA_GLOBALE:
            return "Il diario sta ricevendo troppi pensieri: riprova tra poco."

        _browser.registra(ident, adesso)
        _ip.registra(chiave_ip, adesso)
        _globale.registra("tutti", adesso)
    return None
