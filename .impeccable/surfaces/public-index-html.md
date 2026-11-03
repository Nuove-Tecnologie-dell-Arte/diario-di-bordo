---
version: 1
slug: "public-index-html"
primary_target: "public/index.html"
related_targets: ["public/archivio.html"]
---

# Surface brief: Diario di bordo (home + archivio)

Scope: home (scrivere un pensiero) in modalità Operate; archivio (leggere per gruppo) in modalità Read. Mobile-first, 390px.
Audience/job: allievi e docenti dell'Accademia, dal telefono, in pochi secondi; poi leggere cosa scrivono gli altri gruppi.
Constraints: anonimato (nessun dato personale, in UI solo il giorno, mai l'ora); WCAG 2.2 AA + DSA; nome "Diario di bordo"; palette Tokyo Night pinnata dall'utente (dark = Tokyo Night, light = Tokyo Night Light).
Memorable moment: il pensiero inviato diventa una scheda del campionario, con il suo numero.

## Direction contract

THESIS: Il diario come campionario colori del colorificio: ogni gruppo è una tinta, ogni pensiero un campione numerato. Rifiuta il diario-quaderno crema con serif e il feed di card generiche.

OWN-WORLD: Palette Tokyo Night (pinnata): fondo #1a1b26 / barra #16161e / schede #1f2335; in chiaro #e6e7ed / #d6d8df / #f4f5f8. Otto tinte = otto gruppi (verde, teal, ciano, blu, magenta, arancio, giallo; Docenti = tinta dell'inchiostro). Tessere-campione rettangolari come le strisce-campione del colorificio (rettangoli, non quadrati, per tenere campionario e Invia nel primo schermo a 390) con angoli 3px; la fascia del campionario attraversa tessere e testate: più scura della tinta in scuro, più chiara in chiaro, perché le tinte di Tokyo Night Light sono già scure e una fascia nera sparirebbe; numeri di catalogo "N. 0042" in mono tabellare, Atkinson Hyperlegible Next per tutto il resto.

STORY: Chi arriva vede subito dove scrivere; sceglie la sua tinta dal campionario, invia, e vede il suo campione entrare nel diario. In archivio legge per tinte: il campionario dice chi sta scrivendo e quanto.

FIRST VIEWPORT: Home 390: barra con la striscia di 8 tessere come marchio + Scrivi/Archivio; titolo e descrizione; area di testo grande; sotto, il campionario dei gruppi a griglia 4x2 di tessere grandi; Invia a tutta larghezza con la riga "Anonimo · pubblicato subito · non modificabile". Archivio: titolo, barra proporzionale del campionario (larghezze = pensieri per gruppo), filtri a tessera scorrevoli, ricerca etichettata, poi i campioni.

FORM: Campionario colori del colorificio, candidato 5 della lista ordinata (assegnato dal tiro), tradotto nella palette Tokyo Night pinnata. Raise: catalogo numerato per ogni voce (da Saville/Factory), stato "pubblicato" che si timbra sul campione invece di sparire (dal ticket wallet), griglia del campionario come armatura visibile (da Crouwel). seed:0569b74bde425665

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
