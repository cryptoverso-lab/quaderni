r"""La figura del capitolo 6 del terzo volume — il ritracciamento del ciclo.

Il paragrafo chiede due cose, e la figura risponde a entrambe con lo stesso
materiale congelato.

**A sinistra**: la mediana del ritracciamento, cella per cella, dentro la nube
prodotta dallo stesso rilevatore su serie a fase randomizzata. Se il numero
dicesse qualcosa del mercato, l'osservato uscirebbe dalla nube; sta dentro in
undici celle su quattordici, e le tre che escono stanno **sotto** — i cicli veri
ritracciano un po' meno del rumore, il verso opposto a quello che servirebbe.

**A destra**: la domanda di Fibonacci. Per ciascuno dei sei livelli, quante
celle mostrano un addensamento sopra il novantacinquesimo percentile della
nube. Nessun livello arriva a tre celle su quattordici, e i pochi che compaiono
non sono gli stessi da un contesto all'altro.

I numeri vengono da `dati/misure/ritracciamento.json`.

    uv run python codice/figure/libro3_cap06_ritracciamento.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
SIGLE = {"BTCUSDT": "BTC", "ETHUSDT": "ETH", "SOLUSDT": "SOL"}


def _grado(livello: str) -> int:
    resto = livello[1:].strip()
    return int(resto) if resto else 0


def _valore_fib(chiave: str) -> float:
    """`fib_0618` -> 0,618. La chiave non porta il punto perche' nel file
    congelato un punto sarebbe un altro segmento di percorso."""
    return float(chiave.removeprefix("fib_")) / 1000.0


def _dati() -> dict:
    percorso = RADICE / "dati" / "misure" / "ritracciamento.json"
    return json.loads(percorso.read_text(encoding="utf-8"))


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    dati = _dati()
    righe = sorted(dati["nulla"], key=lambda r: (-_grado(r["livello"]), r["simbolo"]))
    scuro = layout.tinta(0, schermo)
    chiaro = layout.GRIGI[3] if not (schermo or layout.STAMPA_A_COLORI) else "#c9c9c9"

    fig, (sinistra, destra) = layout.figura(
        "alta", ncols=2, gridspec_kw={"width_ratios": [1.9, 1.0], "wspace": 0.30})

    # --- pannello sinistro: l'osservato dentro o fuori la nube ----------------
    posizioni = np.arange(len(righe))[::-1].astype(float)
    for posizione, riga in zip(posizioni, righe):
        sinistra.plot([riga["mediana_p05"], riga["mediana_p95"]], [posizione] * 2,
                      color=chiaro, linewidth=5.0, solid_capstyle="butt", zorder=2)
        sinistra.plot([riga["mediana_nulla"]] * 2,
                      [posizione - 0.28, posizione + 0.28],
                      color="white", linewidth=1.2, zorder=3)

    dentro = [(r["mediana_osservata"], p) for p, r in zip(posizioni, righe)
              if r["mediana_dentro_la_nube"]]
    sotto = [(r["mediana_osservata"], p) for p, r in zip(posizioni, righe)
             if r["mediana_sotto_la_nube"]]
    sinistra.scatter([v for v, _ in dentro], [p for _, p in dentro], s=22, zorder=4,
                     marker="o", facecolor=scuro, edgecolor="white", linewidth=0.6,
                     label="dentro la nube")
    sinistra.scatter([v for v, _ in sotto], [p for _, p in sotto], s=30, zorder=4,
                     marker="D", facecolor="white", edgecolor=scuro, linewidth=1.1,
                     label="sotto la nube")

    sinistra.set_yticks(posizioni)
    sinistra.set_yticklabels(
        [f"{r['livello']} {SIGLE.get(r['simbolo'], r['simbolo'])}" for r in righe],
        fontsize=6.4)
    sinistra.grid(axis="y", visible=False)
    sinistra.set_ylim(posizioni.min() - 0.8, posizioni.max() + 0.8)
    sinistra.set_xlim(0.80, 1.28)
    # La virgola decimale anche sulle tacche: dentro una figura sola non possono
    # convivere «0.9» sull'asse e «0,618» nelle etichette dell'altro pannello.
    sinistra.set_xticks([0.8, 0.9, 1.0, 1.1, 1.2])
    sinistra.set_xticklabels([layout.numero(v, 1) for v in (0.8, 0.9, 1.0, 1.1, 1.2)])
    sinistra.set_xlabel("ritracciamento mediano, in frazione dell'escursione",
                        fontsize=7.6)

    # --- pannello destro: gli addensamenti di Fibonacci -----------------------
    fib = dati["conteggi"]["fibonacci"]
    livelli = sorted(fib, key=_valore_fib)
    celle = [fib[chiave]["celle"] for chiave in livelli]
    sopra = [fib[chiave]["sopra_la_nube"] for chiave in livelli]
    ordinate = np.arange(len(livelli))[::-1].astype(float)

    destra.barh(ordinate, sopra, height=0.62, zorder=2,
                **layout.riempimento(0, schermo))
    destra.set_yticks(ordinate)
    destra.set_yticklabels([layout.numero(_valore_fib(chiave), 3) for chiave in livelli],
                           fontsize=6.8)
    destra.set_xlim(0, max(celle))
    # Ogni quattro, non ogni due: a questa larghezza «10 12 14» si toccavano.
    destra.set_xticks(range(0, max(celle) + 1, 4))
    destra.tick_params(axis="x", labelsize=6.8)
    destra.grid(axis="y", visible=False)
    destra.set_ylim(ordinate.min() - 0.7, ordinate.max() + 0.7)
    destra.set_xlabel(f"celle con addensamento\nsopra la nube (su {celle[0]})",
                      fontsize=7.6)

    for asse in (sinistra, destra):
        layout.cornice(asse)
    layout.legenda_figura(fig, sinistra, ncols=2, fontsize=7)
    # `bbox_inches="tight"` ritaglia sui contenuti: con due pannelli le etichette
    # dell'asse sinistro spingono il PDF un decimo di millimetro oltre la gabbia,
    # e il presidio dell'uscita lo vede. Si nasce un filo piu' stretti.
    fig.set_size_inches(layout.BLOCCO_IN * 0.98, fig.get_size_inches()[1])
    return layout.salva(
        fig, "cap06_ritracciamento", libro=3, schermo=schermo,
        fatti={
            "celle": len(righe),
            "dentro_la_nube": dati["conteggi"]["mediana"]["dentro_la_nube"],
            "sotto_la_nube": dati["conteggi"]["mediana"]["sotto_la_nube"],
            "repliche": dati["repliche"],
            "file": "dati/misure/ritracciamento.json",
        },
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for su_schermo in (False, True):
        print(disegna(schermo=su_schermo))
