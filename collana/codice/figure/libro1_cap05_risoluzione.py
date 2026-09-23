"""Il capitolo 5: quante barre vale un livello, e su quale righello.

**Calcolo dal catalogo, non misura sui prezzi.** Ogni cella e' l'equazione della
risoluzione applicata a un livello e a un timeframe: il periodo nominale diviso
la durata di una barra. Nessun prezzo entra in questa figura, e la ragione per cui
sta qui e' che il risultato non dipende dai prezzi — dipende dal righello, ed e'
il punto del paragrafo.

I due pannelli sono lo stesso conto su due mercati con ore di scambio diverse.
A sinistra un mercato continuo, dove una giornata porta ventiquattro ore di barre;
a destra un listino azionario a sei ore e mezza, dove una giornata ne porta meno
di un terzo **e** solo cinque giorni su sette sono giorni di scambio. La stessa
riga della stessa tabella cade in due fasce diverse: **il proprietario di un
livello non e' una proprieta' del livello, e' una proprieta' della coppia livello
e mercato**.

Le tre fasce sono quelle dichiarate dal capitolo: sotto le trenta barre i
parametri del rilevatore toccano il proprio pavimento e due livelli vicini
diventano lo stesso rilevatore con due nomi; oltre le duemila il campione di quel
livello si assottiglia troppo. In mezzo il livello si risolve, e la cornice marca
il timeframe in cui la risoluzione e' piu' vicina al centro della finestra.

    uv run python codice/figure/libro1_cap05_risoluzione.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from matplotlib.colors import ListedColormap

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

#: Periodi nominali del catalogo, in giorni.
LIVELLI = {"T-2": 2.5, "T-1": 5.0, "T": 10.0, "T+1": 20.0, "T+2": 45.0,
           "T+3": 90.0, "T+4": 160.0, "T+5": 480.0}

#: Minuti per barra di ciascun timeframe.
MINUTI = {"M15": 15, "M30": 30, "H1": 60, "H2": 120, "H4": 240, "D": 1440, "W": 10080}

#: Gli estremi della finestra di risoluzione, in barre, e il centro geometrico.
PAVIMENTO, TETTO = 30.0, 2000.0
CENTRO = float(np.sqrt(PAVIMENTO * TETTO))

#: I due mercati: ore di scambio al giorno, e quota di giorni che sono sedute.
MERCATI = (("mercato continuo\n24 ore, sette giorni", 24.0, 1.0),
           ("listino azionario\n6 ore e mezza, cinque giorni su sette", 6.5, 5 / 7))


def _barre(periodo_giorni: float, tf: str, ore: float, sedute: float) -> float:
    """Barre per giorno di calendario: barre per seduta per quota di sedute.

    Il settimanale fa eccezione: una barra e' una settimana su qualunque listino,
    e le sedute non cambiano quante barre esistono.
    """
    if tf == "W":
        al_giorno = 1 / 7
    elif tf == "D":
        al_giorno = sedute
    else:
        al_giorno = ore * 60.0 / MINUTI[tf] * sedute
    return periodo_giorni * al_giorno


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    fig, assi = layout.figura("alta", ncols=2, sharey=True)

    for asse, (titolo, ore, sedute) in zip(assi, MERCATI):
        griglia = np.array([[_barre(p, tf, ore, sedute) for p in LIVELLI.values()]
                            for tf in MINUTI])
        fascia = np.where(griglia < PAVIMENTO, 0, np.where(griglia > TETTO, 2, 1))
        # La scala e' ordinata — sotto il pavimento, si risolve, oltre il
        # tetto — e in stampa resta monotona. A schermo il centro e' quello
        # che si deve vedere, e i due estremi lo incorniciano.
        toni = layout.bande(schermo)
        asse.imshow(fascia, cmap=ListedColormap(toni), vmin=-0.5, vmax=2.5,
                    aspect="auto", interpolation="nearest")

        for r, tf in enumerate(MINUTI):
            distanze = [abs(np.log(griglia[r, c] / CENTRO)) for c in range(len(LIVELLI))]
            for c in range(len(LIVELLI)):
                valore = griglia[r, c]
                testo = layout.numero(valore, 0 if valore >= 10 else 1)
                asse.text(c, r, testo, ha="center", va="center", fontsize=5.6,
                          color="white" if fascia[r, c] == 2 else "#1a1a1a")
        # nota: il testo resta nero (o bianco sulla banda scura) in tutte e
        # due le edizioni — e' un numero da leggere, non una serie.
        for c in range(len(LIVELLI)):
            colonna = [abs(np.log(griglia[r, c] / CENTRO))
                       if PAVIMENTO <= griglia[r, c] <= TETTO else np.inf
                       for r in range(len(MINUTI))]
            if np.isfinite(min(colonna)):
                r = int(np.argmin(colonna))
                asse.add_patch(__import__("matplotlib").patches.Rectangle(
                    (c - 0.5, r - 0.5), 1, 1, fill=False, edgecolor="#1a1a1a",
                    linewidth=1.4))

        asse.set_xticks(range(len(LIVELLI)))
        asse.set_xticklabels(LIVELLI, fontsize=6.4)
        asse.set_yticks(range(len(MINUTI)))
        asse.set_yticklabels(MINUTI, fontsize=6.8)
        asse.set_title(titolo, fontsize=7.6)
        asse.grid(visible=False)

    assi[0].set_ylabel("timeframe")
    legenda = chr(10).join((
        "livello del catalogo — nella cella, le barre che occupa",
        "chiaro: sotto le 30 barre il rilevatore tocca il pavimento · medio: si risolve",
        "scuro: oltre le 2000, campione troppo sottile · cornice: il proprietario",
    ))
    fig.supxlabel(legenda, fontsize=6.8, linespacing=1.7)
    return layout.salva(fig, "risoluzione_righello", libro=1, schermo=schermo)


if __name__ == "__main__":
    for modo in (False, True):
        print(disegna(schermo=modo))
