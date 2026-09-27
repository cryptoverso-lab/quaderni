"""La figura del capitolo 1 del libro 2: T e T+1 su tre righelli.

Tre pannelli, uno per ciascuno dei tre indicatori con cui la regola dichiara che
un livello non e' autonomo, misurati sulla **stessa** coppia `T`/`T+1` e sulla
stessa storia, da tre risoluzioni: il giornaliero — dove la decisione su `T+1`
era stata presa —, le due ore, che e' il timeframe proprietario di `T+1`, e
l'ora. La riga tratteggiata e' la soglia; la freccia dice da che parte sta la
risposta «non e' un livello autonomo». Sul giornaliero i tre indicatori stanno
tutti dalla parte ridondante; sui due righelli che risolvono la coppia stanno
tutti dall'altra, e non di poco.

I numeri vengono da `dati/misure/ciclo-giornaliero.json`, blocco
`controllo_t_t1`: sono il braccio di controllo della carta `CR-049`, misurato
prima dei bracci nuovi e con le stesse soglie di produzione.

    .venv\\Scripts\\python.exe codice\\figure\\libro2_cap01_t_t1_righello.py
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

NOMI_TF = {"D": "giorn.", "H2": "2 ore", "H1": "1 ora"}
#: (chiave minima, chiave massima, titolo, chiave della soglia, verso in cui la
#: soglia dichiara il livello ridondante, tetto dell'asse).
PANNELLI = (
    ("overlap_min", "overlap_max", "sovrapposizione dei minimi", "overlap",
     "sopra", 1.0),
    ("rapporto_min", "rapporto_max", "rapporto fra le durate", "rapporto",
     "sotto", 2.6),
    ("vuoti_min", "vuoti_max", "cicli senza sotto-cicli", "cicli_vuoti",
     "sopra", 1.0),
)


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    dati = json.loads((MISURE / "ciclo-giornaliero.json").read_text(encoding="utf-8"))
    righe = sorted(dati["controllo_t_t1"], key=lambda r: r["barre_per_giorno"])
    soglie = dati["soglie"]

    x = np.arange(len(righe), dtype=float)
    etichette = [NOMI_TF.get(r["timeframe"], r["timeframe"]) for r in righe]

    fig, assi = layout.figura("normale", ncols=3)
    for indice, (chiave_lo, chiave_hi, titolo, chiave_soglia, verso, tetto) in \
            enumerate(PANNELLI):
        asse = assi[indice]
        for posizione, riga in zip(x, righe):
            ridondante = riga["esito"] == "RIDONDANTE"
            # La barra del braccio di controllo e' CHIARA davvero, come dice la didascalia:
            # il verde pieno aveva la luminanza del blu, e in grigi le due erano uguali.
            stile = ({"facecolor": layout.BANDE_GRIGI[0], "edgecolor": layout.tinta(2, schermo),
                      "linewidth": 0.9} if ridondante else layout.riempimento(0, schermo))
            altezza = (riga[chiave_lo] + riga[chiave_hi]) / 2.0
            asse.bar(posizione, altezza, width=0.6, zorder=2, **stile)
            asse.plot([posizione, posizione], [riga[chiave_lo], riga[chiave_hi]],
                      color=layout.GRIGI[0], linewidth=1.2, zorder=4)
        soglia = soglie[chiave_soglia]
        asse.axhline(soglia, color=layout.GRIGI[0], linewidth=0.9,
                     linestyle="--", zorder=3)
        # La lettura della soglia sta nel titolo e non dentro il riquadro: una
        # nota ancorata alla riga finirebbe sopra le barre a ogni rigenerazione.
        asse.set_title(f"{titolo}\nridondante {verso} {layout.numero(soglia)}",
                       fontsize=8.0)
        asse.set_xticks(x)
        asse.set_xticklabels(etichette)
        asse.set_xlim(-0.6, len(righe) - 0.4)
        asse.set_ylim(0.0, tetto)
        asse.grid(axis="x", visible=False)
    assi[0].set_ylabel("valore misurato")
    assi[1].set_xlabel("righello, dal più grossolano al più fine")
    return layout.salva(fig, "t_t1_righello", libro=2, schermo=schermo)


if __name__ == "__main__":
    for schermo in (False, True):
        print(disegna(schermo=schermo))
