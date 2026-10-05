"""Il capitolo 5: tre famiglie di rilevatori, la stessa serie, tre risposte.

A sinistra quanti minimi ciascuna famiglia produce sullo stesso periodo di
Bitcoin, livello per livello: le tre colonne non sono vicine, sono di ordini
diversi. A destra l'accordo fra le famiglie, **nei due versi**: la barra chiara
dice quanti minimi della prima famiglia trovano un vicino nella seconda, quella
scura il contrario. Le due barre di una stessa coppia non hanno la stessa altezza,
e la differenza e' la cardinalita': chi produce piu' minimi ne trova sempre in
proporzione di meno.

Legge `dati/misure/tre-rilevatori.json`, non ricalcola niente.

    uv run python codice/figure/libro1_cap05_tre_rilevatori.py
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

FAMIGLIE = ("a soglia", "a finestra", "a banda")
LIVELLI = ("T+1", "T+2", "T+3")
COPPIE = ("a finestra / a soglia", "a banda / a soglia", "a banda / a finestra")
BREVI = {"a finestra / a soglia": "finestra\ne soglia",
         "a banda / a soglia": "banda\ne soglia",
         "a banda / a finestra": "banda\ne finestra"}


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    righe = json.loads((MISURE / "tre-rilevatori.json").read_text(encoding="utf-8"))["righe"]
    di_btc = {r["livello"]: r for r in righe if r["asset"] == "Bitcoin"}

    fig, (sinistra, destra) = layout.figura("normale", ncols=2)

    base = np.arange(len(LIVELLI))
    larghezza = 0.26
    for indice, famiglia in enumerate(FAMIGLIE):
        sinistra.bar(base + (indice - 1) * larghezza,
                     [di_btc[liv]["conteggi"][famiglia] for liv in LIVELLI],
                     width=larghezza, label=famiglia,
                     **layout.riempimento(indice, schermo))
    sinistra.set_yscale("log")
    # Tacche intere: le potenze di dieci con la mantissa non si leggono a colpo d'occhio.
    tacche = [20, 30, 50, 100, 200, 300]
    sinistra.set_yticks(tacche)
    sinistra.set_yticklabels([str(t) for t in tacche])
    sinistra.yaxis.set_minor_formatter(__import__("matplotlib").ticker.NullFormatter())
    sinistra.set_xticks(base)
    sinistra.set_xticklabels(LIVELLI)
    sinistra.set_xlabel("livello interrogato")
    sinistra.set_ylabel("minimi trovati su Bitcoin")
    sinistra.set_title("quanti minimi", fontsize=8.0)
    sinistra.grid(axis="x", visible=False)

    base2 = np.arange(len(COPPIE))
    medie = {"primo": [], "secondo": []}
    for coppia in COPPIE:
        medie["primo"].append(float(np.mean(
            [r["accordo"][coppia]["quota_sul_primo_pct"] for r in righe])))
        medie["secondo"].append(float(np.mean(
            [r["accordo"][coppia]["quota_sul_secondo_pct"] for r in righe])))
    # Tinte che il pannello sinistro non usa: il rosso li' e' «a finestra», e ripetuto qui
    # per «dalla prima alla seconda» dava alla stessa tinta due significati (04/10/2026).
    destra.bar(base2 - 0.19, medie["primo"], width=0.36, label="dalla prima alla seconda",
               **layout.riempimento(3, schermo))
    destra.bar(base2 + 0.19, medie["secondo"], width=0.36, label="dalla seconda alla prima",
               facecolor="white", edgecolor=layout.tinta(3, schermo), linewidth=0.9)
    destra.set_xticks(base2)
    # Etichette corte e fitte: in inglese le tre coppie si toccavano, e l'asse
    # lungo urtava la legenda in alto.
    destra.set_xticklabels([BREVI[c] for c in COPPIE], fontsize=5.8)
    destra.set_ylabel("minimi con un vicino (%)")
    destra.set_ylim(0, 108)
    destra.set_title("quanto si accordano", fontsize=8.0)
    destra.grid(axis="x", visible=False)
    destra.legend(loc="upper right", frameon=False, fontsize=6.0)

    layout.legenda_figura(fig, sinistra, ncols=3)
    return layout.salva(fig, "tre_rilevatori", libro=1, schermo=schermo)


if __name__ == "__main__":
    for modo in (False, True):
        print(disegna(schermo=modo))
