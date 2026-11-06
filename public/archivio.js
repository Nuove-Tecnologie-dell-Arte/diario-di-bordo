// Archivio: i pensieri del diario, da leggere per gruppo.
// Lo stato (gruppo, ricerca, pagina) sta nell'URL, così un link si può condividere.

const PER_PAGINA = 20;
const filtri = document.getElementById("filtri");
const cerca = document.getElementById("cerca");
const riepilogo = document.getElementById("riepilogo");
const elenco = document.getElementById("elenco");
const paginazione = document.getElementById("paginazione");
const prec = document.getElementById("prec");
const succ = document.getElementById("succ");
const pos = document.getElementById("pos");
const spettroBox = document.getElementById("spettro-box");
const spettro = document.getElementById("spettro");

let categorie = [];
let nomi = {};
let richiesta = 0;
const stato = leggiUrl();

// --- Filtro per data ---------------------------------------------------
// Nell'URL: `periodo` (oggi, ieri, settimana, mese) oppure `giorno` (AAAA-MM-GG).
// Le scorciatoie si calcolano qui, nel fuso del browser, e diventano dal/al
// per l'API; un link condiviso con "oggi" mostra l'oggi di chi lo apre.

function testoArchivio(k, r, p) { return window.T ? window.T(k, r, p) : r; }

const periodi = document.getElementById("periodi");
const inputGiorno = document.getElementById("giorno");
const PERIODI = ["oggi", "ieri", "settimana", "mese"];
const RE_GIORNO = /^\d{4}-\d{2}-\d{2}$/;

function giornoValido(g) {
  if (!RE_GIORNO.test(g || "")) return false;
  const [a, m, d] = g.split("-").map(Number);
  const x = new Date(2000, m - 1, d);
  x.setFullYear(a);
  return x.getFullYear() === a && x.getMonth() === m - 1 && x.getDate() === d;
}

function leggiDataUrl() {
  const p = new URLSearchParams(location.search);
  const giorno = p.get("giorno") || "";
  const periodo = p.get("periodo") || "";
  if (giornoValido(giorno)) return { periodo: "", giorno };
  return { periodo: PERIODI.includes(periodo) ? periodo : "", giorno: "" };
}
Object.assign(stato, leggiDataUrl());

function scriviDataUrl(p) {
  if (stato.giorno) p.set("giorno", stato.giorno);
  else if (stato.periodo) p.set("periodo", stato.periodo);
}

