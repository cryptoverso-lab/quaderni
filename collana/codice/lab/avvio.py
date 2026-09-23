"""Avvio dei quaderni — il pezzo di codice che sta in cima a ogni quaderno.

Scopo: fare in modo che la prima cella trovi sempre il motore `acbook`, il
codice delle figure e delle misure e i dati congelati, senza che il lettore
debba installare o configurare niente.

**Da dove li prende, in quest'ordine** (il primo che risponde vince):

1. **dal pacchetto o dal repository in cui questo file sta**: `avvio.py` vive in
   `<radice>/codice/lab/`, e se accanto c'e' il motore la radice e' quella. E' il
   caso del pacchetto di un volume estratto nel Drive dal quaderno di avvio, e del
   repository dei volumi — il percorso principale dei test;
2. **dalla cartella di lavoro o da una sua madre** che contenga il motore;
3. **da una BASE remota o locale**: l'argomento `base`, altrimenti la variabile
   d'ambiente `CICLI_BASE`, altrimenti `BASE` qui sotto — la vetrina pubblica.
   La BASE e' una cartella (URL o percorso) con un `manifest.json` che elenca ogni
   file con la sua sha256, oppure uno `.zip` con quel manifesto dentro. Ogni file
   scaricato si verifica contro la sua impronta: un file diverso da quello
   dichiarato ferma l'avvio invece di produrre una figura sbagliata.

Il codice dei volumi non e' pubblico (Luigi, 23/09/2026): la vetrina contiene
solo i capitoli dell'anteprima gratuita. Un quaderno di un altro capitolo, aperto
fuori dal suo pacchetto, si ferma qui e dice come ottenerlo.

Nessuna chiamata a un'API di mercato, qui o altrove nei quaderni: i dati sono
file fissi, gli stessi usati per stampare le figure dei volumi.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

#: La vetrina pubblica. Questo file viene scaricato per primo, quando `acbook`
#: non c'e' ancora: l'indirizzo va scritto per esteso. Lo tiene allineato ad
#: `acbook.link.BASE_VETRINA` il comando `costruisci.py --sincronizza`.
BASE = "https://raw.githubusercontent.com/cryptoverso-lab/quaderni/main/collana"

#: Dove il quaderno di avvio mette i pacchetti nel Drive del lettore.
DRIVE = Path("/content/drive/MyDrive/Cryptoverso")

#: Il file che dice «qui c'e' il motore dei quaderni».
_SEGNO = Path("codice") / "src" / "acbook" / "quaderno.py"

#: Moduli che Colab non ha preinstallati e che qualche misura importa.
DA_INSTALLARE = {"diptest": "diptest"}


class NonDisponibile(RuntimeError):
    """Il capitolo chiesto non e' in nessuna sorgente raggiungibile."""


def _e_radice(cartella: Path) -> bool:
    return (cartella / _SEGNO).exists()


def _radice_locale(prodotto: str | None = None) -> Path | None:
    qui = Path(__file__).resolve()
    candidati = [qui.parents[2]] if len(qui.parents) > 2 else []
    candidati += [Path.cwd(), *Path.cwd().parents]
    if prodotto:
        candidati.append(DRIVE / prodotto)
    return next((c for c in candidati if _e_radice(c)), None)


def _leggi(sorgente: str) -> bytes:
    if sorgente.startswith(("http://", "https://", "file:")):
        with urllib.request.urlopen(sorgente, timeout=120) as risposta:
            return risposta.read()
    return Path(sorgente).read_bytes()


def verifica_manifesto(radice: Path) -> list[str]:
    """I file di `radice` che non corrispondono al suo `manifest.json`."""
    manifesto = json.loads((radice / "manifest.json").read_text(encoding="utf-8"))
    fuori = []
    for voce in manifesto["file"]:
        percorso = radice / voce["percorso"]
        if not percorso.exists():
            fuori.append(f"manca {voce['percorso']}")
        elif hashlib.sha256(percorso.read_bytes()).hexdigest() != voce["sha256"]:
            fuori.append(f"impronta diversa: {voce['percorso']}")
    return fuori


def _da_zip(contenuto: bytes, destinazione: Path) -> Path:
    with zipfile.ZipFile(io.BytesIO(contenuto)) as archivio:
        archivio.extractall(destinazione)
    return destinazione


def _da_cartella(base: str, destinazione: Path) -> Path:
    """Scarica i file del manifesto di una cartella remota, verificandoli uno a uno."""
    grezzo = _leggi(f"{base.rstrip('/')}/manifest.json")
    manifesto = json.loads(grezzo)
    for voce in manifesto["file"]:
        percorso = destinazione / voce["percorso"]
        if percorso.exists() and hashlib.sha256(percorso.read_bytes()).hexdigest() == voce["sha256"]:
            continue
        dati = _leggi(f"{base.rstrip('/')}/{voce['percorso']}")
        if hashlib.sha256(dati).hexdigest() != voce["sha256"]:
            raise RuntimeError(f"{voce['percorso']}: il file scaricato non e' quello dichiarato")
        percorso.parent.mkdir(parents=True, exist_ok=True)
        percorso.write_bytes(dati)
    (destinazione / "manifest.json").write_bytes(grezzo)
    return destinazione


def _installa_mancanti() -> None:
    import importlib.util
    import subprocess

    mancanti = [p for m, p in DA_INSTALLARE.items() if importlib.util.find_spec(m) is None]
    if mancanti:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", *mancanti], check=False)


def prepara(capitolo: str | None = None, prodotto: str | None = None,
            base: str | None = None, radice: str = ".") -> Path:
    """Trova (o scarica) codice e dati, e restituisce la radice usata."""
    locale = _radice_locale(prodotto)
    if locale is None:
        sorgente = base or os.environ.get("CICLI_BASE") or BASE
        destinazione = Path(radice).resolve() / "cicli"
        if _e_radice(destinazione) and not verifica_manifesto(destinazione):
            locale = destinazione
        elif sorgente.lower().endswith(".zip"):
            locale = _da_zip(_leggi(sorgente), destinazione)
        else:
            locale = _da_cartella(sorgente, destinazione)
        guasti = verifica_manifesto(locale)
        if guasti:
            raise RuntimeError("il pacchetto non corrisponde al suo manifesto: " + "; ".join(guasti[:5]))
        _installa_mancanti()
        print(f"codice e dati da {sorgente}")
    sys.path.insert(0, str(locale / "codice" / "src"))
    print(f"motore pronto in {locale}")
    if capitolo is not None:
        indice = json.loads((locale / "codice" / "lab" / "capitoli.json").read_text(encoding="utf-8"))
        if capitolo not in indice["capitoli"]:
            raise NonDisponibile(
                f"Il quaderno del capitolo {capitolo} e' riservato a chi possiede il volume. "
                "Apri il quaderno di avvio della collana dalla pagina del capitolo su "
                "cryptoverso.net, inserisci il tuo codice d'accesso e riapri questo quaderno "
                "dal tuo Drive. / This chapter's notebook is for owners of the volume: open the "
                "series' setup notebook from the chapter page on cryptoverso.net, enter your "
                "access code and reopen this notebook from your Drive.")
    return locale
