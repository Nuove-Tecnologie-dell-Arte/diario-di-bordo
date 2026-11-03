// Home: scrivere un pensiero e inviarlo nel diario.

const form = document.getElementById("form");
const campionario = document.getElementById("categorie");
const gruppo = document.getElementById("gruppo");
const testo = document.getElementById("testo");
const contatore = document.getElementById("contatore");
const statoBozza = document.getElementById("stato-bozza");
const erroreTesto = document.getElementById("errore-testo");
const erroreGruppo = document.getElementById("errore-gruppo");
const invia = document.getElementById("invia");
const messaggio = document.getElementById("messaggio");
const esito = document.getElementById("esito");

const CHIAVE_GRUPPO = "diario_categoria";
const CHIAVE_BOZZA = "diario_bozza";
const TESTO_MIN = 3;
let testoMax = 5000;
let nomi = {};
let inviando = false;

// --- Campo di testo: crescita automatica, contatore, bozza ------------

const crescitaNativa = CSS.supports("field-sizing", "content");
function adattaAltezza() {
  if (crescitaNativa) return;
  testo.style.height = "auto";
  testo.style.height = Math.min(testo.scrollHeight + 2, window.innerHeight * 0.7) + "px";
}

function aggiornaContatore() {
  const n = testo.value.length;
  // Il contatore compare solo vicino al limite: prima sarebbe rumore.
  contatore.hidden = n < testoMax * 0.8;
  contatore.textContent = `${n} / ${testoMax}`;
  contatore.classList.toggle("troppo", n > testoMax);
}

let timerBozza;
function salvaBozza() {
  clearTimeout(timerBozza);
  timerBozza = setTimeout(() => {
    const v = testo.value;
    scriviMemoria(CHIAVE_BOZZA, v.trim() ? v : null);
    statoBozza.textContent = v.trim() ? "Bozza salvata su questo dispositivo" : "";
  }, 500);
}

function ripristinaBozza() {
  const bozza = leggiMemoria(CHIAVE_BOZZA);
  if (bozza) {
    testo.value = bozza;
    statoBozza.textContent = "Bozza ripresa da dove l'avevi lasciata";
  }
}

testo.addEventListener("input", () => {
  pulisciErrore(testo, erroreTesto);
  adattaAltezza();
  aggiornaContatore();
  salvaBozza();
});

// Ctrl/Cmd + Invio invia, per chi scrive da tastiera.
testo.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    form.requestSubmit();
  }
});

// --- Errori legati al campo --------------------------------------------

function mostraErrore(campo, box, testoErrore) {
  box.replaceChildren(icona("avviso"), document.createTextNode(testoErrore));
  box.hidden = false;
  campo.setAttribute("aria-invalid", "true");
}
function pulisciErrore(campo, box) {
  box.hidden = true;
  box.textContent = "";
  campo.removeAttribute("aria-invalid");
}

function pulisciErroreGruppo() {
  erroreGruppo.hidden = true;
  erroreGruppo.textContent = "";
  for (const r of campionario.querySelectorAll("input")) {
    r.removeAttribute("aria-invalid");
    r.removeAttribute("aria-describedby");
  }
}

// --- Campionario dei gruppi --------------------------------------------

async function caricaCategorie() {
  try {
    const r = await fetch("/api/categorie");
    const dati = await r.json();
    testoMax = dati.testo_max || testoMax;
    const ricordato = leggiMemoria(CHIAVE_GRUPPO);
    for (const c of dati.categorie) {
      nomi[c.chiave] = c.nome;
      const id = "g-" + c.chiave;
      const input = document.createElement("input");
      input.type = "radio";
      input.name = "categoria";
      input.id = id;
      input.value = c.chiave;
      if (c.chiave === ricordato) input.checked = true;
      input.addEventListener("change", pulisciErroreGruppo);

      const label = document.createElement("label");
      label.htmlFor = id;
      label.dataset.gruppo = c.chiave;
      const tessera = document.createElement("span");
      tessera.className = "tessera";
      tessera.append(icona("spunta"));
      const nome = document.createElement("span");
      nome.className = "nome";
      nome.textContent = c.nome;
      label.append(tessera, nome);
      campionario.append(input, label);
    }
  } catch {
    messaggio.textContent = "Non riesco a caricare i gruppi: ricarica la pagina.";
  }
  aggiornaContatore();
}

