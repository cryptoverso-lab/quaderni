"""La figura del capitolo 1 del libro 2: la sovrapposizione e' il rapporto, scritto due volte.

Il paragrafo chiede se la sovrapposizione fra i minimi di due livelli adiacenti sia
una seconda prova, indipendente dal rapporto fra le loro durate. La risposta sta in
una diagonale: sull'asse orizzontale la sovrapposizione che il solo rapporto
prevede (P figlio / P padre), su quello verticale quella che il rilevatore misura.
Se i quindici punti stanno sulla bisettrice, le due misure sono una.

Le due soglie del criterio compaiono come due rette — l'80% sulla misurata e la
sua traduzione sul rapporto, sull'attesa — e si incrociano sulla bisettrice: e'
il disegno di «le due soglie sono la stessa soglia».

I numeri vengono da `dati/misure/livelli-sovrapposizione.json`, congelato dalla
misura della ricerca.

    .venv\\Scripts\\python.exe codice\\figure\\libro2_cap01_attesa_sovrapposizione.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
MISURA = RADICE / "dati" / "misure" / "livelli-sovrapposizione.json"
FORME = {"Bitcoin": "o", "Ethereum": "s", "Solana": "^"}


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    dati = json.loads(MISURA.read_text(encoding="utf-8"))
    confronti = dati["confronti"]
    soglia = dati["soglia_phantom"]

    fig, asse = layout.figura("alta")
    asse.plot([0.2, 0.9], [0.2, 0.9], color=layout.GRIGI[2], linewidth=0.8,
              linestyle="--", zorder=1, label="misurata = attesa")
    asse.axhline(soglia, color=layout.GRIGI[1], linewidth=0.7, linestyle=":",
                 zorder=1, label="soglia dell'80% sulla sovrapposizione")
    asse.axvline(1.0 / dati["soglia_rapporto"], color=layout.GRIGI[1], linewidth=0.7,
                 linestyle="-.", zorder=1,
                 label="la stessa soglia sul rapporto fra le durate")

    for indice, (mercato, forma) in enumerate(FORME.items()):
        righe = [c for c in confronti if c["asset"] == mercato]
        asse.scatter([c["attesa_dal_rapporto"] for c in righe],
                     [c["sovrapposizione_del_motore"] for c in righe],
                     marker=forma, s=26, color=layout.tinta(indice, schermo),
                     linewidths=0, zorder=4, label=f"{mercato} ({len(righe)} coppie)")

    asse.set_xlim(0.2, 0.9)
    asse.set_ylim(0.2, 0.9)
    asse.set_aspect("equal")
    asse.set_xlabel("sovrapposizione attesa dal solo rapporto fra le durate")
    asse.set_ylabel("sovrapposizione misurata dal rilevatore")
    layout.cornice(asse)
    layout.legenda_figura(fig, asse, ncols=2)

    scarti = [abs(c["scarto_attesa_motore"]) for c in confronti]
    return layout.salva(
        fig, "attesa_sovrapposizione", libro=2, schermo=schermo,
        fatti={"coppie": len(confronti), "scarto_massimo": max(scarti),
               "concordano": sum(c["le_due_soglie_concordano"] for c in confronti),
               "file": "dati/misure/livelli-sovrapposizione.json"})


if __name__ == "__main__":
    for schermo in (False, True):
        print(disegna(schermo=schermo))
