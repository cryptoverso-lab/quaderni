"""Raccoglie i testi che le figure dei tre volumi disegnano, per sapere che cosa costa l'inglese.

Non tocca nessuna figura e non tocca nessun generatore: aggancia il solo punto per cui passa ogni
stringa di matplotlib — `Text.set_text` — e devia `acbook.layout.salva` in una cartella
temporanea, cosi' `figure/libro-N/` resta esattamente com'e'.

E' il primo passo dell'edizione inglese, ed e' anche la sua **misura di costo**: quante stringhe
vanno tradotte, e quali sono neutre (sigle, simboli, timeframe) perche' si leggono uguali nelle due
lingue. Stesso meccanismo gia' in produzione per il paper SIAT
(`docs/SIAT AWARDS/v3/en/codice/genera_figure_en.py` nel repo CyclicalResearch), qui portato sui
libri, dove i generatori sono 72 e vivono ognuno nel proprio processo.

    .venv\\Scripts\\python.exe codice\\traduzione\\raccogli_testi_figure.py
    .venv\\Scripts\\python.exe codice\\traduzione\\raccogli_testi_figure.py libro1
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent
RADICE = QUI.parents[1]
GENERATORI = RADICE / "codice" / "figure"
USCITA = QUI / "testi_delle_figure.json"

#: Una lettera fuori da questi gettoni vuol dire che il testo e' lingua, e va tradotto. Sono
#: simboli, livelli, righelli e sigle che in inglese si leggono identici. Ereditato dal paper e
#: allargato ai gettoni dei libri (`AAFT`, le carte `CR-nnn`, i livelli `T+n`).
NEUTRI = re.compile(
    r"\^?[A-Z]{3,6}USDT?|\^[A-Z]{3,5}|BTC|ETH|SOL|AAFT|CR-\d+|LG-\d+|HU-\d+"
    r"|T\s*[+−-]\s*\d+|\b[MHDW]\d{0,2}\b|\bT\b|\b[npqkNrR]\b|\bA\d\b|\bx\b"
    r"|\$[^$]*\$|\blog\b|\bDSP\b|\bMESA\b|\bFLD\b|\bVTL\b|\bSNR\b|\bdB\b")


def deve_tradursi(testo: str) -> bool:
    """`True` se, tolti i gettoni neutri, resta della lingua."""
    return bool(re.search(r"[A-Za-zÀ-ÿ]", NEUTRI.sub("", testo)))


# --------------------------------------------------------------------------- figlio


def _raccogli_uno(generatore: Path, uscita: Path) -> int:
    """Gira dentro il processo figlio: esegue un generatore e scrive i testi che ha disegnato."""
    import runpy

    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.text import Text

    visti: dict[str, int] = {}
    originale = Text.set_text

    def set_text(self, s):
        if isinstance(s, str) and s.strip():
            visti[s] = visti.get(s, 0) + 1
        return originale(self, s)

    Text.set_text = set_text

    sys.path.insert(0, str(RADICE / "codice" / "src"))
    from acbook import layout

    with tempfile.TemporaryDirectory() as cartella:
        def salva(fig, nome, libro, schermo=False, fatti=None):  # noqa: ANN001, ARG001
            percorso = Path(cartella) / f"{nome}-{libro}-{int(schermo)}.png"
            fig.savefig(percorso)
            import matplotlib.pyplot as plt
            plt.close(fig)
            return percorso

        layout.salva = salva
        try:
            runpy.run_path(str(generatore), run_name="__main__")
        except SystemExit:
            pass

    uscita.write_text(json.dumps(visti, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


# --------------------------------------------------------------------------- padre


def _generatori(prefisso: str) -> list[Path]:
    return sorted(p for p in GENERATORI.glob("*.py")
                  if p.name != "tutte_le_figure.py" and p.name.startswith(prefisso))


def _interprete() -> Path:
    candidato = RADICE / ".venv" / "Scripts" / "python.exe"
    return candidato if candidato.exists() else Path(sys.executable)


def main(argomenti: list[str]) -> int:
    prefisso = argomenti[0] if argomenti else ""
    elenco = _generatori(prefisso)
    if not elenco:
        print(f"nessun generatore con prefisso {prefisso!r}")
        return 1

    visti: dict[str, int] = {}
    per_libro: dict[str, set[str]] = {}
    caduti: list[tuple[str, str]] = []
    inizio = time.time()

    with tempfile.TemporaryDirectory() as tmp:
        for numero, generatore in enumerate(elenco, 1):
            fuori = Path(tmp) / f"{generatore.stem}.json"
            esito = subprocess.run(
                [str(_interprete()), str(Path(__file__).resolve()), "--uno",
                 str(generatore), str(fuori)],
                capture_output=True, text=True, cwd=RADICE)
            if esito.returncode != 0 or not fuori.exists():
                coda = (esito.stderr or esito.stdout).strip().splitlines()
                caduti.append((generatore.name, coda[-1] if coda else "senza traccia"))
                stato = "CADUTA"
            else:
                testi = json.loads(fuori.read_text(encoding="utf-8"))
                for t, n in testi.items():
                    visti[t] = visti.get(t, 0) + n
                libro = generatore.name.split("_")[0]
                per_libro.setdefault(libro, set()).update(
                    t for t in testi if deve_tradursi(t))
                stato = f"{len(testi):>3} testi"
            print(f"[{numero:>2}/{len(elenco)}] {generatore.name:<44} {stato}", flush=True)

    da_tradurre = sorted(t for t in visti if deve_tradursi(t))
    USCITA.write_text(json.dumps({
        "quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "generatori": len(elenco), "caduti": [n for n, _ in caduti],
        "testi_distinti": len(visti), "da_tradurre": len(da_tradurre),
        "per_libro": {k: len(v) for k, v in sorted(per_libro.items())},
        "elenco_da_tradurre": da_tradurre,
        "neutri": sorted(set(visti) - set(da_tradurre)),
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{len(elenco) - len(caduti)} su {len(elenco)} generatori — "
          f"{time.time() - inizio:.0f} s")
    print(f"testi distinti {len(visti)}, DA TRADURRE {len(da_tradurre)} "
          f"({', '.join(f'{k}: {len(v)}' for k, v in sorted(per_libro.items()))})")
    for nome, traccia in caduti:
        print(f"  caduto {nome}: {traccia}")
    print(f"-> {USCITA}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--uno":
        raise SystemExit(_raccogli_uno(Path(sys.argv[2]), Path(sys.argv[3])))
    raise SystemExit(main(sys.argv[1:]))
