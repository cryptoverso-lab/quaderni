"""La figura del capitolo 23 del libro 2 (e della Parte II del libro 3).

Una soglia si giudica contro cio' che lo strumento produce **quando i cicli non
ci sono**. La misura congelata in `dati/misure/overlap-nulla.json` fa esattamente
questo: lo stesso rilevatore, con gli argomenti con cui gira in produzione, viene
applicato ai tre mercati e a duecento repliche per mercato — cento a fase
randomizzata e cento AAFT — e per ogni coppia di livelli adiacenti si misura la
sovrapposizione.

Il disegno mette sulla stessa riga il valore osservato e la mediana della nulla,
e traccia la soglia in uso. Se la nulla sta **sopra** la soglia, la soglia non
distingue niente: la supererebbe anche una serie senza cicli.

Dalla corsa del pavimento le righe sono **quindici**, ognuna letta sul righello
che la risolve — il giornaliero per T+4/T+5, le quattro ore per T+2/T+3, il minuto
per le coppie da T-7 a T-4 — e su **nessuna** la nulla supera la soglia; la piu'
vicina le resta sotto di un margine che si congela nel verbale. Il righello sta
nell'etichetta di ogni riga, come la didascalia lo dice (finding A24). La coppia
T/T+1 sul giornaliero, dove la nulla sta sopra, non e' fra queste righe: la dice
il testo. La versione di prima parlava di «tutte e nove le coppie del
giornaliero», che era la figura del primo giro.

Nessun numero e' trascritto: vengono tutti dal file di misura.

    .venv\\Scripts\\python.exe codice\\figure\\libro2_cap23_strumento.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]

BREVE = {"BTCUSDT": "BTC", "ETHUSDT": "ETH", "SOLUSDT": "SOL"}


def _misura() -> dict:
    percorso = RADICE / "dati" / "misure" / "overlap-nulla.json"
    return json.loads(percorso.read_text(encoding="utf-8"))


def disegna(schermo: bool = False, libro: int = 2) -> Path:
    layout.configura(schermo=schermo)
    dati = _misura()
    righe = list(dati["coppie_sul_giornaliero"])
    soglia = float(dati["soglia_in_uso"])

    fig, asse = layout.figura("normale")
    posizioni = np.arange(len(righe))[::-1].astype(float)

    osservati = np.array([r["osservato"] for r in righe], dtype=float)
    nulle = np.array([r["nulla_mediana"] for r in righe], dtype=float)

    for quota, osservato, nulla in zip(posizioni, osservati, nulle):
        asse.plot([min(osservato, nulla), max(osservato, nulla)], [quota, quota],
                  linewidth=0.7, color=layout.GRIGI[2], zorder=2)

    asse.plot(nulle, posizioni, marker="s", markersize=5, linestyle="none",
              zorder=4, markerfacecolor="white", markeredgewidth=0.9,
              color=layout.GRIGI[1] if not (schermo or layout.STAMPA_A_COLORI) else layout.COLORI_SCHERMO[1],
              label="mediana della nulla: lo stesso rilevatore su serie senza cicli")
    asse.plot(osservati, posizioni, marker="o", markersize=5, linestyle="none",
              zorder=5,
              color=layout.GRIGI[0] if not (schermo or layout.STAMPA_A_COLORI) else layout.COLORI_SCHERMO[0],
              label="osservato sul mercato")
    asse.axvline(soglia, linewidth=0.9, linestyle="--",
                 color=layout.GRIGI[0] if not (schermo or layout.STAMPA_A_COLORI) else layout.COLORI_SCHERMO[3],
                 zorder=3, label=f"soglia in uso ({layout.numero(soglia, 2)})")

    # Una riga sottile fra un righello e il successivo: le quindici righe sono
    # tre gruppi, e la didascalia li nomina uno per uno.
    for sopra, sotto, quota in zip(righe, righe[1:], posizioni[1:]):
        if sopra.get("righello") != sotto.get("righello"):
            asse.axhline(quota + 0.5, color=layout.GRIGI[3], linewidth=0.5, zorder=1)

    asse.set_yticks(posizioni)
    asse.set_yticklabels(
        [f"{BREVE.get(r['mercato'], r['mercato'])} · {r['coppia']}"
         + (f" · {r['righello']}" if r.get("righello") else "") for r in righe],
        fontsize=7.0)
    asse.set_xlabel("sovrapposizione fra i minimi di due livelli adiacenti")
    asse.grid(axis="y", visible=False)
    asse.set_ylim(posizioni.min() - 0.7, posizioni.max() + 0.7)
    layout.legenda_figura(fig, asse, ncols=2, fontsize=7)
    margini = [r["margine"] for r in righe if r.get("margine") is not None]
    fatti = {"righe": len(righe),
             "nulla_sopra_la_soglia": sum(bool(r.get("nulla_supera_la_soglia"))
                                          for r in righe),
             "margine_minimo": min(margini) if margini else None,
             "fonte": "dati/misure/overlap-nulla.json, coppie_sul_giornaliero"}
    return layout.salva(fig, "soglia_contro_lo_strumento", libro=libro,
                        schermo=schermo, fatti=fatti)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for su_schermo in (False, True):
        print(disegna(schermo=su_schermo, libro=2))
        print(disegna(schermo=su_schermo, libro=3))
