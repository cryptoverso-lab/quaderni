"""Genera le figure dei volumi IN INGLESE, dagli stessi dati e dallo stesso codice.

Nessun generatore viene toccato: la resa italiana è chiusa e una traduzione che passasse per i
sorgenti delle figure rischierebbe di cambiarla. Si aggancia il solo punto per cui passa ogni testo
di matplotlib — `Text.set_text` — e lo si fa passare per il dizionario `testi_figure_en.json`.

**Un testo non tradotto è un errore, non un avviso**: una figura inglese con una legenda italiana è
esattamente il difetto per cui questa resa esiste. Lo script elenca i mancanti ed esce con 1.

Le figure inglesi vivono accanto alle italiane, in `figure/libro-N/stampa-en/` e `schermo-en/`: due
cartelle nuove, nessun file italiano sovrascritto.

    .venv\\Scripts\\python.exe codice\\traduzione\\genera_figure_en.py            # tutti
    .venv\\Scripts\\python.exe codice\\traduzione\\genera_figure_en.py libro1     # un volume
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent
RADICE = QUI.parents[1]
GENERATORI = RADICE / "codice" / "figure"
DIZIONARIO = QUI / "testi_figure_en.json"

sys.path.insert(0, str(QUI))
from raccogli_testi_figure import deve_tradursi  # noqa: E402


class Traduttore:
    """Italiano → inglese: prima il testo esatto, poi i modelli, poi la virgola decimale."""

    def __init__(self, dizionario: dict) -> None:
        self.esatti: dict[str, str] = dizionario.get("esatti", {})
        self.modelli = [(re.compile(m), s) for m, s in dizionario.get("modelli", [])]
        self.mancanti: set[str] = set()
        # matplotlib rimette lo stesso testo più volte (la legenda copia l'etichetta già passata
        # di qui): un testo già tradotto passa com'è.
        self.uscite: set[str] = set(self.esatti.values())

    def __call__(self, testo):
        if not isinstance(testo, str) or not testo.strip():
            return testo
        if testo in self.uscite:
            return testo
        fuori = self._traduci(testo)
        self.uscite.add(fuori)
        return fuori

    def _traduci(self, testo: str) -> str:
        if testo in self.esatti:
            # Il testo esatto è scritto in inglese da chi traduce, numeri compresi: non passa
            # dalla conversione dei numeri, che rovescerebbe «3,220» inglese in «3.220».
            return self.esatti[testo]
        else:
            fuori = None
            for modello, sostituto in self.modelli:
                trovato = modello.fullmatch(testo)
                if trovato:
                    # `format` e non `re.sub`: il sostituto porta LaTeX, e le barre rovesce di
                    # `\approx` diventerebbero caratteri di escape.
                    # Un gruppo facoltativo assente vale "", non «None».
                    fuori = sostituto.format(*(g or "" for g in trovato.groups()))
                    break
            if fuori is None:
                if deve_tradursi(testo):
                    self.mancanti.add(testo)
                fuori = testo
        # Il punto delle migliaia italiano («3.206») diventa la virgola inglese, e la virgola
        # decimale italiana fra due cifre diventa il punto: in quest'ordine, passando per un
        # segnaposto, perché le due sostituzioni si scambiano gli stessi caratteri.
        fuori = re.sub(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+)(?![\d.,])",
                       lambda m: m.group(1).replace(".", "\x00"), fuori)
        fuori = re.sub(r"(?<=\d),(?=\d)", ".", fuori)
        return fuori.replace("\x00", ",")


def _genera_uno(generatore: Path, uscita: Path) -> int:
    """Dentro il processo figlio: disegna un generatore in inglese, e dice che cosa manca."""
    import runpy

    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.text import Text

    traduci = Traduttore(json.loads(DIZIONARIO.read_text(encoding="utf-8")))
    originale = Text.set_text
    Text.set_text = lambda self, s: originale(self, traduci(s))  # noqa: E731

    sys.path.insert(0, str(RADICE / "codice" / "src"))
    from acbook import layout

    # Le tacche numeriche col punto inglese: la virgola del libro la mette `layout`, e dentro il
    # mathtext diventerebbe `{,}`, che la regola sulla virgola fra cifre non vede.
    layout.DECIMALE = "."
    scritte: list[str] = []

    def salva(fig, nome, libro, schermo=False, fatti=None):  # noqa: ANN001, ARG001
        import matplotlib.pyplot as plt
        cartella = RADICE / "figure" / f"libro-{libro}" / (
            "schermo-en" if schermo else "stampa-en")
        cartella.mkdir(parents=True, exist_ok=True)
        percorso = cartella / f"{nome}.{'png' if schermo else 'pdf'}"
        fig.savefig(percorso)
        plt.close(fig)
        scritte.append(str(percorso))
        return percorso

    # Il sidecar non si riscrive: serve al presidio delle didascalie ITALIANE, e una copia
    # inglese lo farebbe discordare dal `.qmd` che quel presidio controlla.
    layout.salva = salva
    try:
        runpy.run_path(str(generatore), run_name="__main__")
    except SystemExit:
        pass

    uscita.write_text(json.dumps({"mancanti": sorted(traduci.mancanti), "scritte": scritte},
                                 ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def main(argomenti: list[str]) -> int:
    if not DIZIONARIO.exists():
        print(f"manca il dizionario: {DIZIONARIO}")
        return 1
    prefisso = argomenti[0] if argomenti else ""
    elenco = sorted(p for p in GENERATORI.glob("*.py")
                    if p.name != "tutte_le_figure.py" and p.name.startswith(prefisso))
    interprete = RADICE / ".venv" / "Scripts" / "python.exe"
    if not interprete.exists():
        interprete = Path(sys.executable)

    mancanti: set[str] = set()
    caduti: list[tuple[str, str]] = []
    scritte = 0
    inizio = time.time()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for numero, generatore in enumerate(elenco, 1):
            fuori = Path(tmp) / f"{generatore.stem}.json"
            esito = subprocess.run(
                [str(interprete), str(Path(__file__).resolve()), "--uno",
                 str(generatore), str(fuori)],
                capture_output=True, text=True, cwd=RADICE)
            if esito.returncode != 0 or not fuori.exists():
                coda = (esito.stderr or esito.stdout).strip().splitlines()
                caduti.append((generatore.name, coda[-1] if coda else "senza traccia"))
                stato = "CADUTA"
            else:
                d = json.loads(fuori.read_text(encoding="utf-8"))
                mancanti.update(d["mancanti"])
                scritte += len(d["scritte"])
                stato = f"{len(d['scritte'])} figure" + (
                    f", {len(d['mancanti'])} da tradurre" if d["mancanti"] else "")
            print(f"[{numero:>2}/{len(elenco)}] {generatore.name:<44} {stato}", flush=True)

    print(f"\n{len(elenco) - len(caduti)} su {len(elenco)} generatori, {scritte} figure scritte "
          f"— {time.time() - inizio:.0f} s")
    for nome, traccia in caduti:
        print(f"  caduto {nome}: {traccia}")
    if mancanti:
        (QUI / "mancanti.json").write_text(
            json.dumps(sorted(mancanti), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nTESTI NON TRADOTTI ({len(mancanti)}) — le figure inglesi li porterebbero in "
              f"italiano. Elenco in {QUI / 'mancanti.json'}")
        for t in sorted(mancanti)[:20]:
            print(f"  {t!r}")
        return 1
    return 1 if caduti else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--uno":
        raise SystemExit(_genera_uno(Path(sys.argv[2]), Path(sys.argv[3])))
    raise SystemExit(main(sys.argv[1:]))
