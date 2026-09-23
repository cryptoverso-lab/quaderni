"""Avvio dei quaderni — il pezzo di codice che sta in cima a ogni lab.

Scopo: fare in modo che la prima cella di un quaderno funzioni sempre, sia su
Colab sia sul computer del lettore, senza che debba installare o configurare
niente.

**I tre livelli (decisione di Luigi, 23/09/2026).** Il codice del libro e' di
chi il libro l'ha comprato: in pubblico, nel repository `cryptoverso-lab/quaderni`,
resta solo una **vetrina** — i quaderni dei capitoli che l'anteprima gratuita
mostra — mentre tutti i ventinove quaderni, il motore e i dati stanno in un
**pacchetto** che l'acquirente scarica con un codice d'accesso personale.
Questo file serve entrambi, ed e' lo stesso file in tutti e due i posti.

Cosa fa `prepara()`, in quest'ordine:

1. **locale** — se gira dentro una cartella che contiene il motore (la
   repository del libro, oppure il pacchetto estratto) non scarica nulla;
2. **pacchetto su Drive** — su Colab, se il pacchetto e' gia' estratto in
   `MyDrive/Cryptoverso/matematica/`, usa quello;
3. **vetrina** — altrimenti scarica motore e serie da `raw.githubusercontent.com`,
   ma solo le serie della vetrina: un quaderno che ne chiede altre fa parte del
   pacchetto, e lo dice invece di morire con un 404.

`scarica_pacchetto()` e' la modalita' PACCHETTO: chiede il codice, scarica lo
zip dal sito, ne verifica ogni file contro il manifesto e lo estrae nel Drive
del lettore (su Colab) o in una cartella locale.

Nessuna chiamata a un'API di mercato, qui o altrove nei quaderni: i dati sono
file fissi, gli stessi identici usati per stampare le figure del libro. E' la
condizione perche' la figura che ottieni sia la figura che stai leggendo.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

#: Radice dei file grezzi della VETRINA. Questo file viene scaricato per primo,
#: quando `cvbook` non c'e' ancora: l'indirizzo va scritto per esteso. Lo tiene
#: allineato a `cvbook.link` il comando `costruisci.py --sincronizza`.
BASE = "https://raw.githubusercontent.com/cryptoverso-lab/quaderni/main/matematica"

#: Il prodotto del sito a cui appartiene il pacchetto, e l'indirizzo che lo
#: consegna: risponde 302 verso un URL firmato che dura pochi minuti.
PRODOTTO = "matematica"
API_PACCHETTO = "https://cryptoverso.net/api/lab/pacchetto"

#: Dove il pacchetto si estrae su Colab: il Drive del lettore, che sopravvive
#: alla sessione. Fuori da Colab si estrae in `./Cryptoverso/matematica`.
DRIVE = Path("/content/drive")
CARTELLA_DRIVE = DRIVE / "MyDrive" / "Cryptoverso" / PRODOTTO

#: I moduli del motore. L'ordine non conta: si scaricano tutti.
#:
#: QUESTO ELENCO NON SI SCRIVE A OCCHIO. Non basta che ci sia cio' che un
#: quaderno importa: serve anche cio' che importano i moduli importati. Il
#: 2026-08-21 `lingua.py` e' nato e non e' entrato qui, e `stile.py` lo importa:
#: risultato, ventisette quaderni su ventinove morivano alla prima cella con
#: `No module named 'cvbook.lingua'` — **in mano al lettore soltanto**. In casa
#: non si vedeva, perche' in casa `cvbook` e' gia' importabile dal repository e
#: nessuno passa da questa lista; e non si vedeva nemmeno in CI, perche' anche
#: la CI esegue i quaderni dentro il checkout. Quattro giorni con ventisette
#: codici QR stampabili che portavano a un errore.
#:
#: Adesso l'elenco e' verificato da `codice/testing/test_avvio.py`, che calcola
#: la chiusura transitiva degli import dei quaderni e fallisce se qui ne manca
#: uno. Se aggiungi un modulo a `cvbook`, non ricordartelo: il gate te lo dice.
#: Lo stesso elenco decide che cosa entra nel pacchetto e nella vetrina.
MODULI = [
    "__init__.py",
    "layout.py",
    "lingua.py",
    "stile.py",
    "dati.py",
    "metriche.py",
    "simulazioni.py",
    "regole.py",
    "ciclica.py",
]

#: I moduli pubblicati nella VETRINA: solo quelli che i quaderni in vetrina
#: raggiungono. Il motore dei backtest (`regole.py`) e della ciclica
#: (`ciclica.py`) sta nel pacchetto. `test_pacchetto.py` ricalcola la chiusura.
MODULI_VETRINA = [
    "__init__.py",
    "layout.py",
    "lingua.py",
    "stile.py",
    "dati.py",
    "metriche.py",
    "simulazioni.py",
]
#: `link.py` stava qui e non ci sta piu': nessun quaderno lo raggiunge. Serve a
#: `costruisci.py` e a `genera_indice.py`, che girano dentro la repository e non
#: passano mai da questo scaricamento. Toglierlo non cambia niente per il
#: lettore se non trenta millisecondi di rete in meno; resta scritto perche' un
#: giorno qualcuno lo rimettera' credendo che manchi.

#: Le serie disponibili. Ogni quaderno chiede solo quelle che gli servono.
#: Le sei non cripto servono ai quaderni che rifanno fuori dalle criptovalute
#: cio' che il libro dimostra dentro.
SERIE = [
    "btcusdt", "ethusdt", "solusdt", "lunausdt", "fttusdt",
    "ftsemib", "eni", "enel", "intesa", "generali", "eurusd",
]

#: Le serie pubblicate nella vetrina: quelle che chiedono i quaderni di vetrina
#: (`cvbook.link`, campo `vetrina`), e nessun'altra. Il gate in
#: `codice/testing/test_pacchetto.py` le ricava dai quaderni e confronta.
SERIE_VETRINA = ["btcusdt", "ethusdt", "solusdt"]


def _ha_il_motore(cartella: Path) -> bool:
    return (cartella / "codice" / "src" / "cvbook" / "dati.py").exists()


def _radice_locale() -> Path | None:
    """La radice della repository o del pacchetto, se il quaderno gira dentro."""
    for cartella in [Path.cwd(), *Path.cwd().parents]:
        if _ha_il_motore(cartella):
            return cartella
    return None


def _in_colab() -> bool:
    return importlib.util.find_spec("google.colab") is not None


def _monta_drive() -> None:
    """Monta il Drive del lettore su Colab; chiede l'autorizzazione una volta."""
    if (DRIVE / "MyDrive").exists():
        return
    from google.colab import drive  # type: ignore[import-not-found]

    drive.mount(str(DRIVE))


