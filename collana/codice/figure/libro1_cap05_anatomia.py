"""La figura del capitolo 5 del libro 1: l'anatomia di un ciclo, e il righello.

Due pannelli sulla **stessa** finestra di prezzo, con lo stesso rilevatore e una
sola cosa diversa: il periodo interrogato. Sopra, il periodo del livello `T+2`;
sotto, quello di `T+1`.

Il pannello alto serve a nominare le grandezze del capitolo su un caso vero —
minimo iniziale, minimo finale, durata, massimo interno, escursione, posizione del
massimo e polarita' — e mostra
che nessuna di esse esiste prima che il righello abbia deciso dove sono i minimi.
Il pannello basso serve a dire la cosa che il capitolo ripete: cambiando il
periodo interrogato cambiano i minimi, quindi cambiano le durate, quindi cambia
ogni numero che da esse discende. **Non e' rumore di misura: e' la definizione
che si sposta.**

La serie e' il logaritmo delle chiusure giornaliere di Bitcoin dallo snapshot
congelato; il rilevatore e' quello elementare di `acbook.surrogati` — il punto
piu' basso in una finestra centrata di mezzo periodo — lo stesso applicato ai
dati veri e alle repliche in tutto il lavoro.

La figura non aggiunge nessun numero al testo: illustra definizioni.

    .venv\\Scripts\\python.exe codice\\figure\\libro1_cap05_anatomia.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout, surrogati  # noqa: E402

SIMBOLO = "BTCUSDT"
#: La finestra disegnata, in barre giornaliere dallo snapshot. Scelta una volta
#: e scritta qui: contiene piu' cicli `T+2` interi e non e' stata cercata fra
#: molte per trovare la piu' bella.
DA, A = 1500, 1900
PERIODI = (("T+2", 45), ("T+1", 20))


def _tratto() -> np.ndarray:
    serie = surrogati.chiusure(SIMBOLO)
    return serie[DA:A]


def _anatomia(asse, serie: np.ndarray, indici: np.ndarray, schermo: bool) -> None:
    """Marca sul primo ciclo intero le cinque grandezze del capitolo."""
    if len(indici) < 2:
        return
    inizio, fine = int(indici[0]), int(indici[1])
    tratto = serie[inizio : fine + 1]
    cima = inizio + int(np.argmax(tratto))

    ampiezza = float(serie.max()) - float(serie.min())
    quota = float(serie.min()) - 0.07 * ampiezza
    asse.annotate(
        "", xy=(inizio, quota), xytext=(fine, quota),
        arrowprops={"arrowstyle": "<->", "color": layout.GRIGI[1], "linewidth": 0.7},
    )
    asse.text(inizio + 0.75 * (fine - inizio), quota, "durata", ha="center", va="center",
              fontsize=7.0, zorder=7,
              bbox={"facecolor": "white", "edgecolor": "none", "pad": 2.0})
    # La posizione del massimo, pi, sulla freccia della durata: e' una frazione di lei.
    asse.plot([cima, cima], [quota - 0.012 * ampiezza, quota + 0.012 * ampiezza],
              color=layout.GRIGI[1], linewidth=0.7)
    asse.text(cima, quota + 0.02 * ampiezza,
              f"π = {layout.numero((cima - inizio) / (fine - inizio), 2)}",
              ha="center", va="bottom", fontsize=7.0)

    asse.annotate(
        "", xy=(cima, serie[inizio]), xytext=(cima, serie[cima]),
        arrowprops={"arrowstyle": "<->", "color": layout.GRIGI[1], "linewidth": 0.7},
    )
    # In basso a sinistra della freccia: li' sotto il prezzo non passa.
    asse.text(cima - 3, serie[inizio], "escursione", ha="right", va="bottom", fontsize=7.0)
    verso = "negativa" if serie[fine] < serie[inizio] else "positiva"
    confronto = "più basso" if verso == "negativa" else "più alto"
    asse.text(fine + 4, serie[fine] - 0.02 * ampiezza,
              f"polarità {verso}:\nminimo finale {confronto}",
              ha="left", va="top", fontsize=6.4, linespacing=1.3)
    asse.plot([cima], [serie[cima]], marker="^", markersize=5,
              color=layout.GRIGI[0] if not (schermo or layout.STAMPA_A_COLORI) else layout.COLORI_SCHERMO[1],
              linestyle="none", zorder=6)
    asse.text(cima, serie[cima], "massimo interno  ", ha="right", va="bottom",
              fontsize=7.0)


def disegna(schermo: bool = False) -> Path:
    """Una cornice sola: la serie si disegna una volta, i righelli sono due.

    Disegnare due volte la stessa finestra di prezzo, una per righello, costava
    meta' figura per ripetere un dato identico e costringeva il lettore a fare
    con la memoria il confronto che l'occhio fa da solo. Qui la serie sta sopra
    con i minimi del righello piu' grosso, e le due fasce in basso mettono i due
    conteggi uno sotto l'altro.
    """
    layout.configura(schermo=schermo)
    serie = _tratto()
    passi = np.arange(len(serie))

    fig, asse = layout.figura("alta")
    layout.cornice(asse)

    letture = [(nome, periodo, surrogati.minimi(serie, periodo)) for nome, periodo in PERIODI]
    principale = letture[0]

    asse.plot(passi, serie, linewidth=0.8, **{**layout.serie(0, schermo), "linestyle": "-"})
    for i in principale[2]:
        asse.axvline(i, linewidth=0.5, linestyle=":", color=layout.GRIGI[2], zorder=0)
    asse.plot(
        principale[2], serie[principale[2]], marker="o", markersize=4.5,
        linestyle="none", zorder=5,
        color=layout.GRIGI[0] if not (schermo or layout.STAMPA_A_COLORI) else layout.COLORI_SCHERMO[0],
        markerfacecolor="white", markeredgewidth=0.9,
    )
    _anatomia(asse, serie, principale[2], schermo)

    # Le due fasce: una riga per righello, con periodo e conteggio scritti.
    basso, alto = float(serie.min()), float(serie.max())
    ampiezza = alto - basso
    passo = 0.105 * ampiezza
    prima_riga = basso - 0.21 * ampiezza
    for indice, (nome, periodo, indici) in enumerate(letture):
        quota = prima_riga - indice * passo
        asse.scatter(indici, np.full(len(indici), quota), marker="D", s=11,
                     color=layout.GRIGI[1 + indice % 2], zorder=4)
        layout.etichetta_curva(
            asse, 3.0, quota,
            f"righello {nome}: {periodo // 2} barre per lato — {len(indici)} minimi",
            fontsize=6.0, va="bottom", ha="left", scarto=(0.0, 2.5),
        )

    asse.set_xlabel("barre giornaliere dall'inizio della finestra")
    asse.set_ylabel("log prezzo")
    asse.set_xlim(0, len(serie) - 1)
    asse.set_ylim(prima_riga - (len(letture) - 0.3) * passo, alto + 0.05 * ampiezza)
    return layout.salva(fig, "anatomia_ciclo", libro=1, schermo=schermo)


if __name__ == "__main__":
    for su_schermo in (False, True):
        print(disegna(schermo=su_schermo))
