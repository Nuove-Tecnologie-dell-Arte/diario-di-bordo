---
name: Diario di bordo
description: Il diario anonimo dell'Accademia come campionario colori, nella palette Tokyo Night.
colors:
  # Chiaro = Tokyo Night Light (valori di :root)
  fondo: "#e6e7ed"
  barra: "#d6d8df"
  scheda: "#f4f5f8"
  campo: "#f4f5f8"
  testo: "#343b58"
  testo-2: "#51577a"
  segnaposto: "#51577a"
  bordo-campo: "#707280"
  linea: "#c1c2c7"
  accento: "#2959aa"
  su-accento: "#ffffff"
  errore: "#8c4351"
  su-tinta: "#f4f5f8"
  fascia: "rgb(244 245 248 / .22)"
  t-anno-1: "#385f0d"
  t-anno-2: "#33635c"
  t-anno-3: "#006c86"
  t-anno-4: "#2959aa"
  t-anno-5: "#65359d"
  t-fuori-corso: "#965027"
  t-ex-allievi: "#8f5e15"
  t-docenti: "#343b58"
  # Scuro = Tokyo Night (valori sotto prefers-color-scheme: dark)
  fondo-scuro: "#1a1b26"
  barra-scuro: "#16161e"
  scheda-scuro: "#1f2335"
  campo-scuro: "#16161e"
  testo-scuro: "#c0caf5"
  testo-2-scuro: "#9aa5ce"
  segnaposto-scuro: "#8f98c4"
  bordo-campo-scuro: "#737aa2"
  linea-scuro: "#292e42"
  accento-scuro: "#7aa2f7"
  su-accento-scuro: "#16161e"
  errore-scuro: "#f7768e"
  su-tinta-scuro: "#16161e"
  fascia-scuro: "rgb(22 22 30 / .3)"
  t-anno-1-scuro: "#9ece6a"
  t-anno-2-scuro: "#73daca"
  t-anno-3-scuro: "#7dcfff"
  t-anno-4-scuro: "#7aa2f7"
  t-anno-5-scuro: "#bb9af7"
  t-fuori-corso-scuro: "#ff9e64"
  t-ex-allievi-scuro: "#e0af68"
  t-docenti-scuro: "#c0caf5"
typography:
  display:
    fontFamily: "Atkinson Next, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(2.1rem, 6.5vw, 3.4rem)"
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "clamp(1.6rem, 5vw, 2.2rem)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.55
  body:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.55
  body-pensiero:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Atkinson Next, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 600
    lineHeight: 1.2
  catalogo:
    fontFamily: "Atkinson Mono, ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "0.875rem"
    fontWeight: 500
    letterSpacing: "0.02em"
    fontFeature: "tnum"
  timbro:
    fontFamily: "Atkinson Mono, ui-monospace, monospace"
    fontSize: "0.8125rem"
    fontWeight: 500
    letterSpacing: "0.12em"
rounded:
  raggio: "3px"
  raggio-campo: "6px"
spacing:
  xs: "8px"
  sm: "12px"
  gutter: "16px"
  scheda: "20px"
  lg: "24px"
  colonne: "48px"
components:
  bottone:
    backgroundColor: "{colors.accento}"
    textColor: "{colors.su-accento}"
    typography: "{typography.body}"
    rounded: "{rounded.raggio-campo}"
    padding: "0 28px"
    height: "52px"
  bottone-secondario:
    backgroundColor: "transparent"
    textColor: "{colors.testo}"
    rounded: "{rounded.raggio-campo}"
    padding: "0 28px"
    height: "52px"
  bottone-secondario-hover:
    backgroundColor: "{colors.scheda}"
  campo:
    backgroundColor: "{colors.campo}"
    textColor: "{colors.testo}"
    typography: "{typography.body-pensiero}"
    rounded: "{rounded.raggio-campo}"
    padding: "14px 16px"
  tessera:
    backgroundColor: "{colors.t-anno-1}"
    textColor: "{colors.su-tinta}"
    rounded: "{rounded.raggio}"
    height: "48px"
  campione:
    backgroundColor: "{colors.scheda}"
    textColor: "{colors.testo}"
    rounded: "{rounded.raggio-campo}"
    padding: "16px 20px"
  campione-testa:
    backgroundColor: "{colors.t-anno-3}"
    textColor: "{colors.su-tinta}"
    padding: "8px 20px 14px"
    height: "46px"
  filtro:
    backgroundColor: "{colors.scheda}"
    textColor: "{colors.testo}"
    typography: "{typography.label}"
    rounded: "{rounded.raggio-campo}"
    padding: "0 14px 0 10px"
    height: "44px"
  filtro-attivo:
    backgroundColor: "{colors.testo}"
    textColor: "{colors.fondo}"
  nav-voce:
    textColor: "{colors.testo-2}"
    typography: "{typography.label}"
    rounded: "{rounded.raggio-campo}"
    padding: "0 12px"
    height: "44px"
  nav-voce-attiva:
    textColor: "{colors.testo}"
