"""Il motore dei quaderni: rifa' le figure di un capitolo senza toccare il repository.

Ogni quaderno di `codice/lab/` chiama questo modulo con il codice del suo
capitolo (`"1-05"`). Che cosa appartenga a quel capitolo — quali figure, quali
generatori, quali misure — non e' scritto nel quaderno: sta in
`codice/lab/capitoli.json`, che `codice/lab/costruisci.py --indicizza` ricava dai
capitoli e dall'esecuzione vera dei generatori. Un quaderno scritto a mano che
elencasse le proprie figure diventerebbe falso alla prima figura aggiunta.

**Un quaderno non scrive mai dentro `figure/` ne' dentro `dati/`.** I generatori
salvano con `acbook.layout.salva`, che scrive le figure del libro: qui quella
funzione e' sostituita, per la durata della chiamata, con una che scrive in
`.uscita-quaderni/` — una cartella ignorata da git. Il lettore ottiene la stessa
figura, e il repository resta com'era. La resa di stampa (PDF e sidecar) non si
produce: serve al libro, non a chi verifica.

**L'inglese passa dallo stesso punto della resa inglese dei volumi**
(`codice/traduzione/genera_figure_en.py`): ogni testo disegnato attraversa il
dizionario delle figure, e la virgola decimale torna punto. Un testo che il
dizionario non conosce resta in italiano, e il quaderno lo dice.
"""

from __future__ import annotations

import contextlib
import io
import json
import runpy
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parents[3]
FIGURE = RADICE / "codice" / "figure"
TRADUZIONE = RADICE / "codice" / "traduzione"
CAPITOLI = RADICE / "codice" / "lab" / "capitoli.json"

#: L'unica cartella in cui un quaderno scrive. E' in `.gitignore`.
USCITA = RADICE / ".uscita-quaderni"

_T = {
    "it": {
        "figure": "Figure del capitolo: {n}, da {g} generatori.",
        "nessuna": "Questo capitolo non ha figure: le sue prove sono tavole e misure, sotto.",
        "gen": "  {file:<44} {s:5.1f} s   {nomi}",
        "manca": "ATTENZIONE: il generatore non ha prodotto {nome}.",
        "dal_testo": "Non rigenerabili qui, perche' il generatore legge il testo del volume, "
                     "che non e' pubblico: {nomi}",
        "non_tradotti": "Testi senza traduzione, rimasti in italiano: {elenco}",
        "didascalia": "Figura «{nome}» — volume {libro}, rigenerata da codice/figure/{file}",
    },
    "en": {
        "figure": "Figures of the chapter: {n}, from {g} generators.",
        "nessuna": "This chapter has no figures: its evidence is tables and measurements, below.",
        "gen": "  {file:<44} {s:5.1f} s   {nomi}",
        "manca": "WARNING: the generator did not produce {nome}.",
        "dal_testo": "Not redrawable here, because the generator reads the text of the volume, "
                     "which is not public: {nomi}",
        "non_tradotti": "Texts without a translation, left in Italian: {elenco}",
        "didascalia": "Figure «{nome}» — volume {libro}, redrawn by codice/figure/{file}",
    },
}


class Silenzio(io.StringIO):
    """Raccoglie cio' che uno script stampa. Accetta `reconfigure`, che piu' di
    una misura chiama su `sys.stdout` per forzare l'UTF-8 su Windows."""

    def reconfigure(self, *_a, **_k) -> None:
        return None


def capitoli() -> dict:
    """L'indice dei capitoli, come lo scrive `costruisci.py --indicizza`."""
    return json.loads(CAPITOLI.read_text(encoding="utf-8"))["capitoli"]


def capitolo(codice: str) -> dict:
    tutti = capitoli()
    if codice not in tutti:
        raise KeyError(f"capitolo sconosciuto: {codice!r}")
    return tutti[codice]


