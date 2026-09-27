"""La seconda figura del capitolo 1: due tradizioni che non si sono mai lette.

**Schema**: non misura dati di mercato. Le date sono quelle di pubblicazione dei
lavori citati nel capitolo, e l'unica grandezza rappresentata e' il tempo.

Sopra la linea, la letteratura che data i punti di svolta con procedure
dichiarate; sotto, le scuole cicliche dell'analisi tecnica. Fra le due corsie non
c'e' nessuna freccia, e non e' una semplificazione: in nessuno dei lavori sopra
compare un rimando a quelli sotto, e viceversa. Il vuoto in mezzo e' il contenuto
della figura.

    uv run python codice/figure/libro1_cap01_due_tradizioni.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

#: (anno, etichetta, riga di sotto, altezza del gambo, allineamento del testo) —
#: la corsia della misura statistica. Altezza e allineamento si scelgono voce per
#: voce: due lavori a un anno di distanza (2003 e 2004) hanno i gambi quasi
#: sovrapposti, e con un'alternanza fissa il gambo dell'uno attraversava il testo
#: dell'altro. Dove due gambi sono vicini i testi si aprono verso l'esterno.
MISURA = [
    (1971, "Bry e Boschan", "datazione automatica\ndei punti di svolta", 0.30, "center"),
    (1989, "Hamilton", "modelli a cambio\ndi regime", 0.30, "center"),
    (2003, "Pagan e Sossounov", "fasi rialziste\ne ribassiste", 0.78, "right"),
    (2004, "Lunde e Timmermann", "dipendenza\ndalla durata", 1.26, "left"),
    (2011, "Claessens e altri", "cicli finanziari,\n44 paesi", 0.30, "left"),
]

#: La corsia delle scuole cicliche.
SCUOLE = [
    (1970, "Hurst", "il modello nominale\ne i sette principi", 0.30, "center"),
    (2001, "Ehlers", "trasformata di Hilbert\ne filtri adattativi", 0.78, "right"),
    (2013, "Ehlers", "l'autocorrelazione\ncome periodogramma", 0.30, "left"),
    (2005, "scuola italiana", "vent'anni di dispense\ne corsi", 1.26, "left"),
]


def _corsia(asse, voci, verso: int, schermo: bool, indice: int) -> None:
    """Una corsia: i gambi partono dalla linea e si alternano su due altezze.

    L'alternanza non e' decorazione: senza, i lavori a due anni di distanza si
    sovrappongono e la figura diventa illeggibile — che e' esattamente il difetto
    che il primo disegno di questa figura aveva.
    """
    stile = layout.serie(indice, schermo)
    colore = stile["color"]
    for anno, chi, cosa, quota, allineamento in sorted(voci):
        altezza = quota * verso
        asse.plot([anno, anno], [0.0, altezza], color=colore, linewidth=0.7)
        asse.plot([anno], [altezza], ("o", "s")[indice % 2], markersize=4, color=colore,
                  zorder=5)
        asse.annotate(f"{chi}, {anno}" + chr(10) + cosa,
                      xy=(anno, altezza + 0.06 * verso),
                      ha=allineamento, va="bottom" if verso > 0 else "top",
                      fontsize=6.0, color=colore, linespacing=1.2)


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    fig, asse = layout.figura("alta")

    asse.axhline(0.0, color="#808080", linewidth=0.8)
    _corsia(asse, MISURA, +1, schermo, 0)
    _corsia(asse, SCUOLE, -1, schermo, 1)

    # Le etichette di corsia a sinistra del primo lavoro: nessun gambo le attraversa.
    asse.annotate("la misura\ndei punti di svolta", xy=(1944.5, 0.12), fontsize=7.5,
                  ha="left", va="bottom", style="italic")
    asse.annotate("le scuole cicliche", xy=(1944.5, -0.12), fontsize=7.5,
                  ha="left", va="top", style="italic")
    asse.annotate("nessun rimando, in cinquant'anni, in nessuna delle due direzioni",
                  xy=(1993, 1.66), fontsize=7.5, ha="center", va="bottom")

    asse.set_xlim(1944, 2031)
    asse.set_ylim(-2.05, 2.05)
    asse.set_yticks([])
    asse.set_xticks([1970, 1980, 1990, 2000, 2010, 2020])
    asse.set_xticklabels(["1970", "1980", "1990", "2000", "2010", "2020"])
    asse.grid(visible=False)
    for lato in ("left", "bottom"):
        asse.spines[lato].set_visible(False)
    asse.tick_params(axis="y", length=0)

    return layout.salva(fig, "due_tradizioni", libro=1, schermo=schermo)


if __name__ == "__main__":
    for modo in (False, True):
        print(disegna(schermo=modo))
