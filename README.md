# Diario di bordo

Diario condiviso per allievi e docenti: si lascia un pensiero anonimo
indicando solo il proprio gruppo (Docenti, 1°–5° anno, Fuori corso, Ex
allievi). I pensieri sono pubblicati subito e si consultano nell'archivio,
filtrando per gruppo, per giorno o cercando una parola. Pensato per girare su
computersopra (WSL del lab) e per essere letto anche da Oracolo.

## Avvio

Serve solo Python 3.10+, senza pacchetti da installare.

```bash
cp .env.example .env        # poi impostare almeno DIARIO_EXPORT_API_KEY
python3 -m diario           # serve il sito su http://127.0.0.1:8007/
python3 -m diario esporta   # stampa tutto il DB in JSON (backup)
```

Come servizio: vedi le istruzioni in testa a `scripts/diario-di-bordo.service`.

## Struttura

```
diario/config.py   configurazione da .env
diario/db.py       database SQLite (data/diario.db) e categorie
diario/limiti.py   limiti di invio anti-spam
diario/server.py   webserver (http.server della stdlib) e API
public/            home (index.html + app.js), archivio (archivio.html + archivio.js),
                   comune.js, style.css, fonts/ (Atkinson Hyperlegible, serviti in locale)
```

Aspetto: palette Tokyo Night (scuro) / Tokyo Night Light (chiaro), secondo
le preferenze del dispositivo. Ogni gruppo ha la sua tinta, come in un
campionario colori; le tinte sono in testa a `public/style.css`. I font sono
serviti dal sito stesso, perché passare da Google Fonts farebbe arrivare a
Google l'IP di chi visita.

Il titolo e la descrizione della home si cambiano in `public/index.html`,
nel blocco segnato da un commento.

## API

| Metodo | Percorso | Cosa fa |
|---|---|---|
| GET | `/api/categorie` | categorie con il numero di pensieri |
| GET | `/api/categorie?cerca=&dal=&al=` | come sopra, contando solo i pensieri che contengono il testo e/o scritti tra `dal` e `al` |
| GET | `/api/pensieri?categoria=&cerca=&dal=&al=&pagina=&per_pagina=` | archivio paginato, dal più recente; per ogni pensiero solo il `giorno`, mai l'ora |
| POST | `/api/pensieri` | `{"testo", "categoria"}` → nuovo pensiero |
| GET | `/api/export?dal_id=N` | tutti i pensieri con id > N, header `X-Api-Key` |
| GET | `/api/health` | stato del servizio |

`dal` e `al` sono giorni `AAAA-MM-GG`, estremi inclusi, tutti e due
facoltativi (`dal=2026-11-06&al=2026-11-06` = solo quel giorno). Il giorno è
quello del server (`created_at` è in ora locale del server), lo stesso che
l'archivio mostra sotto ogni pensiero. Un valore non valido, o `dal` dopo
`al`, dà `400` con `{"errore": "..."}`. Le scorciatoie dell'archivio (Oggi,
Ieri, Ultima settimana = ultimi 7 giorni, Ultimo mese = ultimi 30 giorni)
sono calcolate dal browser e tradotte in `dal`/`al`. Si filtra
solo per giorno, mai per ora.

## Condividere il database con altri progetti

- **Via HTTP** (consigliato): `/api/export` restituisce gli stessi campi
  dell'`export.php` di Oracolo (`id, text, created_at, status, ip, likes`)
  più `categoria`. `ip` è sempre `null` e `likes` sempre `0`. Con `dal_id`
  si scaricano solo i pensieri nuovi.
- **Direttamente**: `data/diario.db` è un normale file SQLite (tabella
  `pensieri`, schema in `diario/db.py`). Un altro processo sulla stessa
  macchina lo può leggere in sola lettura mentre il server gira (modalità WAL).

Le categorie sono chiavi fisse: `docenti`, `anno-1` … `anno-5`,
`fuori-corso`, `ex-allievi`.

## Anonimato e limiti di invio

Nel database non finiscono IP, nomi né altri dati di chi scrive. Il giorno e
l'ora dell'invio restano nel DB e in `/api/export`, ma le pagine e l'API
pubblica mostrano solo il giorno: in una comunità piccola l'ora esatta basta
a capire chi ha scritto. Contro lo
spam non si usa l'IP singolo (una classe intera esce dalla stessa Wi-Fi)
e nemmeno il MAC address, che al server non arriva. Si combinano invece:

- un cookie firmato per browser: senza cookie non si invia, il primo invio
  deve arrivare almeno 3 s dopo l'apertura della pagina, ne servono 30 tra un
  pensiero e l'altro e se ne possono inviare al massimo 12 all'ora;
- un tetto per IP molto largo (200 all'ora) contro i flood automatici;
- un tetto globale (600 all'ora);
- il rifiuto dello stesso testo già inviato nelle ultime 24 ore;
- un campo esca nascosto nel form contro i bot.

Tutti i valori si regolano in `.env`. I contatori stanno in memoria: un
riavvio li azzera.