// --- Invio -------------------------------------------------------------

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (inviando) return;
  messaggio.textContent = "";

  const valore = testo.value.trim();
  const scelta = form.querySelector('input[name="categoria"]:checked');
  let primoErrore = null;

  if (valore.length < TESTO_MIN) {
    mostraErrore(testo, erroreTesto, "Scrivi almeno qualche parola.");
    primoErrore = testo;
  } else if (valore.length > testoMax) {
    mostraErrore(testo, erroreTesto, `Il pensiero supera i ${testoMax} caratteri: accorcialo un po'.`);
    primoErrore = testo;
  }
  if (!scelta) {
    erroreGruppo.replaceChildren(icona("avviso"), document.createTextNode("Scegli il tuo gruppo dal campionario."));
    erroreGruppo.hidden = false;
    for (const r of campionario.querySelectorAll("input")) {
      r.setAttribute("aria-invalid", "true");
      r.setAttribute("aria-describedby", "errore-gruppo");
    }
    primoErrore = primoErrore || campionario.querySelector("input");
  }
  if (primoErrore) {
    primoErrore.focus();
    return;
  }

  inviando = true;
  invia.setAttribute("aria-disabled", "true");
  invia.textContent = "Invio in corso…";
  try {
    const r = await fetch("/api/pensieri", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        testo: valore,
        categoria: scelta.value,
        sito: document.getElementById("sito").value,
      }),
    });
    const dati = await r.json().catch(() => ({}));
    if (r.ok) {
      scriviMemoria(CHIAVE_GRUPPO, scelta.value);
      scriviMemoria(CHIAVE_BOZZA, null);
      mostraEsito(dati.pensiero, valore, scelta.value);
    } else if (r.status === 409 || r.status === 400) {
      mostraErrore(testo, erroreTesto, dati.errore || "Controlla il testo e riprova.");
      testo.focus();
    } else {
      messaggio.textContent = dati.errore || "Qualcosa è andato storto: riprova tra poco. Il testo resta qui.";
    }
  } catch {
    messaggio.textContent = "Connessione assente: il testo resta qui, riprova appena torna la rete.";
  } finally {
    inviando = false;
    invia.removeAttribute("aria-disabled");
    invia.textContent = "Invia nel diario";
  }
});

function mostraEsito(pensiero, valore, chiave) {
  const campione = document.getElementById("esito-campione");
  campione.dataset.gruppo = chiave;
  document.getElementById("esito-gruppo").textContent = nomi[chiave] || chiave;
  document.getElementById("esito-numero").textContent = pensiero ? numeroCatalogo(pensiero.id) : "";
  document.getElementById("esito-testo").textContent = pensiero ? pensiero.testo : valore;
  document.getElementById("esito-giorno").textContent = pensiero ? formattaGiorno(pensiero.giorno) : "";
  const link = document.getElementById("esito-link");
  link.href = "/archivio?categoria=" + encodeURIComponent(chiave);
  const chi = { "fuori-corso": "scrivono i fuori corso", "ex-allievi": "scrivono gli ex allievi", docenti: "scrivono i docenti" };
  link.textContent = "Leggi cosa " + (chi[chiave] || `scrive il ${nomi[chiave] || "tuo gruppo"}`);

  // Il timbro si riattiva a ogni invio.
  const timbro = campione.querySelector(".timbro");
  timbro.style.animation = "none";
  void timbro.offsetWidth;
  timbro.style.animation = "";

  form.hidden = true;
  esito.hidden = false;
  window.scrollTo({ top: 0 });
  document.getElementById("esito-titolo").focus();
}

document.getElementById("esito-altro").addEventListener("click", () => {
  esito.hidden = true;
  form.hidden = false;
  testo.value = "";
  statoBozza.textContent = "";
  adattaAltezza();
  aggiornaContatore();
  testo.focus();
});

ripristinaBozza();
adattaAltezza();
caricaCategorie();
