"""I fatti di una figura, scritti accanto alla figura.

Nato il 2026-09-15 da quattro difetti che solo **guardare** le figure aveva
trovato (errata §12.414): una didascalia che diceva il contrario del disegno, un
conteggio che nascondeva un livello, un numero rimasto indietro di una rimisura.
I presidi di allora guardavano file e numeri; nessuno guardava se la **frase**
descrivesse il **disegno**.

Qui il disegno si dichiara. Ogni figura, quando viene salvata, scrive accanto a
se' un `<nome>.meta.json` con i fatti che matplotlib gia' conosce — pannelli,
titoli, etichette di legenda, testi, livelli di soglia, quante serie e quanti
punti ciascuna, dove arrivano — piu' i fatti che solo il generatore sa, passati
a `layout.salva(..., fatti={...})`. Il presidio
`codice/testing/test_didascalie_contro_figure.py` confronta quei fatti con la
didascalia del `.qmd`, senza leggere l'immagine e senza NLP.

Il sidecar **non e' una misura**: e' un verbale di cio' che sta nel disegno. Non
sostituisce le misure congelate di `dati/misure/`, che restano la sola fonte dei
numeri stampati.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from matplotlib.markers import MarkerStyle

#: Marker riconosciuti per forma, con il nome che una didascalia userebbe. Il
#: confronto e' sul path canonico del marker: piu' solido del numero di vertici,
#: che confonde quadrato e rombo.
FORME = {
    "o": "tondo", "s": "quadrato", "^": "triangolo", "v": "triangolo",
    "D": "rombo", "d": "rombo", "P": "croce", "X": "ics", "*": "stella",
    "+": "piu'", "x": "ics",
}


def _normale(vertici: np.ndarray) -> np.ndarray:
    """Vertici centrati e scalati: la forma senza la taglia ne' la posizione.

    Serve perche' lo stesso marker ha scale diverse a seconda di come lo si
    chiede — `scatter(marker="o")` lo porta a raggio 0,5 e `MarkerStyle("o")` a
    1 — e il quadrato canonico e' il rettangolo unitario, non centrato.
    """
    vertici = np.asarray(vertici, dtype=float)
    # Centro sul riquadro, non sulla media dei vertici: il vertice di chiusura,
    # ripetuto, sposterebbe il centro e farebbe fallire il confronto.
    mezzo = (vertici.max(axis=0) + vertici.min(axis=0)) / 2
    centrati = vertici - mezzo
    scala = np.abs(centrati).max()
    return centrati / scala if scala else centrati


def _forma(collezione) -> str | None:
    """Il nome della forma di uno scatter, confrontando i path canonici."""
    percorsi = collezione.get_paths()
    if not percorsi:
        return None
    vertici = _normale(percorsi[0].vertices)
    for marker, nome in FORME.items():
        # Il path canonico va TRASFORMATO: la rotazione del rombo sta nella
        # trasformazione del marker, non nei suoi vertici, e senza applicarla
        # un rombo si confronta come un quadrato — cioe' non si riconosce.
        stile = MarkerStyle(marker)
        canonico = _normale(
            stile.get_path().transformed(stile.get_transform()).vertices)
        if canonico.shape == vertici.shape and np.allclose(canonico, vertici, atol=1e-2):
            return nome
    return None


def _forma_di_marker(marker) -> str | None:
    """La forma di un marker chiesto per simbolo — `plot(marker="D")`.

    Le forme non stanno solo negli scatter: meta' delle figure dei volumi le
    disegna con `plot`, e guardare i soli scatter faceva dire al verbale che una
    figura piena di rombi non ne avesse nessuno (15/09/2026).
    """
    if isinstance(marker, str):
        return FORME.get(marker)
    return None


def _forma_di_patch(patch) -> str | None:
    """La forma di una patch disegnata a mano: schemi e riquadri dei modelli."""
    nome = type(patch).__name__
    if nome in ("Rectangle", "FancyBboxPatch"):
        return "quadrato"
    if nome in ("Circle", "Ellipse"):
        return "tondo"
    if nome == "Polygon":
        vertici = len(np.unique(np.round(patch.get_xy(), 6), axis=0))
        return {3: "triangolo", 4: "quadrato"}.get(vertici)
    return None


def _etichetta(artista) -> str | None:
    """L'etichetta di legenda, se e' stata data: matplotlib ne inventa una."""
    testo = artista.get_label()
    if not testo or testo.startswith("_"):
        return None
    return testo


#: Sopra questa taglia una serie e' una curva, e i suoi valori uno per uno non
#: servono a nessuno: bastano gli estremi. Sotto, sono i numeri che la didascalia
#: cita — «il margine piu' stretto vale 0,096» — e cercarli fra i soli estremi
#: faceva dire al verbale che non c'erano.
VALORI_PER_ESTESO = 40


def _limiti(valori) -> dict | None:
    valori = np.asarray(valori, dtype=float)
    valori = valori[np.isfinite(valori)]
    if valori.size == 0:
        return None
    voce = {"minimo": float(valori.min()), "massimo": float(valori.max())}
    if valori.size <= VALORI_PER_ESTESO:
        voce["valori"] = [float(v) for v in valori]
    return voce


def _serie_di_linea(linea) -> dict:
    x = np.asarray(linea.get_xdata(), dtype=float)
    y = np.asarray(linea.get_ydata(), dtype=float)
    voce: dict = {
        "tipo": "linea",
        "etichetta": _etichetta(linea),
        "forma": _forma_di_marker(linea.get_marker()),
        "punti": int(y.size),
        "tratto": linea.get_linestyle(),
        "x": _limiti(x),
        "y": _limiti(y),
    }
    # Una `axhline`/`axvline` e' una linea di due punti costante su un asse: e'
    # la soglia di cui parlano le didascalie, e va nominata come tale.
    if y.size == 2 and np.allclose(y, y[0]):
        voce["livello"] = {"verso": "orizzontale", "valore": float(y[0])}
    elif x.size == 2 and np.allclose(x, x[0]):
        voce["livello"] = {"verso": "verticale", "valore": float(x[0])}
    return voce


def _serie_di_punti(collezione) -> dict:
    scarti = np.asarray(collezione.get_offsets(), dtype=float)
    return {
        "tipo": "punti",
        "etichetta": _etichetta(collezione),
        "forma": _forma(collezione),
        "punti": int(scarti.shape[0]),
        "x": _limiti(scarti[:, 0]) if scarti.size else None,
        "y": _limiti(scarti[:, 1]) if scarti.size else None,
    }


def _serie_di_barre(contenitore) -> dict:
    """Barre verticali e ORIZZONTALI: in `barh` il numero sta nella larghezza.

    Registrare la sola altezza faceva uscire un verbale di zeri per ogni
    pannello a barre orizzontali — e la didascalia che citava il numero della
    barra piu' corta risultava non confermata (15/09/2026).
    """
    altezze = [b.get_height() for b in contenitore.patches]
    larghezze = [b.get_width() for b in contenitore.patches]
    return {
        "tipo": "barre",
        "etichetta": _etichetta(contenitore),
        "punti": len(altezze),
        "y": _limiti(altezze),
        "x": _limiti(larghezze),
    }


def _asse(asse) -> dict:
    serie = [_serie_di_linea(l) for l in asse.lines]
    serie += [_serie_di_punti(c) for c in asse.collections
              if hasattr(c, "get_offsets") and len(c.get_offsets())]
    # Solo i contenitori di barre: un `ErrorbarContainer` non ha `patches`, e
    # chiederglieli faceva cadere due generatori (15/09/2026).
    serie += [_serie_di_barre(c) for c in asse.containers
              if getattr(c, "patches", None)]
    # Le forme disegnate a mano — i riquadri di uno schema, i rombi di un nido —
    # non sono serie ma stanno nel disegno, e una didascalia le nomina.
    forme_disegnate = sorted({f for f in (_forma_di_patch(p) for p in asse.patches) if f})
    legenda = asse.get_legend()
    return {
        "forme_disegnate": forme_disegnate,
        "titolo": asse.get_title() or None,
        "asse_x": asse.get_xlabel() or None,
        "asse_y": asse.get_ylabel() or None,
        "tacche_x": [t.get_text() for t in asse.get_xticklabels() if t.get_text()],
        "tacche_y": [t.get_text() for t in asse.get_yticklabels() if t.get_text()],
        "testi": [t.get_text() for t in asse.texts if t.get_text()],
        "legenda": [t.get_text() for t in legenda.get_texts()] if legenda else [],
        "limiti_x": [float(v) for v in asse.get_xlim()],
        "limiti_y": [float(v) for v in asse.get_ylim()],
        "serie": serie,
    }


def fatti_della_figura(fig, nome: str, libro: int, dichiarati: dict | None = None) -> dict:
    """Il verbale di una figura: che cosa c'e' dentro, misurato sugli artisti."""
    return {
        "figura": nome,
        "libro": libro,
        "generato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pannelli": len(fig.axes),
        "titolo_generale": fig._suptitle.get_text() if fig._suptitle else None,
        "assi": [_asse(a) for a in fig.axes],
        "dichiarati": dichiarati or {},
    }


def scrivi(fig, nome: str, libro: int, radice: Path, dichiarati: dict | None = None) -> Path:
    """Scrive `figure/libro-N/meta/<nome>.meta.json` accanto alla figura."""
    cartella = radice / "figure" / f"libro-{libro}" / "meta"
    cartella.mkdir(parents=True, exist_ok=True)
    percorso = cartella / f"{nome}.meta.json"
    fatti = fatti_della_figura(fig, nome, libro, dichiarati)
    percorso.write_text(json.dumps(fatti, ensure_ascii=False, indent=2), encoding="utf-8")
    return percorso
