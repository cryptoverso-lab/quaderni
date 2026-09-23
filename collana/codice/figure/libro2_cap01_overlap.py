"""La figura del capitolo 1 del libro 2: la soglia dell'overlap e la sua nulla.

Due pannelli. A sinistra, per ogni coppia adiacente e ogni mercato, la
sovrapposizione osservata e la mediana della nube che lo stesso rilevatore
produce su serie senza struttura, con la riga verticale della soglia in uso: si
vede se la soglia stia a destra della nube (ha potere) o dentro (non ne ha). A
destra il margine della soglia sui quattro timeframe: il segno cambia fra il
giornaliero e le quattro ore, ed e' il punto del capitolo.

I numeri del pannello di sinistra vengono da `dati/misure/overlap-esteso.json`
— la corsa a copertura piena del lavoro 86, chiusa il 13 settembre 2026: undici
coppie su undici, trentatre' righe, e `T/T+1` finalmente misurata sul righello
che la possiede per intero (`H2`) invece di essere dichiarata cieca. Il pannello
di destra resta la corsa per risoluzione di `dati/misure/overlap-nulla.json`, che
e' un'altra misura e va detto.

    .venv\\Scripts\\python.exe codice\\figure\\libro2_cap01_overlap.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
MISURE = RADICE / "dati" / "misure"

BREVE = {"BTCUSDT": "BTC", "ETHUSDT": "ETH", "SOLUSDT": "SOL"}
NOMI_TF = {"W": "settim.", "D": "giorn.", "H4": "4 ore", "H1": "1 ora"}
#: I tre mercati sulla stessa riga: forma diversa, non colore — l'edizione di
#: stampa e' in grigi e il colore li renderebbe indistinguibili.
MARCATORE = {"BTCUSDT": "o", "ETHUSDT": "s", "SOLUSDT": "^"}
SCARTO = {"BTCUSDT": 0.22, "ETHUSDT": 0.0, "SOLUSDT": -0.22}


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    esteso = json.loads((MISURE / "overlap-esteso.json").read_text(encoding="utf-8"))
    dati = json.loads((MISURE / "overlap-nulla.json").read_text(encoding="utf-8"))
    bracci = dati["per_timeframe"]
    soglia = esteso["soglia_in_uso"]
    # Trentatre' righe su undici coppie: una riga per coppia, i tre mercati come
    # forme diverse sulla stessa riga. Trentatre' etichette starebbero dentro la
    # gabbia e non si leggerebbero: la coppia e' l'unita' dell'affermazione, il
    # mercato e' la replica.
    per_coppia: dict[str, list[dict]] = {}
    for riga in esteso["righe"]:
        per_coppia.setdefault(riga["coppia"], []).append(riga)
    ordine = sorted(per_coppia, key=lambda c: -min(r["margine"] for r in per_coppia[c]))

    fig, assi = layout.figura("alta", ncols=2,
                              gridspec_kw={"width_ratios": [1.5, 1.0]})
    colore_nube = layout.GRIGI[2] if not (schermo or layout.STAMPA_A_COLORI) else layout.COLORI_SCHERMO[3]
    colore_oss = layout.GRIGI[0] if not (schermo or layout.STAMPA_A_COLORI) else layout.COLORI_SCHERMO[1]

    posizioni = np.arange(len(ordine))[::-1]
    primo = True
    for y, coppia in zip(posizioni, ordine):
        for riga in sorted(per_coppia[coppia], key=lambda r: r["mercato"]):
            scarto = SCARTO.get(riga["mercato"], 0.0)
            assi[0].plot([riga["nulla_mediana"]] * 2,
                         [y + scarto - 0.12, y + scarto + 0.12],
                         color=colore_nube, linewidth=1.6, zorder=2,
                         label="mediana della nulla" if primo else None)
            assi[0].scatter([riga["osservato"]], [y + scarto], s=18,
                            marker=MARCATORE.get(riga["mercato"], "o"),
                            color=colore_oss, zorder=4, linewidths=0,
                            label=BREVE.get(riga["mercato"], riga["mercato"])
                            if y == posizioni[0] else None)
            primo = False
    assi[0].axvline(soglia, color=layout.GRIGI[0], linewidth=0.9, linestyle="--",
                    zorder=3, label="soglia in uso")
    assi[0].set_yticks(posizioni)
    assi[0].set_yticklabels([f"{c} · {esteso['righello_per_coppia'][c]}"
                             for c in ordine])
    assi[0].set_xlabel("sovrapposizione bidirezionale")
    minimo = min(min(r["osservato"], r["nulla_mediana"])
                 for righe in per_coppia.values() for r in righe)
    assi[0].set_xlim(max(0.0, minimo - 0.06), 1.0)
    assi[0].grid(axis="y", visible=False)

    y_tf = np.arange(len(bracci))[::-1]
    margini = [r["margine_peggiore"] for r in bracci]
    for indice, (y, riga) in enumerate(zip(y_tf, bracci)):
        stile = layout.riempimento(0 if riga["margine_peggiore"] >= 0 else 2, schermo)
        assi[1].barh(y, riga["margine_peggiore"], height=0.55, zorder=2, **stile)
    assi[1].axvline(0.0, color=layout.GRIGI[0], linewidth=0.8, zorder=3)
    assi[1].set_yticks(y_tf)
    assi[1].set_yticklabels([NOMI_TF.get(r["timeframe"], r["timeframe"]) for r in bracci])
    assi[1].set_xlabel("margine della soglia")
    assi[1].set_xlim(min(margini) - 0.08, max(margini) + 0.08)
    assi[1].grid(axis="y", visible=False)

    layout.legenda_figura(fig, assi[0], ncols=5)
    return layout.salva(fig, "overlap_nulla", libro=2, schermo=schermo)


if __name__ == "__main__":
    for schermo in (False, True):
        print(disegna(schermo=schermo))
