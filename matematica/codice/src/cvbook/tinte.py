"""Tinte a schermo: i grigi della stampa diventano i colori del marchio.

I generatori disegnano in grigi, e 41 su 43 li impostano a mano (`color="black"`,
`"#595959"`...): cosi' scavalcano il ciclo di colori del contesto `schermo`, e la
build digitale — quella che si pubblica — usciva in bianco e nero con il solo
testo in indaco. Invece di duplicare in ogni generatore un ramo per lo schermo,
la traduzione avviene qui, una volta, sulla figura finita e prima di salvarla.

La regola segue la gerarchia della stampa, che e' anche quella di lettura: il
grigio piu' scuro e' la serie protagonista e diventa `blu`, il grigio medio la
accompagna e diventa `arancio`, il terzo `notte`, i grigi chiari restano tinte
chiare dello stesso blu. **I riempimenti quasi bianchi restano grigi**: sono le bande di contesto
(periodi difficili, regimi di volatilita'), e a colori il contesto neutro fa
risaltare il dato invece di competere con lui — e il testo che le chiama
«bande grigie» resta vero in tutte e due le edizioni.

Si tocca solo il grigio puro (tre canali uguali): un colore scelto a mano da un
generatore resta com'e'. La stampa passa di qui solo con
`layout.STAMPA_A_COLORI` (acceso dal 28/09/2026: il libro si stampa a colori).
"""

from __future__ import annotations

import numpy as np
from matplotlib.colors import to_rgba

from .stile import BRAND

_BLU_CHIARO = "#7A8CC7"
_BLU_TENUE = "#AEBBE3"
_BLU_VELATO = "#C9D2EE"

#: (grigio fino a, tinta). None = resta com'e'. Per i tratti e' il ciclo del
#: contesto `schermo` messo in fila con `GRIGI`: nero → blu, #595959 → arancio,
#: #8C8C8C → notte, #BFBFBF → blu chiaro. Tre serie in tre grigi restano tre
#: colori distinti.
_SCALA = {
    "tratto": (
        (0.30, BRAND["blu"]),
        (0.50, BRAND["arancio"]),
        (0.66, BRAND["notte"]),
        (0.77, _BLU_CHIARO),
        (0.99, _BLU_TENUE),
    ),
    # Un'area in `notte` sarebbe una macchia nera: i riempimenti medi vanno sul blu chiaro.
    "riempimento": (
        (0.30, BRAND["blu"]),
        (0.50, BRAND["arancio"]),
        (0.66, _BLU_CHIARO),
        (0.84, _BLU_TENUE),
        (0.99, None),
    ),
}


def _tinta(colore, ruolo: str):
    """Il colore a schermo per un grigio, o None se non va toccato."""
    if colore is None or (isinstance(colore, str) and colore in ("none", "face", "edge")):
        return None
    r, g, b, a = to_rgba(colore)
    if a == 0 or max(r, g, b) - min(r, g, b) > 2 / 255:
        return None
    for soglia, nuovo in _SCALA[ruolo]:
        if r < soglia:
            return None if nuovo is None else to_rgba(nuovo, a)
    return None


def _schiera(colori, ruolo: str):
    """Stessa regola su un array Nx4 di colori (le collezioni)."""
    colori = np.asarray(colori, dtype=float)
    if colori.size == 0:
        return None
    nuovi = [_tinta(tuple(c), ruolo) or tuple(c) for c in colori]
    nuovi = np.asarray(nuovi)
    return None if np.array_equal(nuovi, colori) else nuovi


def _linea(ln) -> None:
    for leggi, scrivi in (("get_color", "set_color"),
                          ("get_markerfacecolor", "set_markerfacecolor"),
                          ("get_markeredgecolor", "set_markeredgecolor")):
        nuovo = _tinta(getattr(ln, leggi)(), "tratto")
        if nuovo is not None:
            getattr(ln, scrivi)(nuovo)


def _toppa(p) -> None:
    # Il tratteggio segue il bordo: si legge prima di cambiare il bordo.
    tratteggio = _tinta(p.get_hatchcolor(), "tratto") if p.get_hatch() else None
    faccia = _tinta(p.get_facecolor(), "riempimento")
    bordo = _tinta(p.get_edgecolor(), "tratto")
    if faccia is not None:
        p.set_facecolor(faccia)
    if bordo is not None:
        p.set_edgecolor(bordo)
    if tratteggio is not None:
        p.set_hatchcolor(tratteggio)