---

# Design System: Diario di bordo

## Overview

**Creative North Star: "Il campionario del colorificio"**

Il diario è un campionario colori: ogni gruppo dell'Accademia è una tinta, ogni pensiero è un campione numerato a catalogo. Chi arriva sceglie la propria tinta da una griglia di tessere-campione, scrive, e vede il proprio campione entrare nel diario con il suo numero e un timbro "Pubblicato". In archivio si legge per tinte: la barra del campionario dice chi sta scrivendo e quanto.

La palette è **Tokyo Night** (https://github.com/tokyo-night/tokyo-night-vscode-theme), scelta e fissata dall'utente: in chiaro Tokyo Night Light, in scuro Tokyo Night, commutati da `prefers-color-scheme`. È un impegno di marca vincolante, non una proposta: nuove superfici non introducono tinte fuori da questa palette. La densità è quella di uno strumento da pollice: un'unica colonna a 390px, target da 44px in su, testo grande e leggibile (Atkinson Hyperlegible) per lettori con DSA. Il mondo rifiuta il diario-quaderno crema con serif e il feed di card generiche.

**Key Characteristics:**
- Otto tinte = otto gruppi, sempre nello stesso ordine (1°–5° anno, Fuori corso, Ex allievi, Docenti).
- La tessera-campione rettangolare con fascia orizzontale è il segno ricorrente: marchio, scelta del gruppo, testata del campione, filtri, barra proporzionale.
- Numero di catalogo "N. 0042" in mono tabellare su ogni pensiero.
- Superfici piatte su fondo tonale, una sola ombra morbida per i campioni.
- Due temi a pari dignità; nessuno dei due è derivato dall'altro.

## Colors

Una palette da editor notturno, fredda e indaco, su cui otto tinte sature fanno da identità dei gruppi; la stessa struttura vale in chiaro e in scuro, con i valori di Tokyo Night Light e Tokyo Night.

### Primary
- **Blu Tokyo** (`accento` / `accento-scuro`): l'unico colore d'azione. Bottone Invia, link, sottolineatura della voce di navigazione attiva, anello di focus, cursore, selezione. Coincide con la tinta del 4° anno: la distinzione è di forma (il bottone è largo e piatto, la tessera ha la fascia).

### Secondary
- **Le otto tinte del campionario** (`t-anno-1` verde, `t-anno-2` teal, `t-anno-3` ciano, `t-anno-4` blu, `t-anno-5` magenta, `t-fuori-corso` arancio, `t-ex-allievi` giallo, `t-docenti` inchiostro; varianti `-scuro`): ogni gruppo ha la sua, applicata via `data-gruppo` che imposta `--tinta`. In chiaro sono le tinte scure di Tokyo Night Light; in scuro le tinte luminose di Tokyo Night. Docenti usa la tinta dell'inchiostro (`testo`).
- **Su tinta** (`su-tinta`): il testo sopra una tinta (nome del gruppo e numero nella testata). Chiaro su tinta scura in chiaro, scuro su tinta luminosa in scuro; ogni coppia supera 5:1.
- **Fascia del campionario** (`fascia`): la banda traslucida che attraversa tessere e testate. Più chiara della tinta in chiaro, più scura in scuro.

### Neutral
- **Fondo** (`fondo`): il fondo della pagina.
- **Barra** (`barra`): la barra in alto, un gradino più profondo del fondo; usato anche come `theme-color`.
- **Scheda** (`scheda`): la carta dei campioni e dei filtri, un gradino più chiaro del fondo.
- **Campo** (`campo`): il fondo di area di testo e ricerca (in scuro coincide con la barra: il campo è un pozzo).
- **Inchiostro** (`testo`) e **Inchiostro tenue** (`testo-2`): testo principale e secondario (didascalie, aiuti, giorno, contatori). `testo-2` supera 5.6:1 su fondo e scheda in entrambi i temi.
- **Segnaposto** (`segnaposto`): placeholder, sempre ≥4.5:1.
- **Bordo dei campi** (`bordo-campo`): contorno di input, filtri, bottone secondario; ≥3:1 (circa 4.3:1) come richiesto per i controlli.
- **Linea** (`linea`): divisori e bordo dei campioni, puramente decorativo.
- **Errore** (`errore`): bordo e messaggio dei campi non validi, contatore oltre il limite.

### Named Rules
**La Regola del Pin.** La palette è Tokyo Night e basta. Nuovi colori si prendono dal tema ufficiale (chiaro o scuro), mai inventati; ogni token esiste in entrambi i temi.

**La Regola Una Tinta, Un Gruppo.** Una tinta del campionario indica solo il suo gruppo. Non la si usa come decorazione, come colore di stato o come secondo accento.

**La Regola della Fascia.** La fascia va verso il contrasto con la tinta: chiara in chiaro, scura in scuro. Una fascia nera sulle tinte già scure di Tokyo Night Light sparirebbe.

## Typography

**Display Font:** Atkinson Hyperlegible Next (`--font`, "Atkinson Next", con fallback system-ui)
**Body Font:** Atkinson Hyperlegible Next
**Label/Mono Font:** Atkinson Hyperlegible Mono (`--mono`, "Atkinson Mono", peso 500), solo per numeri di catalogo e timbro

**Character:** Un'unica famiglia ad alta leggibilità, nata per lettori ipovedenti, porta tutto il diario; la gerarchia nasce da peso e dimensione, non da un contrasto di famiglie. Il mono tabellare è la voce del catalogo. Entrambi i font sono serviti in locale da `public/fonts/`.

### Hierarchy
- **Display** (700, `clamp(2.1rem, 6.5vw, 3.4rem)`, 1.05, -0.025em): il titolo di pagina, uno per pagina, con `text-wrap: balance`.
- **Headline** (700, `clamp(1.6rem, 5vw, 2.2rem)`, 1.1, -0.02em): il titolo dello stato "Il tuo pensiero è nel diario".
- **Title** (700, 1rem): etichette dei campi e legende ("Il tuo pensiero", "Il tuo gruppo").
- **Body** (400, 1.0625rem, 1.55): testo corrente, descrizioni (max 56ch), spiegazioni (max 62ch).
- **Body pensiero** (400, 1.125rem, 1.6): il testo dei pensieri, sia nell'area di scrittura sia nei campioni; max 65ch, `white-space: pre-wrap` per rispettare gli a capo.
- **Label** (600, 0.9375rem): nomi dei gruppi sotto le tessere, filtri, voci di navigazione, aiuti. Dettagli minori a 0.875rem (giorno, contatore, didascalia della barra).
- **Catalogo** (Mono 500, 0.875rem, 0.02em, cifre tabellari): "N. 0042", sempre a quattro cifre, allineato a destra nella testata.
- **Timbro** (Mono 500, 0.8125rem, 0.12em, maiuscolo): solo il timbro "Pubblicato".

### Named Rules
**La Regola del Numero.** Ogni pensiero mostrato porta il suo numero di catalogo in mono tabellare; nessun altro testo usa il mono, tranne il timbro.

**La Regola DSA.** Niente testo giustificato, niente corpo sotto 0.875rem, righe dei pensieri entro 65ch. Tutte le cifre che cambiano (contatori, totali, posizioni) sono tabellari.

## Layout

Mobile-first a 390px: una colonna con gutter laterale di 16px (`gutter`), contenitore massimo 1040px centrato; la colonna di scrittura è limitata a 680px, quella dell'archivio a 760px. Il ritmo verticale è morbido più che modulare: 8 e 12px dentro i gruppi di controlli, 18px tra i blocchi del form, 20px di padding orizzontale nei campioni, 24px tra le sezioni a schermo stretto.

- **Home 390:** barra, titolo e descrizione, area di testo grande (6.5em, cresce col contenuto con `field-sizing: content`, max 70vh), campionario dei gruppi a griglia 4×2, Invia a tutta larghezza con la riga "Anonimo · pubblicato subito · non si può modificare". Campionario e Invia stanno nel primo schermo.
- **≥760px:** intestazione più ariosa (64px sopra), tessere alte 64px, Invia e promessa affiancati, filtri dell'archivio che vanno a capo invece di scorrere.
- **≥1000px:** il form diventa due colonne (testo 1.35fr, gruppo 1fr, distanza 48px); il campionario passa a 2 colonne con tessere da 56px.
- **≤420px e ≤380px:** la striscia del marchio si assottiglia e il campionario stringe i gap, senza mai cambiare l'ordine delle tinte.
- **Archivio:** titolo, barra proporzionale del campionario (larghezze = pensieri per gruppo), filtri a tessera scorrevoli orizzontalmente con scroll-snap (che sbordano fino al bordo dello schermo), ricerca etichettata, elenco dei campioni con 14px di distanza, paginazione "Più recenti / Più vecchi".

### Named Rules
**La Regola del Pollice.** Ogni bersaglio interattivo è alto almeno 44px; il bottone principale 52px.

## Elevation & Depth

Il sistema è piatto e tonale: la profondità viene dal gradino barra → fondo → scheda, non dalle ombre. Un'unica ombra morbida (`--ombra`) solleva i campioni e la tessera selezionata; la sua formula cambia per tema (più densa in scuro).

### Shadow Vocabulary
- **Ombra del campione** (chiaro: `0 1px 2px rgb(52 59 88 / .08), 0 8px 24px -12px rgb(52 59 88 / .18)`; scuro: `0 1px 2px rgb(0 0 0 / .3), 0 10px 28px -14px rgb(0 0 0 / .6)`): campioni in archivio e nell'esito, tessera selezionata.
- **Anello di selezione** (`0 0 0 2px fondo, 0 0 0 4px testo`): la tessera del gruppo scelto, staccata dal fondo e cerchiata d'inchiostro.

### Named Rules
**La Regola Piatto a Riposo.** Le tessere stanno piatte; si alzano di 2px al passaggio e di 3px quando sono scelte. Nient'altro si muove in profondità.

## Shapes

Rettangoli quasi netti. Le tessere-campione e le piccole tessere usano un angolo appena smussato (3px, `raggio`), come le strisce-campione stampate; campi, bottoni, filtri e campioni usano 6px (`raggio-campo`). Le tessere sono rettangoli più larghi che alti, non quadrati, per tenere campionario e Invia nel primo schermo. La forma ricorrente è la tessera con fascia orizzontale al 62–80% dell'altezza; nella testata del campione la fascia è una banda di 8px sul bordo inferiore. I campioni ritagliano il contenuto (`overflow: clip`) così la testata tinta segue l'angolo della scheda. Le icone sono SVG a tratto (2px, estremi arrotondati), mai glifi o icon font.

## Components

### Buttons
Pieni, larghi, senza ornamento.
- **Shape:** angolo morbido (6px, `raggio-campo`), altezza 52px, padding orizzontale 28px.
- **Primary:** fondo `accento`, testo `su-accento`, Body 700. Su mobile a tutta larghezza.
- **Hover / Focus / Active:** al passaggio `brightness(1.08)`; premuto scende di 1px; in attesa `aria-disabled` con cursore progress e saturazione ridotta; focus con l'anello globale (2px `accento`, offset 3px).
- **Secondario:** trasparente, testo `testo`, bordo `bordo-campo`; al passaggio si riempie di `scheda`. In paginazione scende a 44px di altezza e 16px di padding.

### Chips (filtri dell'archivio)
- **Style:** fondo `scheda`, bordo `bordo-campo`, 44px di altezza, piccola tessera da 14px della tinta del gruppo + nome + conteggio in `testo-2` tabellare. Il filtro "Tutti" ha una tessera a spicchi con le otto tinte (conic-gradient).
- **State:** al passaggio il bordo diventa `testo`; attivo (`aria-pressed="true"`) si inverte: fondo `testo`, testo `fondo`, tessera cerchiata.

### Cards / Containers (il campione)
- **Corner Style:** 6px (`raggio-campo`), contenuto ritagliato.
- **Background:** `scheda`, bordo 1px `linea`.
- **Shadow Strategy:** l'Ombra del campione (vedi Elevation & Depth).
- **Testata:** tinta del gruppo con la fascia di 8px in basso; a sinistra il nome del gruppo (700), a destra il numero di catalogo. Testo `su-tinta`, 0.9375rem.
- **Internal Padding:** testata 8px 20px 14px, corpo 16px 20px; sotto il testo il giorno (mai l'ora) in `testo-2` 0.875rem.

### Inputs / Fields
- **Style:** fondo `campo`, bordo 1px `bordo-campo`, 6px, padding 14px 16px. L'area di testo usa Body pensiero, non si ridimensiona a mano e cresce col contenuto. La ricerca ha l'icona lente a 14px da sinistra e altezza 50px.
- **Focus:** bordo `accento` più un anello interno di 1px `accento`; al passaggio il bordo diventa `testo-2`.
- **Error:** bordo e anello `errore`, messaggio sotto il campo in `errore` 600 con icona di avviso, collegato via `aria-describedby`; contatore in `errore` 700 oltre il limite.

### Navigation
- **Style:** barra `barra` alta 60px con bordo inferiore `linea`. A sinistra il marchio: la striscia di otto tessere (7×20px, 2px di distanza; 5px sotto 420px) seguita da "Diario di bordo" in 700. A destra le voci "Scrivi" e "Archivio" in Label 600 `testo-2`, alte 44px.
- **States:** al passaggio testo `testo` su `fondo`; la voce attiva (`aria-current="page"`) ha testo `testo` e una sottolineatura interna di 2px `accento`.
- **Mobile:** stessa barra, gap ridotti; un link "Vai al contenuto" appare al focus.

### Campionario dei gruppi (signature)
Griglia 4×2 (2 colonne sopra 1000px) di radio nascosti con etichetta: tessera alta 48px (64 / 56px sui larghi) della tinta del gruppo con la fascia, nome sotto in Label `testo-2`. Scelta: la tessera sale di 3px, prende l'anello di selezione e mostra una spunta SVG; il nome passa a `testo` 700. Focus da tastiera: anello `accento` a 6px di distanza.

### Timbro "Pubblicato" (signature)
Nello stato di esito il campione appena inviato riceve un timbro in basso a destra: Mono maiuscolo, colore e bordo 2px della tinta del gruppo, angolo 3px, ruotato di -4°. Entra con l'animazione `timbra` (0.55s, `--uscita` = `cubic-bezier(.16, 1, .3, 1)`, da scala 1.6 e -12° a riposo) e si ripete a ogni invio.

### Barra del campionario (signature, archivio)
Una barra alta 14px, angolo 3px, divisa in segmenti tinti separati da 2px di `linea`, larghi in proporzione ai pensieri di ciascun gruppo; didascalia "Chi scrive nel diario" e totale tabellare. I segmenti crescono con una transizione di 0.6s.

## Do's and Don'ts

### Do:
- **Do** prendere ogni colore da Tokyo Night (scuro) o Tokyo Night Light (chiaro) e definirlo in entrambi i temi.
- **Do** dare a ogni elemento legato a un gruppo il suo `data-gruppo`, così eredita `--tinta`, e mostrare le otto tinte sempre nello stesso ordine.
- **Do** usare la tessera rettangolare con fascia (3px di angolo) come unico segno identitario dei gruppi.
- **Do** mostrare ogni pensiero come campione: testata tinta, numero "N. 0000" in mono tabellare, testo su `scheda`, giorno senza ora.
- **Do** tenere bersagli da 44px, corpo ≥0.875rem, righe dei pensieri ≤65ch, testo allineato a sinistra.
- **Do** rispettare `prefers-reduced-motion`: le animazioni (timbro, sollevamento delle tessere, barra) si azzerano.

### Don't:
- **Don't** introdurre tinte fuori dalla palette Tokyo Night pinnata, né un secondo accento accanto a `accento`.
- **Don't** usare una tinta di gruppo per decorare o per segnalare uno stato (successo, errore, avviso).
- **Don't** tornare al diario-quaderno: fondo crema, serif, card generiche tutte uguali.
- **Don't** usare il mono per testo corrente o titoli: è riservato a numero di catalogo e timbro.
- **Don't** mostrare l'ora di un pensiero o qualunque segno che suggerisca un'identità oltre al gruppo.
- **Don't** rendere quadrate le tessere del campionario o togliere loro la fascia.