def _usa(radice: Path, come: str) -> Path:
    sys.path.insert(0, str(radice / "codice" / "src"))
    print(f"motore {come}: {radice}")
    return radice


def _scarica(percorso_remoto: str, destinazione: Path) -> None:
    if destinazione.exists():
        return
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(f"{BASE}/{percorso_remoto}", destinazione)


def prepara(serie: list[str] | None = None, *, radice: str = ".") -> Path:
    """Prepara l'ambiente e restituisce la radice usata.

    `serie` elenca gli snapshot che il quaderno usa. Ometterlo vuol dire
    tutte e undici, che stanno per intero solo nel pacchetto.
    """
    locale = _radice_locale()
    if locale is not None:
        return _usa(locale, "locale")
    if _ha_il_motore(CARTELLA_DRIVE):
        return _usa(CARTELLA_DRIVE, "dal pacchetto su Drive")

    richieste = list(serie) if serie is not None else list(SERIE)
    for nome in richieste:
        if nome not in SERIE:
            raise ValueError(f"serie sconosciuta: {nome!r} — disponibili {SERIE}")

    fuori = [nome for nome in richieste if nome not in SERIE_VETRINA]
    if fuori:
        if _in_colab():
            _monta_drive()
            if _ha_il_motore(CARTELLA_DRIVE):
                return _usa(CARTELLA_DRIVE, "dal pacchetto su Drive")
        raise RuntimeError(
            "Questo quaderno usa dati del pacchetto riservato a chi ha il libro "
            f"({', '.join(fuori)}).\n"
            "Apri il quaderno di avvio dalla pagina del lab su cryptoverso.net, "
            "inserisci il tuo codice d'accesso e riapri questo quaderno dal tuo Drive.\n"
            "This notebook uses data from the package reserved to book owners: open "
            "the start notebook from the lab page on cryptoverso.net, enter your "
            "access code and reopen this notebook from your Drive."
        )

    base = Path(radice).resolve()
    for modulo in MODULI_VETRINA:
        _scarica(f"codice/src/cvbook/{modulo}", base / "codice" / "src" / "cvbook" / modulo)
    _scarica("codice/dati/registro.json", base / "codice" / "dati" / "registro.json")
    for nome in richieste:
        _scarica(
            f"codice/dati/snapshot/{nome}.parquet",
            base / "codice" / "dati" / "snapshot" / f"{nome}.parquet",
        )

    sys.path.insert(0, str(base / "codice" / "src"))
    print(f"motore e {len(richieste)} serie pronti in {base}")
    return base


