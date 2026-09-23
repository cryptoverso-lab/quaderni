"""Le misure di un capitolo: rifatte e confrontate con l'esito congelato, oppure lette.

Una misura di `codice/verifica/` scrive il proprio esito in `dati/misure/`. Qui la
si esegue con **gli stessi argomenti con cui gira in produzione** — lo script
intero, la sua `main()` — cambiando una cosa sola: il file in cui scrive, che
diventa `.uscita-quaderni/misure/<stesso nome>.json`. Poi il nuovo esito si
confronta, valore per valore, con quello congelato, e il quaderno dice
«coincide» oppure «non coincide», con i numeri che non coincidono.

Due ragioni per cui una misura si **legge** invece di rifarla, e il quaderno le
dice tutte e due quando capitano:

* **e' lenta**: rifarla supererebbe il minuto che un quaderno si concede. Il
  tempo misurato in casa sta in `codice/lab/capitoli.json`, e il comando per
  rifarla resta scritto;
* **non ha uno script in questo deposito**: e' congelata dal motore della
  ricerca, che qui non c'e'. Il dato resta verificabile, non rigenerabile.

Non si confrontano i campi che cambiano a ogni esecuzione senza che la misura
cambi — l'ora e il commit della corsa (`VOLATILI`). Tutto il resto si
confronta, numeri compresi, con una tolleranza relativa di un miliardesimo: la
stessa misura sulla stessa macchina deve dare lo stesso numero.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import math
import time
from pathlib import Path

from acbook.quaderno import RADICE, USCITA, Silenzio, capitolo

VERIFICA = RADICE / "codice" / "verifica"
MISURE = RADICE / "dati" / "misure"

#: Chiavi che registrano il QUANDO di una corsa, non il suo esito.
VOLATILI = {"generato", "generata", "data", "quando", "commit", "eseguito",
            "timestamp", "secondi", "durata_s", "tempo_s", "creato", "aggiornato"}

TOLLERANZA = 1e-9

_T = {
    "it": {
        "nessuna": "Nessuna misura congelata poggia su questo capitolo.",
        "rifaccio": "Rifaccio {script} (in casa: {s:.0f} s) e confronto con dati/misure/{esito}",
        "coincide": "  COINCIDE — {n} valori confrontati, nessuno diverso.",
        "diverge": "  NON COINCIDE — {d} valori diversi su {n}. I primi:",
        "riga": "    {chiave}: congelato {a!r}, rifatto {b!r}",
        "lenta": "Leggo dati/misure/{esito} senza rifarla: {script} impiega {s:.0f} s in casa, "
                 "oltre il minuto del quaderno. Per rifarla: uv run python codice/verifica/{script}",
        "senza": "Leggo dati/misure/{esito}: e' congelata dal motore della ricerca, e in "
                 "questo deposito non ha uno script che la rigeneri.",
        "testo": "Leggo dati/misure/{esito}: la produce {script}, un presidio che legge il testo "
                 "dei volumi, e il testo non e' pubblico.",
        "chiavi": "  contenuto: {chiavi}",
        "fallita": "  LA MISURA NON E' GIRATA: {errore}",
    },
    "en": {
        "nessuna": "No frozen measurement underlies this chapter.",
        "rifaccio": "Re-running {script} ({s:.0f} s at home) and comparing with dati/misure/{esito}",
        "coincide": "  MATCHES — {n} values compared, none different.",
        "diverge": "  DOES NOT MATCH — {d} values differ out of {n}. The first ones:",
        "riga": "    {chiave}: frozen {a!r}, re-run {b!r}",
        "lenta": "Reading dati/misure/{esito} without re-running it: {script} takes {s:.0f} s at "
                 "home, beyond the notebook's minute. To re-run it: uv run python codice/verifica/{script}",
        "senza": "Reading dati/misure/{esito}: it was frozen by the research engine, and this "
                 "repository has no script that regenerates it.",
        "testo": "Reading dati/misure/{esito}: it is produced by {script}, a check that reads "
                 "the text of the volumes, and the text is not public.",
        "chiavi": "  contents: {chiavi}",
        "fallita": "  THE MEASUREMENT DID NOT RUN: {errore}",
    },
}


def rifai(script: str) -> Path:
    """Esegue lo script di misura com'e', deviando solo il file d'esito."""
    nome = f"_verifica_{Path(script).stem}"
    spec = importlib.util.spec_from_file_location(nome, VERIFICA / script)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    uscita = None
    for attributo in ("ESITO", "USCITA"):
        valore = getattr(modulo, attributo, None)
        if isinstance(valore, Path) and valore.parent == MISURE:
            # Dentro RADICE: alcuni script stampano `ESITO.relative_to(RADICE)`.
            uscita = USCITA / "misure" / valore.name
            uscita.parent.mkdir(parents=True, exist_ok=True)
            setattr(modulo, attributo, uscita)
    if uscita is None:
        raise RuntimeError(f"{script}: non trovo il file d'esito da deviare")
    with contextlib.redirect_stdout(Silenzio()):
        try:
            modulo.main()
        except SystemExit:
            pass
    return uscita


