"""Configurazione del Diario di bordo, letta da `.env` (se c'è) e dalle
variabili d'ambiente. Nessuna dipendenza: il parser di `.env` è minimale
(righe CHIAVE=valore, `#` per i commenti)."""

import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _carica_env(percorso: Path) -> None:
    if not percorso.is_file():
        return
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("#") or "=" not in riga:
            continue
        chiave, valore = riga.split("=", 1)
        valore = valore.strip().strip('"').strip("'")
        os.environ.setdefault(chiave.strip(), valore)


_carica_env(ROOT / ".env")


def _int(nome: str, predefinito: int) -> int:
    try:
        return int(os.environ.get(nome, predefinito))
    except ValueError:
        return predefinito


def _percorso(nome: str, predefinito: str) -> Path:
    p = Path(os.environ.get(nome, predefinito))
    return p if p.is_absolute() else ROOT / p


# --- Webserver ---
HOST = os.environ.get("DIARIO_HOST", "127.0.0.1")
PORT = _int("DIARIO_PORT", 8007)
PUBLIC_DIR = ROOT / "public"

# Se true, l'IP del visitatore si legge dagli header del proxy
# (CF-Connecting-IP / X-Forwarded-For), ma solo per richieste che arrivano
# dal loopback (cioè da cloudflared o nginx sulla stessa macchina).
TRUST_PROXY = os.environ.get("DIARIO_TRUST_PROXY", "true").lower() == "true"

# --- Database ---
DB_PATH = _percorso("DIARIO_DB_PATH", "data/diario.db")

# Chiave per /api/export (header X-Api-Key), usata da Oracolo e da altri
# progetti. Vuota = export disattivato.
EXPORT_API_KEY = os.environ.get("DIARIO_EXPORT_API_KEY", "")

# Testi dell'interfaccia: override locale dei predefiniti (vedi diario/testi.py).
TESTI_PATH = _percorso("DIARIO_TESTI", "testi.json")

# Password della plancia (/plancia, modifica dei testi dal browser, vedi
# diario/plancia.py). Vuota = plancia spenta (risponde 404).
PLANCIA_PASSWORD = os.environ.get("DIARIO_PLANCIA_PASSWORD", "")

# --- Testi ---
TESTO_MIN = _int("DIARIO_TESTO_MIN", 3)
TESTO_MAX = _int("DIARIO_TESTO_MAX", 5000)

# --- Limiti di invio (vedi diario/limiti.py) ---
# Secondi minimi tra la consegna del gettone (apertura della pagina) e il
# primo invio: sotto questa soglia è quasi certamente un bot.
ATTESA_MINIMA_S = _int("DIARIO_ATTESA_MINIMA_S", 3)
# Secondi minimi tra due invii dallo stesso browser.
PAUSA_BROWSER_S = _int("DIARIO_PAUSA_BROWSER_S", 30)
# Invii massimi all'ora dallo stesso browser.
MAX_ORA_BROWSER = _int("DIARIO_MAX_ORA_BROWSER", 12)
# Invii massimi all'ora dallo stesso IP: alto apposta, perché una classe
# intera può uscire dalla stessa Wi-Fi.
MAX_ORA_IP = _int("DIARIO_MAX_ORA_IP", 200)
# Invii massimi all'ora su tutto il sito (freno d'emergenza).
MAX_ORA_GLOBALE = _int("DIARIO_MAX_ORA_GLOBALE", 600)
# Finestra (ore) in cui lo stesso testo non può essere reinviato.
ORE_DUPLICATI = _int("DIARIO_ORE_DUPLICATI", 24)


def _segreto() -> bytes:
    """Segreto per firmare i gettoni dei browser. Se non è in `.env` se ne
    genera uno e lo si salva accanto al DB, così resta stabile tra i riavvii."""
    valore = os.environ.get("DIARIO_SEGRETO", "")
    if valore:
        return valore.encode()
    file = DB_PATH.parent / ".segreto"
    if file.is_file():
        return file.read_text().strip().encode()
    file.parent.mkdir(parents=True, exist_ok=True)
    nuovo = secrets.token_hex(32)
    file.write_text(nuovo)
    file.chmod(0o600)
    return nuovo.encode()


SEGRETO = _segreto()
