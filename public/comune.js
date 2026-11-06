// Funzioni comuni a home e archivio.

// I testi arrivano da /testi.js (window.TESTI e window.T, vedi diario/testi.py).
// Se quello script non si carica, T restituisce il testo di riserva.
if (typeof window.T !== "function") {
  window.TESTI = window.TESTI || {};
  window.T = function (chiave, riserva, parametri) {
    const testo = riserva !== undefined ? riserva : chiave;
    if (!parametri) return testo;
    return String(testo).replace(/\{(\w+)\}/g, (tutto, nome) => (nome in parametri ? String(parametri[nome]) : tutto));
  };
}

// Applica i testi agli elementi con data-testo (textContent) e
// data-testo-<attributo> (es. data-testo-placeholder, data-testo-aria-label).
function applicaTesti(radice = document) {
  for (const el of radice.querySelectorAll("*")) {
    for (const a of Array.from(el.attributes)) {
      if (!a.name.startsWith("data-testo") || !Object.prototype.hasOwnProperty.call(window.TESTI, a.value)) continue;
      if (a.name === "data-testo") el.textContent = window.TESTI[a.value];
      else el.setAttribute(a.name.slice("data-testo-".length), window.TESTI[a.value]);
    }
  }
}
applicaTesti();

const MESI = T("comune.mesi", "gennaio,febbraio,marzo,aprile,maggio,giugno,luglio,agosto,settembre,ottobre,novembre,dicembre")
  .split(",").map((m) => m.trim());

// 'AAAA-MM-GG' -> '3 novembre 2026' (senza passare da Date: niente slittamenti di fuso).
function formattaGiorno(giorno) {
  const [a, m, g] = String(giorno).split("-").map(Number);
  if (!a || !m || !g) return giorno;
  return T("comune.giorno", "{giorno} {mese} {anno}", { giorno: g, mese: MESI[m - 1], anno: a });
}

function numeroCatalogo(id) {
  return T("comune.numero", "N. {numero}", { numero: String(id).padStart(4, "0") });
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