@contextlib.contextmanager
def _salvataggio_deviato(cartella: Path, prodotte: dict[str, Path]):
    """`layout.salva` scrive in `cartella` la sola resa schermo, e la registra."""
    import matplotlib.pyplot as plt

    from acbook import layout

    originale = layout.salva

    def salva(fig, nome, libro, schermo=False, fatti=None):  # noqa: ANN001, ARG001
        percorso = cartella / f"libro-{libro}" / f"{nome}.png"
        if schermo:
            percorso.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(percorso)
            prodotte[nome] = percorso
        plt.close(fig)
        return percorso

    layout.salva = salva
    try:
        yield
    finally:
        layout.salva = originale


@contextlib.contextmanager
def _in_inglese(attivo: bool, mancanti: set[str]):
    """Traduce ogni testo disegnato, come la resa inglese dei volumi."""
    if not attivo:
        yield
        return
    from matplotlib.text import Text

    from acbook import layout

    sys.path.insert(0, str(TRADUZIONE))
    from genera_figure_en import DIZIONARIO, Traduttore

    traduci = Traduttore(json.loads(DIZIONARIO.read_text(encoding="utf-8")))
    originale, decimale = Text.set_text, layout.DECIMALE
    Text.set_text = lambda self, s: originale(self, traduci(s))  # noqa: E731
    layout.DECIMALE = "."
    try:
        yield
    finally:
        Text.set_text, layout.DECIMALE = originale, decimale
        mancanti.update(traduci.mancanti)


def esegui_generatore(file: str, lingua: str = "it") -> tuple[dict[str, Path], float, set[str]]:
    """Esegue un generatore come script e ne raccoglie le figure schermo.

    Ritorna le figure prodotte (nome -> PNG), i secondi, e i testi rimasti senza
    traduzione. Il generatore gira nel processo corrente: e' cio' che fa un
    lettore che preme Esegui, ed e' la sola misura di tempo che gli interessa.
    """
    import matplotlib
    matplotlib.use("Agg")

    sys.path.insert(0, str(RADICE / "codice" / "src"))
    sys.path.insert(0, str(FIGURE))
    prodotte: dict[str, Path] = {}
    mancanti: set[str] = set()
    inizio = time.perf_counter()
    with _salvataggio_deviato(USCITA / "figure" / lingua, prodotte), \
            _in_inglese(lingua == "en", mancanti), \
            contextlib.redirect_stdout(Silenzio()):
        try:
            runpy.run_path(str(FIGURE / file), run_name="__main__")
        except SystemExit as uscita:
            if uscita.code not in (None, 0):
                raise
    return prodotte, time.perf_counter() - inizio, mancanti


def figure(codice: str, lingua: str = "it", mostra: bool = True) -> dict[str, Path]:
    """Rifa' e mostra le figure del capitolo. Ritorna nome -> PNG."""
    t = _T[lingua]
    voce = capitolo(codice)
    richieste = voce["figure"]
    if voce.get("figure_dal_testo"):
        print(t["dal_testo"].format(nomi=", ".join(voce["figure_dal_testo"])))
    if not richieste:
        print(t["nessuna"])
        return {}
    generatori = list(dict.fromkeys(f["generatore"] for f in richieste))
    print(t["figure"].format(n=len(richieste), g=len(generatori)))

    tutte: dict[str, Path] = {}
    senza_traduzione: set[str] = set()
    for file in generatori:
        prodotte, secondi, mancanti = esegui_generatore(file, lingua)
        tutte.update(prodotte)
        senza_traduzione |= mancanti
        mie = [f["nome"] for f in richieste if f["generatore"] == file]
        print(t["gen"].format(file=file, s=secondi, nomi=", ".join(mie)))
    if senza_traduzione:
        print(t["non_tradotti"].format(elenco=sorted(senza_traduzione)))

    for f in richieste:
        if f["nome"] not in tutte:
            print(t["manca"].format(nome=f["nome"]))
        elif mostra:
            _mostra(tutte[f["nome"]], t["didascalia"].format(
                nome=f["nome"], libro=f["libro"], file=f["generatore"]))
    return {f["nome"]: tutte[f["nome"]] for f in richieste if f["nome"] in tutte}


def _mostra(png: Path, didascalia: str) -> None:
    """Mostra un PNG nel quaderno; fuori da IPython non fa niente."""
    try:
        from IPython.display import Image, Markdown, display
    except ImportError:
        return
    display(Image(filename=str(png)))
    display(Markdown(f"*{didascalia}*"))