// Date -> 'AAAA-MM-GG' con le componenti locali (non UTC).
function isoLocale(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function giorniFa(n) {
  const d = new Date();
  d.setHours(12, 0, 0, 0); // a mezzogiorno l'ora legale non fa cambiare giorno
  d.setDate(d.getDate() - n);
  return isoLocale(d);
}

// { dal, al } per l'API, oppure null se non c'è filtro per data.
function intervalloData() {
  if (stato.giorno) return { dal: stato.giorno, al: stato.giorno };
  switch (stato.periodo) {
    case "oggi": return { dal: giorniFa(0), al: giorniFa(0) };
    case "ieri": return { dal: giorniFa(1), al: giorniFa(1) };
    case "settimana": return { dal: giorniFa(6), al: giorniFa(0) };
    case "mese": return { dal: giorniFa(29), al: giorniFa(0) };
    default: return null;
  }
}

function filtroDataAttivo() {
  return Boolean(stato.giorno || stato.periodo);
}

function aggiungiDate(p) {
  const i = intervalloData();
  if (i) { p.set("dal", i.dal); p.set("al", i.al); }
  return p;
}

function paramConteggi() {
  const p = new URLSearchParams();
  if (stato.cerca) p.set("cerca", stato.cerca);
  aggiungiDate(p);
  const q = p.toString();
  return q ? `?${q}` : "";
}

// Pezzo del riepilogo ("di oggi", "del 1 gennaio 1970"...), vuoto senza filtro.
function descriviData() {
  if (stato.giorno) {
    const giorno = formattaGiorno(stato.giorno);
    return testoArchivio("archivio.data.riepilogo-giorno", "del {giorno}", { giorno }).replace("{giorno}", giorno);
  }
  switch (stato.periodo) {
    case "oggi": return testoArchivio("archivio.data.riepilogo-oggi", "di oggi");
    case "ieri": return testoArchivio("archivio.data.riepilogo-ieri", "di ieri");
    case "settimana": return testoArchivio("archivio.data.riepilogo-settimana", "dell'ultima settimana");
    case "mese": return testoArchivio("archivio.data.riepilogo-mese", "dell'ultimo mese");
    default: return "";
  }
}

function disegnaData() {
  for (const b of periodi.querySelectorAll("[data-periodo]")) {
    b.setAttribute("aria-pressed", String(!stato.giorno && b.dataset.periodo === stato.periodo));
  }
  inputGiorno.value = stato.giorno;
  inputGiorno.max = giorniFa(0);
  if (stato.giorno) inputGiorno.dataset.attivo = "";
  else delete inputGiorno.dataset.attivo;
}

function azzeraData() {
  stato.periodo = "";
  stato.giorno = "";
  disegnaData();
}

periodi.addEventListener("click", (e) => {
  const b = e.target.closest("[data-periodo]");
  if (!b) return;
  if (!stato.giorno && stato.periodo === b.dataset.periodo) return;
  stato.periodo = b.dataset.periodo;
  stato.giorno = "";
  stato.pagina = 1;
  disegnaData();
  aggiornaTutto();
});

inputGiorno.addEventListener("change", () => {
  const v = inputGiorno.value;
  if (v && !giornoValido(v)) return; // data ancora incompleta
  if (v === stato.giorno) return;
  stato.giorno = v;
  stato.periodo = "";
  stato.pagina = 1;
  disegnaData();
  aggiornaTutto();
});

disegnaData();

function leggiUrl() {
  const p = new URLSearchParams(location.search);
  return {
    categoria: p.get("categoria") || "",
    cerca: (p.get("cerca") || "").trim(),
    pagina: Math.max(1, parseInt(p.get("pagina"), 10) || 1),
  };
}

function scriviUrl() {
  const p = new URLSearchParams();
  if (stato.categoria) p.set("categoria", stato.categoria);
  if (stato.cerca) p.set("cerca", stato.cerca);
  if (stato.pagina > 1) p.set("pagina", stato.pagina);
  scriviDataUrl(p);
  const q = p.toString();
  history.replaceState(null, "", q ? `?${q}` : location.pathname);
}

function pensieri(n) {
  return n === 1 ? "1 pensiero" : `${n} pensieri`;
}

// Testo con le occorrenze della ricerca evidenziate, senza mai usare innerHTML.
function testoEvidenziato(contenitore, testo, termine) {
  if (!termine) { contenitore.textContent = testo; return; }
  const basso = testo.toLowerCase();
  const t = termine.toLowerCase();
  let i = 0;
  for (let j = basso.indexOf(t); j >= 0; j = basso.indexOf(t, i)) {
    contenitore.append(testo.slice(i, j));
    const m = document.createElement("mark");
    m.textContent = testo.slice(j, j + t.length);
    contenitore.append(m);
    i = j + t.length;
  }
  contenitore.append(testo.slice(i));
}

// --- Campionario: barra proporzionale e filtri -------------------------

async function caricaConteggi() {
  const q = paramConteggi();
  const r = await fetch(`/api/categorie${q}`);
  const dati = await r.json();
  categorie = dati.categorie;
  nomi = Object.fromEntries(categorie.map((c) => [c.chiave, c.nome]));
  if (stato.categoria && !nomi[stato.categoria]) stato.categoria = "";
  disegnaSpettro();
  disegnaFiltri();
}

function disegnaSpettro() {
  const totale = categorie.reduce((s, c) => s + c.conteggio, 0);
  spettroBox.hidden = totale === 0;
  document.getElementById("spettro-totale").textContent = totale;
  spettroBox.querySelector(".spettro-didascalia span").textContent =
    stato.cerca ? `Chi ha scritto «${stato.cerca}»` : "Chi scrive nel diario";
  spettro.replaceChildren(...categorie.filter((c) => c.conteggio > 0).map((c) => {
    const i = document.createElement("i");
    i.dataset.gruppo = c.chiave;
    i.style.flexGrow = c.conteggio;
    return i;
  }));
}

function disegnaFiltri() {
  const totale = categorie.reduce((s, c) => s + c.conteggio, 0);
  const voci = [{ chiave: "", nome: "Tutti", conteggio: totale }, ...categorie];
  filtri.replaceChildren(...voci.map((c) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "filtro";
    b.dataset.gruppo = c.chiave;
    b.setAttribute("aria-pressed", String(c.chiave === stato.categoria));
    b.setAttribute("aria-label", `${c.nome}, ${pensieri(c.conteggio)}`);
    const t = document.createElement("span");
    t.className = "tessera-piccola";
    const nome = document.createElement("span");
    nome.textContent = c.nome;
    const n = document.createElement("span");
    n.className = "n";
    n.textContent = c.conteggio;
    b.append(t, nome, n);
    b.addEventListener("click", () => {
      if (stato.categoria === c.chiave) return;
      stato.categoria = c.chiave;
      stato.pagina = 1;
      for (const altro of filtri.children) altro.setAttribute("aria-pressed", String(altro === b));
      carica();
    });
    return b;
  }));
  filtri.querySelector('[aria-pressed="true"]')?.scrollIntoView({ block: "nearest", inline: "nearest" });
}

// --- Elenco ------------------------------------------------------------

