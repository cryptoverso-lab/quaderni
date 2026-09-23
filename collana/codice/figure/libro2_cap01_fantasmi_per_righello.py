"""La figura del capitolo 1 del libro 2: il livello fantasma si sposta col righello.

Il paragrafo chiede se il livello che la regola di ridondanza dichiara non
autonomo sia sempre lo stesso — un gradino che al mercato manca — oppure cambi
con il righello. La figura e' una griglia righello per livello: un quadrato pieno
dove la regola marca il livello su tutti e tre i mercati, un cerchio vuoto sul
righello che **possiede** quel livello, dove la misura congelata lo dichiara. Se
i quadrati formano una scala che scende col righello, il fantasma e' il fondo
della catena di ciascun righello, non un fatto del mercato.

Le caselle vuote non sono zeri: sono livelli che la regola non marca su quel
righello, o che quel righello non raggiunge. La figura non li distingue perche'
la misura congelata non li distingue.

Da `dati/misure/ciclo-giornaliero.json` (carta CR-049).

    .venv\\Scripts\\python.exe codice\\figure\\libro2_cap01_fantasmi_per_righello.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
MISURA = RADICE / "dati" / "misure" / "ciclo-giornaliero.json"
NOMI_RIGHELLO = {"D": "giornaliero", "H2": "due ore", "H1": "un'ora",
                 "M30": "trenta minuti", "M15": "quindici minuti", "M5": "cinque minuti"}


def _grado(livello: str) -> int:
    resto = livello[1:].replace("−", "-").strip()
    return int(resto) if resto else 0


def _nome(livello: str) -> str:
    return livello.replace("-", "−")


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    dati = json.loads(MISURA.read_text(encoding="utf-8"))
    ridondanti = dati["ridondanti_per_timeframe"]
    proprietari = dati["proprietari"]
    righelli = [tf for tf in NOMI_RIGHELLO if tf in ridondanti]

    livelli = {liv for v in ridondanti.values() for liv in v["livelli"]} | set(proprietari)
    # La catena senza buchi: un livello che nessuno marca e nessuno possiede
    # resta una colonna vuota, non sparisce dall'asse.
    gradi = [_grado(liv) for liv in livelli]
    colonne = [f"T{g:+d}" if g else "T" for g in range(max(gradi), min(gradi) - 1, -1)]
    x_di = {liv: i for i, liv in enumerate(colonne)}
    y_di = {tf: len(righelli) - 1 - i for i, tf in enumerate(righelli)}

    fig, asse = layout.figura("normale")
    xs, ys = [], []
    for tf in righelli:
        for liv in ridondanti[tf]["livelli"]:
            if ridondanti[tf]["asset_per_livello"][liv] == 3:
                xs.append(x_di[liv])
                ys.append(y_di[tf])
    asse.scatter(xs, ys, marker="s", s=70, color=layout.tinta(0, schermo),
                 linewidths=0, zorder=3,
                 label="la regola marca il livello come non autonomo (3 mercati su 3)")

    px, py = [], []
    for liv, per_mercato in proprietari.items():
        tf = next(iter(per_mercato.values()))
        if tf in y_di and len(set(per_mercato.values())) == 1:
            px.append(x_di[liv])
            py.append(y_di[tf])
    asse.scatter(px, py, marker="o", s=70, facecolors="white",
                 edgecolors=layout.tinta(1, schermo), linewidths=1.1, zorder=3,
                 label="righello che possiede il livello")

    asse.set_xticks(range(len(colonne)))
    asse.set_xticklabels([_nome(c) for c in colonne])
    asse.set_yticks([y_di[tf] for tf in righelli])
    asse.set_yticklabels([NOMI_RIGHELLO[tf] for tf in righelli])
    asse.set_xlim(-0.6, len(colonne) - 0.4)
    asse.set_ylim(-0.6, len(righelli) - 0.4)
    asse.set_xlabel("livello della catena, dal più lungo al più corto")
    layout.cornice(asse)
    asse.grid(True, color="#e6e6e6", linewidth=0.4)
    layout.legenda_figura(fig, asse, ncols=1)

    return layout.salva(
        fig, "fantasmi_per_righello", libro=2, schermo=schermo,
        fatti={"righelli": len(righelli), "caselle_marcate": len(xs),
               "proprietari_disegnati": len(px),
               "file": "dati/misure/ciclo-giornaliero.json"})


if __name__ == "__main__":
    for schermo in (False, True):
        print(disegna(schermo=schermo))