def _collezione(c) -> None:
    tratteggio = None
    if c.get_hatch():
        tratteggio = _schiera(np.atleast_2d(c.get_hatchcolor()), "tratto")
    faccia = _schiera(c.get_facecolor(), "riempimento")
    bordo = _schiera(c.get_edgecolor(), "tratto")
    if faccia is not None:
        c.set_facecolor(faccia)
    if bordo is not None:
        c.set_edgecolor(bordo)
    if tratteggio is not None:
        c.set_hatchcolor(tratteggio[0])


def _grigio(colore) -> float | None:
    """Il livello di un grigio puro e visibile (0 nero, 1 bianco), altrimenti None."""
    try:
        r, g, b, a = to_rgba(colore)
    except ValueError:
        return None
    if a == 0 or max(r, g, b) - min(r, g, b) > 2 / 255 or r >= 0.99:
        return None
    return r


def _grigi_dei_dati(ax) -> list[float]:
    """I grigi con cui sono disegnati i dati di un pannello, letti PRIMA di tingerli."""
    grigi = [_grigio(ln.get_color()) for ln in ax.get_lines()]
    for p in ax.patches:
        grigi += [_grigio(p.get_facecolor()), _grigio(p.get_edgecolor())]
    for c in ax.collections:
        for colori in (c.get_facecolor(), c.get_edgecolor()):
            if len(colori):
                grigi.append(_grigio(tuple(colori[0])))
    return sorted({g for g in grigi if g is not None})


def nomina(testo, serie):
    """Dichiara che `testo` e' l'etichetta di `serie` (una linea o una toppa).

    A colori il testo prende la tinta esatta della serie; in grigi resta com'e'. Serve quando
    nel pannello ci sono due o piu' grigi di dati: il grigio piu' vicino, da solo, sbaglia
    appena il testo e' scurito per leggibilita' e un altro segno ha proprio quel grigio
    (revisione del 04/10/2026: «seconda metà» arancio per una curva notte).
    """
    testo._cv_serie = serie
    return testo


def neutro(testo):
    """Dichiara che `testo` non nomina nessuna serie: una nota, che resta nel suo grigio."""
    testo._cv_neutro = True
    return testo


def _colore_di(serie):
    """Il colore che identifica una serie: il tratto di una linea; di una toppa la faccia,
    o il bordo se la faccia e' bianca o trasparente (le barre a retino)."""
    if hasattr(serie, "get_xydata"):
        return serie.get_color()
    faccia = to_rgba(serie.get_facecolor())
    return faccia if faccia[3] > 0 and min(faccia[:3]) < 0.95 else serie.get_edgecolor()


def _testo(tx, grigi_dati: list[float] = ()) -> None:
    # Chi ha dichiarato la serie ne prende la tinta (i dati sono gia' tinti);
    # chi si e' dichiarato neutro resta nel suo grigio.
    serie = getattr(tx, "_cv_serie", None)
    if serie is not None:
        tx.set_color(_colore_di(serie))
    # Un testo in grigio scritto a mano in questo libro e' quasi sempre
    # un'etichetta diretta: in stampa ha il grigio della curva che nomina. A
    # schermo prende il colore della serie dal grigio piu' vicino, cosi'
    # l'accoppiamento regge; senza serie grigie, il nero diventa l'indaco del
    # testo. Mai piu' chiaro del blu chiaro, che e' il limite della leggibilita'.
    dichiarato = serie is not None or getattr(tx, "_cv_neutro", False)
    livello = None if dichiarato else _grigio(tx.get_color())
    if livello is not None:
        if grigi_dati:
            vicino = min(grigi_dati, key=lambda g: abs(g - livello))
            nuovo = _tinta((vicino, vicino, vicino), "tratto")
            if vicino >= 0.77:
                nuovo = to_rgba(_BLU_CHIARO)
            tx.set_color(nuovo)
        elif livello < 0.05:
            tx.set_color(BRAND["notte"])
    freccia = getattr(tx, "arrow_patch", None)
    if freccia is not None:
        _toppa(freccia)


def _artista(a) -> None:
    from matplotlib.collections import Collection
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    if isinstance(a, Line2D):
        _linea(a)
    elif isinstance(a, Patch):
        _toppa(a)
    elif isinstance(a, Collection):
        _collezione(a)


def tingi(fig) -> None:
    """Porta i segni dei dati di `fig` dai grigi della stampa ai colori a schermo."""
    legende = list(fig.legends)
    for ax in fig.get_axes():
        grigi_dati = _grigi_dei_dati(ax)
        for a in (*ax.get_lines(), *ax.patches, *ax.collections):
            _artista(a)
        for tx in ax.texts:
            _testo(tx, grigi_dati)
        if ax.get_legend() is not None:
            legende.append(ax.get_legend())
    for lg in legende:
        for h in getattr(lg, "legend_handles", []) or []:
            if h is not None:
                _artista(h)
    for tx in fig.texts:
        _testo(tx)
