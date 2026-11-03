"""Database del diario: un file SQLite (`data/diario.db`).

SQLite invece di un file JSON perché regge scritture contemporanee senza
corrompersi, e resta un singolo file che altri progetti possono leggere
direttamente (in sola lettura) o tramite `/api/export`.

Schema (tabella `pensieri`):
    id          INTEGER, crescente, mai riusato
    testo       TEXT, il pensiero così come inviato (normalizzato negli a capo)
    categoria   TEXT, una delle chiavi di CATEGORIE
    created_at  TEXT, 'AAAA-MM-GG HH:MM:SS' ora locale del server
    status      TEXT, 'pubblicato' (predisposto per un'eventuale moderazione)

Non si salvano IP né altri dati che identifichino chi scrive.
"""

import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

from diario import config

# Ordine = ordine di visualizzazione nel form e nell'archivio.
CATEGORIE: list[tuple[str, str]] = [
    ("anno-1", "1° anno"),
    ("anno-2", "2° anno"),
    ("anno-3", "3° anno"),
    ("anno-4", "4° anno"),
    ("anno-5", "5° anno"),
    ("fuori-corso", "Fuori corso"),
    ("ex-allievi", "Ex allievi"),
    ("docenti", "Docenti"),
]
CHIAVI_CATEGORIE = {k for k, _ in CATEGORIE}

FORMATO_DATA = "%Y-%m-%d %H:%M:%S"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pensieri (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    testo       TEXT    NOT NULL,
    categoria   TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'pubblicato'
);
CREATE INDEX IF NOT EXISTS idx_pensieri_categoria ON pensieri(categoria, id);
CREATE INDEX IF NOT EXISTS idx_pensieri_created   ON pensieri(created_at);
"""


@contextmanager
def connessione():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connessione() as conn:
        conn.executescript(_SCHEMA)


def normalizza_testo(testo: str) -> str:
    """A capo uniformi, spazi in coda tolti, al massimo una riga vuota di fila."""
    testo = testo.replace("\r\n", "\n").replace("\r", "\n")
    testo = "\n".join(r.rstrip() for r in testo.split("\n"))
    testo = re.sub(r"\n{3,}", "\n\n", testo)
    return testo.strip()


def _riga(r: sqlite3.Row) -> dict:
    """Pensiero per le pagine pubbliche: solo il giorno ('AAAA-MM-GG'), mai
    l'ora, perché in una comunità piccola l'ora esatta basta a capire chi ha
    scritto. L'ora completa resta nel DB e in `esporta()`."""
    return {
        "id": r["id"],
        "testo": r["testo"],
        "categoria": r["categoria"],
        "giorno": r["created_at"][:10],
    }


def e_duplicato(testo: str) -> bool:
    """True se lo stesso testo (senza distinguere maiuscole) è già stato
    inviato nelle ultime ORE_DUPLICATI ore."""
    soglia = (datetime.now() - timedelta(hours=config.ORE_DUPLICATI)).strftime(FORMATO_DATA)
    with connessione() as conn:
        r = conn.execute(
            "SELECT 1 FROM pensieri WHERE lower(testo) = lower(?) AND created_at >= ? LIMIT 1",
            (testo, soglia),
        ).fetchone()
    return r is not None


def inserisci(testo: str, categoria: str) -> dict:
    if categoria not in CHIAVI_CATEGORIE:
        raise ValueError(f"categoria non valida: {categoria!r}")
    adesso = datetime.now().strftime(FORMATO_DATA)
    with connessione() as conn:
        cur = conn.execute(
            "INSERT INTO pensieri (testo, categoria, created_at) VALUES (?, ?, ?)",
            (testo, categoria, adesso),
        )
        r = conn.execute("SELECT * FROM pensieri WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _riga(r)


def _escape_like(s: str) -> str:
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _filtro(categoria: str | None, cerca: str | None) -> tuple[str, list]:
    dove = ["status = 'pubblicato'"]
    parametri: list = []
    if categoria:
        dove.append("categoria = ?")
        parametri.append(categoria)
    if cerca:
        dove.append("testo LIKE ? ESCAPE '\\'")
        parametri.append(f"%{_escape_like(cerca)}%")
    return " AND ".join(dove), parametri


def elenca(categoria: str | None, cerca: str | None, pagina: int, per_pagina: int) -> dict:
    """Pagina di pensieri pubblicati, dal più recente."""
    clausola, parametri = _filtro(categoria, cerca)
    with connessione() as conn:
        totale = conn.execute(f"SELECT COUNT(*) FROM pensieri WHERE {clausola}", parametri).fetchone()[0]
        pagine = max(1, -(-totale // per_pagina))
        pagina = min(max(1, pagina), pagine)
        righe = conn.execute(
            f"SELECT * FROM pensieri WHERE {clausola} ORDER BY id DESC LIMIT ? OFFSET ?",
            [*parametri, per_pagina, (pagina - 1) * per_pagina],
        ).fetchall()
    return {
        "totale": totale,
        "pagina": pagina,
        "pagine": pagine,
        "pensieri": [_riga(r) for r in righe],
    }


def conteggi(cerca: str | None = None) -> dict[str, int]:
    """Pensieri per categoria; con `cerca`, solo quelli che contengono il testo."""
    clausola, parametri = _filtro(None, cerca)
    with connessione() as conn:
        righe = conn.execute(
            f"SELECT categoria, COUNT(*) AS n FROM pensieri WHERE {clausola} GROUP BY categoria",
            parametri,
        ).fetchall()
    trovati = {r["categoria"]: r["n"] for r in righe}
    return {k: trovati.get(k, 0) for k, _ in CATEGORIE}


def esporta(dal_id: int = 0) -> list[dict]:
    """Tutti i pensieri con id > dal_id, nel formato letto da Oracolo
    (stessi campi di hosting/api/export.php: id, text, created_at, status,
    ip, likes) più `categoria`. `ip` è sempre null: non lo salviamo."""
    with connessione() as conn:
        righe = conn.execute(
            "SELECT * FROM pensieri WHERE id > ? ORDER BY id", (dal_id,)
        ).fetchall()
    return [
        {
            "id": r["id"],
            "text": r["testo"],
            "created_at": r["created_at"],
            "status": r["status"],
            "ip": None,
            "likes": 0,
            "categoria": r["categoria"],
        }
        for r in righe
    ]