async function carica({ focus = false } = {}) {
  scriviUrl();
  const mia = ++richiesta;
  const p = new URLSearchParams({ pagina: stato.pagina, per_pagina: PER_PAGINA });
  if (stato.categoria) p.set("categoria", stato.categoria);
  if (stato.cerca) p.set("cerca", stato.cerca);
  aggiungiDate(p);
  elenco.setAttribute("aria-busy", "true");
  try {
    const r = await fetch(`/api/pensieri?${p}`);
    const dati = await r.json();
    if (!r.ok) throw new Error(dati.errore);
    if (mia !== richiesta) return; // è arrivata una richiesta più nuova
    stato.pagina = dati.pagina;
    scriviUrl();
    disegna(dati);
    if (focus) {
      riepilogo.focus({ preventScroll: true });
      riepilogo.scrollIntoView({ block: "start" });
    }
  } catch {
    if (mia === richiesta) riepilogo.textContent = "Non riesco a caricare l'archivio: riprova tra poco.";
  } finally {
    if (mia === richiesta) elenco.removeAttribute("aria-busy");
  }
}

function disegna(dati) {
  const parti = [pensieri(dati.totale)];
  if (stato.categoria) parti.push(nomi[stato.categoria]);
  if (stato.cerca) parti.push(`con «${stato.cerca}»`);
  if (filtroDataAttivo()) parti.push(descriviData());
  riepilogo.replaceChildren();
  const b = document.createElement("b");
  b.textContent = parti[0];
  riepilogo.append(b, parti.length > 1 ? " · " + parti.slice(1).join(" · ") : "");

  elenco.replaceChildren();
  if (!dati.pensieri.length) elenco.append(statoVuoto());
  for (const x of dati.pensieri) elenco.append(campione(x));

  paginazione.hidden = dati.pagine <= 1;
  pos.replaceChildren();
  const sr = document.createElement("span");
  sr.className = "sr";
  sr.textContent = `Pagina ${dati.pagina} di ${dati.pagine}`;
  const vis = document.createElement("span");
  vis.setAttribute("aria-hidden", "true");
  vis.textContent = `${dati.pagina} / ${dati.pagine}`;
  pos.append(sr, vis);
  prec.disabled = dati.pagina <= 1;
  succ.disabled = dati.pagina >= dati.pagine;
}

function campione(x) {
  const li = document.createElement("li");
  li.className = "campione";
  li.dataset.gruppo = x.categoria;

  const testa = document.createElement("div");
  testa.className = "campione-testa";
  const gruppo = document.createElement("span");
  gruppo.className = "campione-gruppo";
  gruppo.textContent = nomi[x.categoria] || x.categoria;
  const numero = document.createElement("span");
  numero.className = "numero";
  numero.textContent = numeroCatalogo(x.id);
  testa.append(gruppo, numero);

  const t = document.createElement("p");
  t.className = "campione-testo";
  testoEvidenziato(t, x.testo, stato.cerca);

  const giorno = document.createElement("time");
  giorno.className = "campione-giorno";
  giorno.dateTime = x.giorno;
  giorno.textContent = formattaGiorno(x.giorno);

  const corpo = document.createElement("div");
  corpo.className = "campione-corpo";
  corpo.append(t, giorno);
  li.append(testa, corpo);
  return li;
}

function statoVuoto() {
  const li = document.createElement("li");
  li.className = "vuoto";
  const p = document.createElement("p");
  const a = document.createElement("a");
  if (stato.cerca || stato.categoria || filtroDataAttivo()) {
    p.textContent = stato.cerca ? `Nessun pensiero con «${stato.cerca}».` : "Questo gruppo non ha ancora scritto.";
    if (!stato.cerca && filtroDataAttivo()) p.textContent = testoArchivio("archivio.data.vuoto", "Nessun pensiero in questo periodo.");
    a.href = "/archivio";
    a.textContent = "Vedi tutti i pensieri";
    a.addEventListener("click", (e) => {
      e.preventDefault();
      stato.categoria = ""; stato.cerca = ""; stato.pagina = 1; cerca.value = "";
      azzeraData();
      aggiornaTutto();
    });
  } else {
    p.textContent = "Il diario è ancora vuoto.";
    a.href = "/";
    a.textContent = "Scrivi il primo pensiero";
  }
  li.append(p, a);
  return li;
}

async function aggiornaTutto() {
  try { await caricaConteggi(); } catch { /* i filtri restano quelli di prima */ }
  carica();
}

prec.addEventListener("click", () => { stato.pagina--; carica({ focus: true }); });
succ.addEventListener("click", () => { stato.pagina++; carica({ focus: true }); });

let timer;
cerca.value = stato.cerca;
cerca.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(() => {
    const v = cerca.value.trim();
    if (v === stato.cerca) return;
    stato.cerca = v;
    stato.pagina = 1;
    aggiornaTutto();
  }, 350);
});

aggiornaTutto();
