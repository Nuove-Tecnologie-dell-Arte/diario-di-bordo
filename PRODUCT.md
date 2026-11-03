# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Allievi e docenti dell'Accademia di Belle Arti di Napoli. Scrivono quasi
sempre **dal telefono**, in momenti sparsi (in aula, in corridoio, a casa),
arrivando da un link. Chi scrive sceglie solo il proprio gruppo: Docenti,
1°–5° anno, Fuori corso, Ex allievi. Chi legge l'archivio è la stessa
comunità, curiosa di cosa pensano gli altri gruppi.

## Product Purpose

Raccogliere pensieri brevi o lunghi sul percorso in Accademia e renderli
consultabili da tutti. Successo: scrivere è così semplice che lo si fa in
pochi secondi dal telefono, e l'archivio invita a leggere e a tornare.

## Positioning

Un diario collettivo e anonimo di una comunità precisa: l'unica
informazione su chi scrive è il gruppo di appartenenza, e la lettura per
gruppo (cosa pensa il 1° anno rispetto agli ex allievi, ai docenti…) è il
cuore della consultazione.

## Operating Context

- Ospitato sul PC del laboratorio (computersopra), raggiungibile da Internet.
- Il database è letto anche da **Oracolo**, un altro progetto. Nell'interfaccia
  del diario Oracolo non si nomina: il diario è un progetto a sé.

## Capabilities and Constraints

- Home: titolo, descrizione, form (scelta del gruppo + testo + Invia).
- Archivio: sfogliabile, filtrabile per gruppo, ricerca nel testo, paginato.
- Pubblicazione immediata, senza approvazione, senza account né password.
- **Anonimato sempre**: nessun nome, nessun dato identificativo salvato.
- Categoria "Docenti" selezionabile da chiunque, senza codice.
- Limiti anti-spam senza identificare nessuno (cookie del browser, tetti
  larghi per rete e globali, duplicati): molti scrivono dalla stessa Wi-Fi.
- Stack esistente: HTML/CSS/JS statici senza build, server Python stdlib.
  Testi dell'interfaccia in italiano.

## Brand Commitments

- Il nome **"Diario di bordo"** è definitivo.

## Evidence on Hand

- Nessun contenuto reale ancora: il diario parte vuoto. Non inventare
  pensieri di esempio presentandoli come veri.
- Nessun logo o marchio fornito.

## Product Principles

1. Scrivere prima di tutto: il form si usa con il pollice, in pochi secondi.
2. L'anonimato è una promessa: l'interfaccia non chiede e non suggerisce mai
   dati personali.
3. Il gruppo è l'unica identità, e organizza la lettura dell'archivio.
4. Ogni pensiero ha dignità, breve o lungo: la lettura deve essere piacevole
   anche per testi lunghi.

## Accessibility & Inclusion

Accessibilità esplicitamente richiesta: puntare a WCAG 2.2 AA (contrasto,
uso da tastiera e screen reader, target touch adeguati, testo
ridimensionabile). Considerare lettori con DSA: testi leggibili, righe non
troppo lunghe, nessun testo giustificato, messaggi chiari.
