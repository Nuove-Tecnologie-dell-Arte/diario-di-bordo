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
diario/testi.py    testi dell'interfaccia (predefiniti + testi.json locale)
diario/plancia.py  plancia: modifica dei testi dal browser, con password
public/            home (index.html + app.js), archivio (archivio.html + archivio.js),
                   comune.js, style.css, fonts/ (Atkinson Hyperlegible, serviti in locale)
```

Aspetto: palette Tokyo Night (scuro) / Tokyo Night Light (chiaro), secondo
le preferenze del dispositivo. Ogni gruppo ha la sua tinta, come in un
campionario colori; le tinte sono in testa a `public/style.css`. I font sono
serviti dal sito stesso, perché passare da Google Fonts farebbe arrivare a
Google l'IP di chi visita.

## Testi

Tutti i testi dell'interfaccia (titoli, etichette, bottoni, messaggi di
errore, title e description delle pagine, nomi dei gruppi) si cambiano senza
toccare il codice e senza riavviare il server.

- I predefiniti stanno in `diario/testi_predefiniti.json` (versionato: è
  anche l'elenco completo delle chiavi).
- Per cambiarne qualcuno si crea `testi.json` nella cartella del progetto
  (non versionato; altro percorso con `DIARIO_TESTI` in `.env`) con solo le
  chiavi da ridefinire:

  ```json
  {
    "home.titolo": "Scrivi qualcosa per chi verrà dopo",
    "comune.categoria.docenti": "Prof"
  }
  ```

- Il server rilegge il file quando lo si salva: basta ricaricare la pagina.
  Se il JSON non è valido, nel log compare un avviso e si usano i predefiniti.
- `{nome}` dentro un testo è un segnaposto riempito dal programma (es.
  `{max}`, `{cerca}`, `{n}`): va lasciato com'è.

Le chiavi hanno un prefisso: `comune.*` (parti comuni, gruppi, date),
`home.*`, `archivio.*`, `server.*` (messaggi restituiti dall'API).

Per aggiungere un testo nuovo: si aggiunge la chiave in
`diario/testi_predefiniti.json`, poi
- nell'HTML si mette `data-testo="chiave"` su un elemento che contiene solo
  testo, oppure `data-testo-<attributo>="chiave"` (es.
  `data-testo-placeholder`, `data-testo-aria-label`, `data-testo-content`);
  il server lo applica prima di inviare la pagina e `comune.js` di nuovo nel
  browser;
- nel JavaScript si usa `T("chiave", "testo di riserva", { parametri })`
  (definita da `/testi.js`, incluso in ogni pagina prima di `comune.js`);
- in Python si usa `testi.t("chiave", parametro=valore)` da `diario/testi.py`.

## Plancia

I testi si possono cambiare anche dal browser, su **`/plancia`** (es.
`http://127.0.0.1:8007/plancia`). La pagina non è linkata da nessuna parte,
è esclusa da `robots.txt` e ha `noindex`.

- Si accende mettendo una password in `.env`:

  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(18))"
  # poi in .env:  DIARIO_PLANCIA_PASSWORD=<la password generata>
  ```

  Senza password (variabile vuota o assente) `/plancia` risponde 404.
- Elenca tutte le chiavi di `diario/testi_predefiniti.json` divise per
  prefisso, con il predefinito, il valore attuale e se è modificato; c'è una
  ricerca e il filtro "Solo i testi modificati". Ogni chiave modificata si
  può riportare al predefinito.
- Salvando, in `testi.json` finiscono solo le chiavi diverse dal predefinito
  (quelle che il sito non conosce, aggiunte a mano, restano). Si toccano
  solo i campi cambiati nella pagina, quindi una modifica fatta a mano al
  file nel frattempo non va persa. Un testo che non ha esattamente gli stessi
  segnaposto `{nome}` del predefinito viene rifiutato.
- Se `testi.json` non è JSON valido la plancia lo dice e non lo sovrascrive:
  per farlo bisogna spuntare la conferma, e prima viene copiato in
  `testi.json.<data>.bak`.
- Sicurezza: sessione in un cookie firmato con `DIARIO_SEGRETO` (8 ore,
  HttpOnly, SameSite=Strict, Secure se si arriva in HTTPS dal proxy), token
  CSRF e controllo dell'Origin su ogni salvataggio, al massimo 5 password
  sbagliate ogni 15 minuti per IP e 30 in tutto (in memoria). Cambiare la
  password chiude tutte le sessioni aperte. La plancia non mostra pensieri
  né IP.

Sul lab, dopo `git pull`: aggiungere `DIARIO_PLANCIA_PASSWORD=...` in `.env`
nella cartella del progetto, poi

```bash
sudo systemctl restart diario-di-bordo
```

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