def figura(destinazione: str = "schermo"):
    """Contesto grafico del libro. `stampa` per i grigi, `schermo` per i colori."""
    from cvbook.stile import contesto

    return contesto(destinazione)


# --- Modalita' PACCHETTO: il quaderno di avvio dell'acquirente -----------------

#: Che cosa dire al lettore per ogni rifiuto del sito, in tutte e due le lingue:
#: il quaderno di avvio e' lo stesso file per le due edizioni.
RIFIUTI = {
    401: "codice d'accesso non valido o scaduto: generane uno nuovo dalla pagina "
         "del lab su cryptoverso.net / access code invalid or expired: get a new "
         "one from the lab page on cryptoverso.net",
    403: "questo codice non da' accesso al pacchetto: il prodotto non risulta fra "
         "i tuoi acquisti / this code does not grant this package: the product "
         "is not among your purchases",
}


def _sha256(dati: bytes) -> str:
    return hashlib.sha256(dati).hexdigest()


def verifica_pacchetto(zip_path: Path, prodotto: str = PRODOTTO) -> dict:
    """Controlla ogni file dello zip contro `manifesto.json`. Ritorna il manifesto.

    Un file mancante, in piu', troncato o alterato ferma tutto prima che il
    lettore apra un quaderno che non e' quello del libro.
    """
    with zipfile.ZipFile(zip_path) as archivio:
        nomi = {n for n in archivio.namelist() if not n.endswith("/")}
        if "manifesto.json" not in nomi:
            raise ValueError("pacchetto senza manifesto.json: scaricalo di nuovo")
        manifesto = json.loads(archivio.read("manifesto.json").decode("utf-8"))
        if manifesto.get("prodotto") != prodotto:
            raise ValueError(f"pacchetto di un altro prodotto: {manifesto.get('prodotto')!r}")
        attesi = {voce["percorso"]: voce for voce in manifesto["file"]}
        difetti = [f"in piu': {n}" for n in sorted(nomi - set(attesi) - {"manifesto.json"})]
        difetti += [f"mancante: {n}" for n in sorted(set(attesi) - nomi)]
        for nome in sorted(set(attesi) & nomi):
            dati = archivio.read(nome)
            voce = attesi[nome]
            if len(dati) != voce["byte"] or _sha256(dati) != voce["sha256"]:
                difetti.append(f"alterato: {nome}")
    if difetti:
        raise ValueError("il pacchetto non corrisponde al manifesto:\n  " + "\n  ".join(difetti))
    return manifesto


