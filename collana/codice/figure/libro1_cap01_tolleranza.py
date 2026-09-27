"""La figura del capitolo 1 del libro 1: senza tolleranza, l'affermazione non decide.

Il capitolo prende «i cicli si annidano per due» e mostra che alla frase mancano
quattro cose per diventare una domanda. Questa figura misura che cosa costa la
mancanza di **una** delle quattro, la tolleranza.

A sinistra i dodici rapporti fra durate mediane di livelli contigui, misurati sui
tre mercati; a destra la quota di quei dodici che risulta «compatibile con il due»
al variare della tolleranza che si decide di accettare. A piu' o meno il dieci per
cento conferma un rapporto su quattro, a piu' o meno il venticinque cinque su sei, e
il banco non si chiude mai del tutto perche' una coppia sta oltre il doppio del due.
La tolleranza non seleziona una soglia naturale: la sceglie chi scrive. Chi non la
dichiara puo' leggere gli stessi dodici numeri come conferma o come smentita, e
nessuno dei due gli da' torto.

Entrano solo le coppie di livelli che la scala del capitolo 11 riporta come
misurate sul giornaliero, da T+1 a T+5: T e T+1 li' non si separano, T+7 ha due
cicli su un mercato solo e T+8 non ha campione, quindi i rapporti che li toccano
non sono misure.

I numeri vengono da `dati/serie/<mercato>_D/structures/nesting_scatter.json`, che
sono i rapporti gia' congelati e non ricalcolati qui.

    uv run python codice/figure/libro1_cap01_tolleranza.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
SERIE = RADICE / "dati" / "serie"

MERCATI = {"BTCUSDT": "BTC", "ETHUSDT": "ETH", "SOLUSDT": "SOL"}
SEGNI = ("o", "s", "^")

#: L'affermazione della tradizione, nella forma in cui la tradizione la enuncia.
ATTESO = 2.0

#: Le coppie di livelli misurate sul giornaliero (tbl-scala-unificata del cap. 11).
MISURATE = ("T+2->T+1", "T+3->T+2", "T+4->T+3", "T+5->T+4")


def _rapporti() -> dict[str, tuple[list[str], list[float]]]:
    """Per ogni mercato: le coppie di livelli e il rapporto misurato."""
    fuori = {}
    for mercato in MERCATI:
        percorso = SERIE / f"{mercato}_D" / "structures" / "nesting_scatter.json"
        traccia = json.loads(percorso.read_text(encoding="utf-8"))["tracce"]["Livelli"]
        coppie = [(c, float(v)) for c, v in zip(traccia["text"], traccia["y"])
                  if c in MISURATE]
        fuori[mercato] = ([c for c, _ in coppie], [v for _, v in coppie])
    return fuori


def _quota_compatibile(valori: list[float], tolleranza: np.ndarray) -> np.ndarray:
    """Quanti dei rapporti stanno entro `tolleranza` dal due, per ogni soglia."""
    scarti = np.abs(np.array(valori) - ATTESO) / ATTESO
    return np.array([(scarti <= t).mean() for t in tolleranza]) * 100.0


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    dati = _rapporti()
    tutti = [v for _, valori in dati.values() for v in valori]

    fig, (sinistra, destra) = layout.figura("normale", ncols=2)

    coppie = dati["BTCUSDT"][0]
    posizione = {c: k for k, c in enumerate(coppie)}
    for indice, (mercato, breve) in enumerate(MERCATI.items()):
        etichette, valori = dati[mercato]
        # Un piccolo scarto orizzontale per mercato: rapporti quasi uguali
        # (T+2→T+1 su ETH e SOL) altrimenti si coprono l'un l'altro.
        x = [posizione[c] + (indice - 1) * 0.16 for c in etichette]
        sinistra.plot(x, valori, SEGNI[indice], markersize=4, linestyle="none",
                      label=breve, **{k: v for k, v in
                                      layout.serie(indice, schermo).items()
                                      if k == "color"})
    sinistra.axhline(ATTESO, color="#1a1a1a", linewidth=0.8, linestyle="--")
    sinistra.annotate("il due della tradizione", xy=(0.98, ATTESO),
                      xycoords=("axes fraction", "data"), xytext=(0, -11),
                      textcoords="offset points", fontsize=7, ha="right")
    sinistra.set_xticks(range(len(coppie)))
    # Le etichette in orizzontale su meta' blocco testo si toccano e si
    # leggono come una riga sola: verticali costano due millimetri di altezza e
    # restano contabili.
    sinistra.set_xticklabels([c.replace("->", "→") for c in coppie],
                             rotation=90, ha="center", fontsize=5.4)
    sinistra.set_ylabel("rapporto misurato")
    sinistra.set_title("i dodici rapporti misurati", fontsize=8.0)
    sinistra.grid(axis="x", visible=False)

    tolleranza = np.linspace(0.0, 1.0, 201)
    quota = _quota_compatibile(tutti, tolleranza)
    destra.plot(tolleranza * 100, quota, **layout.serie(0, schermo))
    for soglia in (0.10, 0.25, 0.50):
        y = _quota_compatibile(tutti, np.array([soglia]))[0]
        destra.plot([soglia * 100], [y], "o", markersize=4, color="#1a1a1a" if not (schermo or layout.STAMPA_A_COLORI) else "#a63603")
        destra.annotate(f"±{int(soglia * 100)}%: {layout.numero(y, 0)}%",
                        # Tutte sotto il punto (sopra il ±50% il gradino della
                        # curva attraversava la scritta), le due a pari quota
                        # su due righe diverse.
                        xy=(soglia * 100, y), xytext=(-2, -22 if soglia == 0.50 else -11),
                        textcoords="offset points", fontsize=6.5, ha="left")
    destra.set_xlabel("tolleranza attorno al due (%)")
    destra.set_ylabel("compatibili (%)")
    destra.set_ylim(0, 105)
    destra.set_title("che cosa decide la tolleranza", fontsize=8.0)

    layout.legenda_figura(fig, sinistra, ncols=3)
    return layout.salva(fig, "tolleranza_nesting", libro=1, schermo=schermo)


if __name__ == "__main__":
    for modo in (False, True):
        print(disegna(schermo=modo))
