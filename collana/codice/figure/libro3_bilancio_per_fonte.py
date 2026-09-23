"""La figura del capitolo 1 del libro 3: le carte per autore della fonte.

Chi e' stato messo alla prova, e come e' andata. Una barra per tradizione, divisa
nei tre verdetti ammessi piu' il segmento delle carte scritte e non ancora
testate.

**Due pannelli e due scale, dichiarate.** Le tradizioni hanno fra zero e quattro
affermazioni; la ricerca stessa ne ha oltre cinquanta. Sullo stesso asse le prime
sparirebbero, e la figura direbbe una cosa sola — che la ricerca ha interrogato
soprattutto se' stessa — nascondendo quella per cui esiste, cioe' come sia andata
a ciascuna scuola. I due pannelli portano scritta la propria scala, e la
differenza di lunghezza resta leggibile nei numeri.

Le tradizioni con **zero** carte compaiono, ed e' il punto: uno zero che non si
disegna e' uno zero che non si legge. Vengono dall'elenco dichiarato
nell'ingest, non da cio' che le carte contengono.

I numeri vengono da `dati/misure/carte-ricerca.json`.

    .venv\\Scripts\\python.exe codice\\figure\\libro3_bilancio_per_fonte.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]

SEGMENTI = (
    ("CONFERMATA", "confermate"),
    ("FALSIFICATA", "falsificate"),
    ("NON_PROVATA", "non provate"),
)
LA_RICERCA = "CyclicalResearch"


def _dati() -> dict:
    percorso = RADICE / "dati" / "misure" / "carte-ricerca.json"
    return json.loads(percorso.read_text(encoding="utf-8"))


def _per_fonte(dati: dict) -> dict:
    """Le sole **affermazioni** per autore della fonte, e a parte i concetti.

    `per_autore_della_fonte` conta anche i concetti, che non si falsificano: il
    concetto di livello di Hurst (`CO-002`) finiva disegnato come «confermata»
    accanto a un principio caduto (finding A2). Si riconta dall'anagrafica
    congelata, carta per carta, tenendo le affermazioni nelle barre e i concetti
    in una nota accanto. Gli autori restano quelli dichiarati nell'ingest,
    compresi quelli a zero.
    """
    fonti = {nome: {"carte": 0, "testate": 0, "verdetti": {}, "concetti": 0}
             for nome in dati["per_autore_della_fonte"]}
    for carta in dati["carte"]:
        voce = fonti.setdefault(carta["autore"], {"carte": 0, "testate": 0,
                                                  "verdetti": {}, "concetti": 0})
        if carta["famiglia"] != "claims":
            voce["concetti"] += 1
            continue
        voce["carte"] += 1
        if carta["verdetto"]:
            voce["testate"] += 1
            voce["verdetti"][carta["verdetto"]] = voce["verdetti"].get(carta["verdetto"], 0) + 1
    return fonti


def _barre(asse, righe: list[tuple[str, dict]], schermo: bool) -> None:
    posizioni = np.arange(len(righe))[::-1].astype(float)
    sinistra = np.zeros(len(righe))
    for indice, (chiave, etichetta) in enumerate(SEGMENTI):
        valori = np.array([v["verdetti"].get(chiave, 0) for _, v in righe],
                          dtype=float)
        asse.barh(posizioni, valori, left=sinistra, height=0.6, label=etichetta,
                  zorder=2, **layout.riempimento(indice, schermo))
        sinistra += valori
    senza = np.array([v["carte"] - v["testate"] for _, v in righe], dtype=float)
    asse.barh(posizioni, senza, left=sinistra, height=0.6,
              label="scritte, non ancora testate", zorder=2,
              **layout.riempimento(3, schermo))
    passo = 0.012 * max(sinistra.max() + senza.max(), 4.0)
    for posizione, fine, (_, voce) in zip(posizioni, sinistra + senza, righe):
        if voce["concetti"]:
            nota = "concetto" if voce["concetti"] == 1 else "concetti"
            asse.text(fine + passo, posizione, f"+{voce['concetti']} {nota}",
                      fontsize=6.5, va="center", ha="left", style="italic")
    asse.set_yticks(posizioni)
    asse.set_yticklabels([nome for nome, _ in righe], fontsize=8)
    asse.grid(axis="y", visible=False)
    asse.set_ylim(posizioni.min() - 0.65, posizioni.max() + 0.65)


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    per_fonte = _per_fonte(_dati())

    tradizioni = sorted(((k, v) for k, v in per_fonte.items() if k != LA_RICERCA),
                        key=lambda kv: (-kv[1]["carte"], kv[0]))
    ricerca = [(LA_RICERCA, per_fonte[LA_RICERCA])]

    fig, assi = layout.figura("normale", ncols=2,
                              width_ratios=[3.0, 1.6])
    _barre(assi[0], tradizioni, schermo)
    _barre(assi[1], ricerca, schermo)
    assi[0].set_title("le tradizioni, e l'autore", fontsize=8.0)
    assi[1].set_title("la ricerca stessa", fontsize=8.0)
    assi[0].set_xticks(range(0, 5))
    # Il margine a destra tiene dentro il riquadro la nota dei concetti.
    assi[1].set_xlim(0, 80)
    assi[1].set_xticks(range(0, 61, 20))
    fig.supxlabel("affermazioni (i concetti, che non si falsificano, sono segnati a parte)",
                  fontsize=8.5)
    layout.legenda_figura(fig, assi[0], ncols=4, fontsize=7)
    return layout.salva(fig, "bilancio_per_fonte", libro=3, schermo=schermo)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for su_schermo in (False, True):
        print(disegna(schermo=su_schermo))
