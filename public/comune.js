// Funzioni comuni a home e archivio.

const MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
  "agosto", "settembre", "ottobre", "novembre", "dicembre"];

// 'AAAA-MM-GG' -> '3 novembre 2026' (senza passare da Date: niente slittamenti di fuso).
function formattaGiorno(giorno) {
  const [a, m, g] = String(giorno).split("-").map(Number);
  if (!a || !m || !g) return giorno;
  return `${g} ${MESI[m - 1]} ${a}`;
}

function numeroCatalogo(id) {
  return "N. " + String(id).padStart(4, "0");
}

function icona(nome, classe = "icona") {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("class", classe);
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS(ns, "use");
  use.setAttribute("href", "#i-" + nome);
  svg.append(use);
  return svg;
}

function leggiMemoria(chiave) {
  try { return localStorage.getItem(chiave); } catch { return null; }
}
function scriviMemoria(chiave, valore) {
  try {
    if (valore === null) localStorage.removeItem(chiave);
    else localStorage.setItem(chiave, valore);
  } catch { /* memoria non disponibile: pazienza */ }
}
