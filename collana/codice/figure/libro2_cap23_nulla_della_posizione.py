"""La figura del capitolo 23 del libro 2: la nulla che indovina, misurata.

Il caso «la nulla che indovina» dice che il valore atteso per caso della posizione
mediana del massimo — un mezzo — era stato dedotto, e che misurandolo con la
stessa procedura su serie senza cicli il centro della nube vale proprio 0,50:
l'osservato sta dentro la nube in quattordici combinazioni su quindici. La figura
mette le quindici combinazioni una per riga: la fascia dal 5° al 95° percentile
delle repliche a fase randomizzata, il loro centro e l'osservato. La fascia e' al
novanta per cento, il verdetto della carta e' bilaterale al cinque: un punto
appena oltre la fascia puo' restare dentro il verdetto, e il segno lo distingue.

Legge `dati/misure/posizione-massimo-nulla.json` (carta `CR-005`, V2).

    .venv\\Scripts\\python.exe codice\\figure\\libro2_cap23_nulla_della_posizione.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
MISURA = RADICE / "dati" / "misure" / "posizione-massimo-nulla.json"
NOMI = {"BTCUSDT": "Bitcoin", "ETHUSDT": "Ethereum", "SOLUSDT": "Solana"}


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    dati = json.loads(MISURA.read_text(encoding="utf-8"))
    righe = [r for r in dati["righe"] if r["decisiva"]]

    fig, asse = layout.figura("alta")
    scuro = layout.tinta(0, schermo)
    evidente = layout.tinta(1, schermo, grigio=0)
    ys, etichette = [], []
    dentro_x, dentro_y, fuori_x, fuori_y = [], [], [], []
    y = 0.0
    mercato_prima = None
    for r in righe:
        if mercato_prima is not None and r["mercato"] != mercato_prima:
            y += 0.6
        mercato_prima = r["mercato"]
        nulla = r["fase"]
        asse.plot([nulla["nulla_p05"], nulla["nulla_p95"]], [y, y], color=layout.GRIGI[2],
                  linewidth=3.2, solid_capstyle="butt", zorder=2,
                  label="repliche senza cicli: dal 5° al 95° percentile" if not ys else None)
        asse.scatter([nulla["nulla_mediana"]], [y], s=16, marker="s", facecolor="white",
                     edgecolor=layout.GRIGI[0], linewidth=0.8, zorder=3,
                     label="centro delle repliche" if not ys else None)
        (fuori_x if nulla["fuori_dalla_nulla"] else dentro_x).append(r["osservato"])
        (fuori_y if nulla["fuori_dalla_nulla"] else dentro_y).append(y)
        ys.append(y)
        etichette.append(f"{NOMI[r['mercato']]} {r['livello']}")
        y += 1.0
    asse.scatter(dentro_x, dentro_y, s=20, marker="o", color=scuro, zorder=4,
                 label="osservato, dentro il verdetto")
    asse.scatter(fuori_x, fuori_y, s=30, marker="D", color=evidente, zorder=4,
                 label="osservato, fuori dal verdetto")
    asse.axvline(0.5, color=layout.GRIGI[1], linewidth=0.8, linestyle="--", zorder=1,
                 label="il valore dedotto: 0,50")
    asse.set_yticks(ys, etichette, fontsize=6.5)
    asse.set_ylim(y - 0.4, -0.6)
    asse.set_xlim(0.33, 0.67)
    asse.set_xticks([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65])
    asse.grid(axis="y", visible=False)
    asse.set_xlabel("posizione mediana del massimo dentro il ciclo")
    layout.legenda(asse, ncols=2, fontsize=6.3)
    return layout.salva(fig, "cap23_nulla_della_posizione", libro=2, schermo=schermo,
                        fatti={"fonte": "dati/misure/posizione-massimo-nulla.json",
                               "combinazioni": len(righe), "dentro": len(dentro_x),
                               "fuori": len(fuori_x)})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for su_schermo in (False, True):
        print(disegna(schermo=su_schermo))
