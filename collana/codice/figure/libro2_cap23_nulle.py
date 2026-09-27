"""La figura del capitolo 23 — il nullo creduto, il nullo misurato, l'osservato.

Il capitolo elenca sei modi di misurare lo strumento credendo di misurare il
mercato. Tre di quei sei condividono la stessa forma, e la forma si vede solo
mettendoli accanto: in tutti e tre qualcuno aveva **dedotto** il valore di
riferimento invece di misurarlo, e l'osservato — che pareva parlare del mercato
— sta addosso al valore che la procedura produce da sola.

I tre casi hanno unita' diverse — una quota di successioni ammesse, una quota di
sovrapposizione fra livelli, un rapporto fra durate — e vengono portati sullo
stesso asse dividendo per il **riferimento creduto**: la base teorica 0,50 nel
primo, la soglia in uso 0,80 nel secondo, la simmetria 1,00 nel terzo. E' l'unico
numero che i tre casi hanno in comune per costruzione, perche' vale uno.
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


def misura(nome: str) -> dict:
    return json.loads((MISURE / f"{nome}.json").read_text(encoding="utf-8"))


def _casi() -> list[tuple[str, list[tuple[float, float]]]]:
    """I tre casi, ciascuno con le coppie (nullo misurato, osservato).

    Entrambi i valori sono gia' divisi per il nullo creduto del caso.
    """
    sequenze = misura("sequenze-h4")
    creduto = sequenze["base_teorica_4t"]
    a = [
        (r["quota_fase_mediana"] / creduto, r["quota_ammesse"] / creduto)
        for r in sequenze["confronti"]
    ]

    overlap = misura("overlap-nulla")
    soglia = overlap["soglia_in_uso"]
    b = [
        (r["nulla_mediana"] / soglia, r["osservato"] / soglia)
        for r in overlap["coppie_sul_giornaliero"]
    ]

    asimmetria = misura("asimmetria-surrogati")
    c = [
        (r["fase_mediana"], r["rapporto_osservato"])
        for r in asimmetria["confronti"]
    ]

    # Il valore del riferimento sta in didascalia e non nell'etichetta: tre
    # etichette lunghe due righe spingono la figura oltre la gabbia di 130 mm,
    # e il gate la rifiuta.
    return [
        (f"sequenze ammesse di polarità ({len(a)})", a),
        (f"sovrapposizione fra livelli ({len(b)})", b),
        (f"asimmetria salita-discesa ({len(c)})", c),
    ]


def nulle_credute_e_misurate(schermo: bool = False) -> Path:
    """Dove sta il nullo misurato, rispetto a quello che era stato dedotto.

    La linea verticale a uno e' il riferimento creduto. I cerchi vuoti sono i nulli
    **misurati** con la stessa procedura su serie senza cicli; i pieni sono i
    valori osservati sui mercati. Quello che si ripete nei tre casi non e' da
    che parte della linea si finisce — cambia — ma che le due nuvole si
    sovrappongono fra loro: l'osservato segue il valore misurato, non quello
    creduto, e la distanza dalla linea e' una proprieta' della procedura.
    """
    layout.configura(schermo=schermo)
    casi = _casi()

    fig, asse = layout.figura("normale")
    posizioni = np.arange(len(casi))[::-1].astype(float)
    tono = layout.COLORI_SCHERMO[0] if (schermo or layout.STAMPA_A_COLORI) else layout.GRIGI[0]

    asse.axvline(1.0, linewidth=1.0, color=tono, zorder=3)
    for indice, (posizione, (_, coppie)) in enumerate(zip(posizioni, casi)):
        misurati = [m for m, _ in coppie]
        osservati = [o for _, o in coppie]
        # Le due nuvole stanno su due righe vicine e non sulla stessa: si
        # sovrappongono quasi ovunque, ed e' proprio la cosa da far vedere.
        asse.plot(
            misurati, np.full(len(misurati), posizione + 0.16),
            linestyle="none", marker="o", markersize=3.4,
            markerfacecolor="white", markeredgecolor=tono, markeredgewidth=0.8,
            zorder=4, label="valore misurato dalla procedura" if indice == 0 else None,
        )
        asse.plot(
            osservati, np.full(len(osservati), posizione - 0.16),
            linestyle="none", marker="o", markersize=3.4,
            markerfacecolor=tono, markeredgecolor=tono, markeredgewidth=0.8,
            zorder=4, label="osservato sul mercato" if indice == 0 else None,
        )


    asse.set_yticks(posizioni)
    asse.set_yticklabels([nome for nome, _ in casi], fontsize=7.2)
    asse.set_xlabel("in rapporto al riferimento creduto")
    asse.set_ylim(-0.6, len(casi) - 0.4)
    asse.grid(axis="y", visible=False)
    layout.cornice(asse)
    # Dentro il riquadro, a destra della linea: sopra, il testo stava a cavallo della
    # cornice superiore (27/09/2026).
    layout.etichetta_curva(asse, 1.0, len(casi) - 0.62, "il riferimento creduto",
                           scarto=(4.0, 0.0), va="center")
    # La legenda appartiene alla FIGURA e non al riquadro: ancorata al
    # riquadro deborda a destra, perche' le etichette di sinistra spostano
    # l'area dati, e il ritaglio porta la figura a 132 mm su 130 di gabbia.
    layout.legenda_figura(fig, asse, ncols=2, fontsize=7)
    return layout.salva(fig, "strumento_nulle_credute", libro=2, schermo=schermo)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for schermo in (False, True):
        print(nulle_credute_e_misurate(schermo=schermo))
