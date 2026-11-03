"""Avvio: `python -m diario` (serve il sito) oppure `python -m diario esporta`
(stampa tutto il DB in JSON, utile per backup o per altri progetti)."""

import json
import sys

from diario import db, server


def main() -> None:
    comando = sys.argv[1] if len(sys.argv) > 1 else "serve"
    if comando == "serve":
        server.avvia()
    elif comando == "esporta":
        db.init_db()
        json.dump(db.esporta(), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.exit(f"Comando sconosciuto: {comando}  (usa: serve | esporta)")


if __name__ == "__main__":
    main()