def _scarica_zip(codice: str, api: str, prodotto: str) -> Path:
    """Scarica lo zip seguendo il 302 del sito. Errori tradotti per il lettore.

    Il codice viaggia nell'intestazione `Authorization`, mai nell'indirizzo:
    un indirizzo finisce nei registri dei server e nella cronologia. Ed e' una
    intestazione **non ridiretta**: `urllib`, a differenza di `requests`, copia
    le intestazioni normali sul 302 anche quando cambia host, e il codice
    arriverebbe al bucket che serve l'URL firmato. Il gate in
    `test_pacchetto.py` lo verifica dal lato del bucket.
    """
    indirizzo = f"{api}?{urllib.parse.urlencode({'prodotto': prodotto})}"
    richiesta = urllib.request.Request(indirizzo, headers={"User-Agent": "cryptoverso-avvio/1"})
    richiesta.add_unredirected_header("Authorization", f"Bearer {codice}")
    try:
        with urllib.request.urlopen(richiesta, timeout=120) as risposta:
            fd, nome = tempfile.mkstemp(suffix=".zip")
            with os.fdopen(fd, "wb") as file:
                shutil.copyfileobj(risposta, file)
    except urllib.error.HTTPError as errore:
        if errore.code in RIFIUTI:
            raise PermissionError(f"{errore.code}: {RIFIUTI[errore.code]}") from None
        raise RuntimeError(
            f"il sito ha risposto {errore.code}: riprova fra qualche minuto / "
            "the site answered with an error: try again in a few minutes"
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError) as errore:
        raise ConnectionError(
            f"rete non raggiungibile ({errore}): controlla la connessione e riesegui "
            "la cella / network unreachable: check the connection and rerun the cell"
        ) from None
    return Path(nome)


def _link_colab(percorso: Path) -> str:
    """Su Drive un quaderno si apre dal suo id; altrove resta il percorso."""
    try:
        identificativo = os.getxattr(percorso, "user.drive.id")  # type: ignore[attr-defined]
        return f"https://colab.research.google.com/drive/{identificativo.decode()}"
    except (AttributeError, OSError):
        return str(percorso)


def scarica_pacchetto(codice: str | None = None, *, destinazione: str | Path | None = None,
                      api: str = API_PACCHETTO, prodotto: str = PRODOTTO) -> Path:
    """Scarica, verifica ed estrae il pacchetto dei quaderni. Ritorna la cartella.

    Su Colab estrae nel Drive del lettore, fuori da Colab in
    `./Cryptoverso/<prodotto>`, salvo `destinazione`. Il codice si chiede con
    `getpass`, cosi' non resta scritto nel quaderno salvato.
    """
    if codice is None:
        import getpass

        codice = getpass.getpass("Codice d'accesso / access code: ")
    codice = codice.strip()
    if not codice:
        raise ValueError("nessun codice inserito / no code entered")

    zip_path = _scarica_zip(codice, api, prodotto)
    try:
        manifesto = verifica_pacchetto(zip_path, prodotto)
        if destinazione is None:
            if _in_colab():
                _monta_drive()
                destinazione = CARTELLA_DRIVE
            else:
                destinazione = Path.cwd() / "Cryptoverso" / prodotto
        cartella = Path(destinazione).resolve()
        cartella.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as archivio:
            for nome in archivio.namelist():
                if not (cartella / nome).resolve().is_relative_to(cartella):
                    raise ValueError(f"percorso fuori dalla cartella nel pacchetto: {nome}")
            archivio.extractall(cartella)
    finally:
        zip_path.unlink(missing_ok=True)

    print(f"pacchetto {manifesto['prodotto']} {manifesto['versione']}: "
          f"{len(manifesto['file'])} file verificati, estratti in {cartella}")
    for quaderno in sorted((cartella / "codice" / "lab").glob("*.ipynb")):
        print(f"  {quaderno.stem:34s} {_link_colab(quaderno)}")
    return cartella