def confronta(congelato, rifatto, chiave: str = "") -> tuple[int, list[tuple[str, object, object]]]:
    """(valori confrontati, differenze) fra due alberi JSON, saltando i `VOLATILI`."""
    if isinstance(congelato, dict) and isinstance(rifatto, dict):
        n, diff = 0, []
        for k in sorted(set(congelato) | set(rifatto), key=str):
            if k in VOLATILI:
                continue
            if k not in congelato or k not in rifatto:
                diff.append((f"{chiave}.{k}", congelato.get(k, "<assente>"),
                             rifatto.get(k, "<assente>")))
                n += 1
                continue
            m, d = confronta(congelato[k], rifatto[k], f"{chiave}.{k}")
            n, diff = n + m, diff + d
        return n, diff
    if isinstance(congelato, list) and isinstance(rifatto, list):
        if len(congelato) != len(rifatto):
            return 1, [(f"{chiave}[len]", len(congelato), len(rifatto))]
        n, diff = 0, []
        for i, (a, b) in enumerate(zip(congelato, rifatto)):
            m, d = confronta(a, b, f"{chiave}[{i}]")
            n, diff = n + m, diff + d
        return n, diff
    uguali = congelato == rifatto
    if (isinstance(congelato, (int, float)) and isinstance(rifatto, (int, float))
            and not isinstance(congelato, bool)):
        uguali = math.isclose(congelato, rifatto, rel_tol=TOLLERANZA, abs_tol=1e-12)
    return 1, ([] if uguali else [(chiave or ".", congelato, rifatto)])


def misure(codice: str, lingua: str = "it", mostrate: int = 8) -> dict[str, bool | None]:
    """Rifa' o legge le misure del capitolo. Ritorna esito -> coincide (None = letta)."""
    t = _T[lingua]
    voce = capitolo(codice)
    esiti: dict[str, bool | None] = {}
    if not voce["misure"]:
        print(t["nessuna"])
    for m in voce["misure"]:
        congelato = json.loads((MISURE / m["esito"]).read_text(encoding="utf-8"))
        if m["modo"] == "rifai":
            print(t["rifaccio"].format(script=m["script"], s=m["secondi"], esito=m["esito"]))
            inizio = time.perf_counter()
            try:
                nuovo = json.loads(rifai(m["script"]).read_text(encoding="utf-8"))
            except Exception as errore:  # noqa: BLE001 — si dice, non si nasconde
                print(t["fallita"].format(errore=f"{type(errore).__name__}: {errore}"))
                esiti[m["esito"]] = False
                continue
            n, diff = confronta(congelato, nuovo)
            if diff:
                print(t["diverge"].format(d=len(diff), n=n))
                for k, a, b in diff[:mostrate]:
                    print(t["riga"].format(chiave=k, a=a, b=b))
            else:
                print(t["coincide"].format(n=n))
            print(f"  ({time.perf_counter() - inizio:.1f} s)")
            esiti[m["esito"]] = not diff
        else:
            print(t[m["modo"]].format(esito=m["esito"], script=m.get("script"), s=m.get("secondi") or 0))
            chiavi = list(congelato)[:12] if isinstance(congelato, dict) else [f"{len(congelato)} righe"]
            print(t["chiavi"].format(chiavi=", ".join(map(str, chiavi))))
            esiti[m["esito"]] = None
    return esiti
