"""Il pacchetto di un volume, dal sito al Drive del lettore: il cuore del quaderno di avvio.

Il codice della collana e' di chi compra (Luigi, 23/09/2026). Chi possiede un
volume riceve dal sito un **codice d'accesso personale che scade**; il quaderno
di avvio, che e' pubblico, lo chiede e chiama questo modulo, che:

1. chiede il pacchetto al sito — `GET <API>?prodotto=<slug>` con il codice
   nell'header `Authorization: Bearer`, **mai nella query string**: un URL finisce
   nei log, nella cronologia, negli screenshot;
2. segue il 302 verso l'URL firmato dello storage **senza reinviargli il codice**.
   `requests` toglie `Authorization` quando il redirect cambia host; il gate
   `codice/testing/test_scarica_pacchetto.py` lo verifica su due server veri,
   perche' e' il genere di garanzia che una libreria puo' cambiare in silenzio;
3. verifica ogni file dello zip contro il `manifest.json` che lo zip porta;
4. lo estrae nel Drive del lettore, in `MyDrive/Cryptoverso/<prodotto>/` (fuori
   da Colab in `./Cryptoverso/<prodotto>/`), e dice dove sono i quaderni.

Gli slug sono quelli del catalogo: `prova`, `resiste`, `meccanismo`.

Contratto del sito: 401 = codice scaduto o non valido; 403 = il codice non apre
quel prodotto. Ogni altro esito si riferisce con il suo stato, senza indovinare.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

API = "https://cryptoverso.net/api/lab/pacchetto"
PRODOTTI = {"prova": "La prova dei cicli", "resiste": "Ciò che resiste",
            "meccanismo": "Il meccanismo"}
DRIVE = Path("/content/drive")
TIMEOUT = 120

_T = {
    "it": {
        "prodotto": "Prodotto sconosciuto: {p!r}. Scegli fra {scelte}.",
        "401": "Il codice d'accesso è scaduto o non è valido. Generane uno nuovo dalla pagina "
               "del volume su cryptoverso.net (serve essere collegati) e riprova.",
        "403": "Questo codice non apre «{titolo}»: vale per un altro volume. Controlla di aver "
               "scelto il volume giusto, o genera il codice dalla pagina di questo volume.",
        "stato": "Il sito ha risposto {s}: riprova fra qualche minuto; se si ripete, scrivi a "
                 "info@cryptoverso.net.",
        "rete": "Non riesco a raggiungere il sito ({e}). Controlla la connessione e riprova.",
        "guasto": "Il pacchetto scaricato non corrisponde al suo manifesto ({n} file): non lo "
                  "installo. Riprova; se si ripete, scrivi a info@cryptoverso.net.",
        "fatto": "«{titolo}», versione {v}: {n} quaderni in {dove}",
        "apri": "Aprili da Colab con File → Apri notebook → Google Drive → Cryptoverso/{p}/",
    },
    "en": {
        "prodotto": "Unknown product: {p!r}. Choose among {scelte}.",
        "401": "The access code has expired or is not valid. Generate a new one from the "
               "volume's page on cryptoverso.net (you need to be signed in) and try again.",
        "403": "This code does not open «{titolo}»: it belongs to another volume. Check that you "
               "chose the right volume, or generate the code from this volume's page.",
        "stato": "The site answered {s}: try again in a few minutes; if it happens again, write "
                 "to info@cryptoverso.net.",
        "rete": "I cannot reach the site ({e}). Check the connection and try again.",
        "guasto": "The downloaded package does not match its manifest ({n} files): I will not "
                  "install it. Try again; if it happens again, write to info@cryptoverso.net.",
        "fatto": "«{titolo}», version {v}: {n} notebooks in {dove}",
        "apri": "Open them from Colab with File → Open notebook → Google Drive → Cryptoverso/{p}/",
    },
}


class ErroreAccesso(RuntimeError):
    """Un esito che il lettore deve leggere: codice, volume, rete o pacchetto."""


def richiedi(prodotto: str, codice: str, lingua: str = "it", api: str = API) -> bytes:
    """Lo zip del prodotto. Solleva `ErroreAccesso` con un messaggio per il lettore."""
    import requests

    t = _T[lingua]
    if prodotto not in PRODOTTI:
        raise ErroreAccesso(t["prodotto"].format(p=prodotto, scelte=", ".join(PRODOTTI)))
    try:
        risposta = requests.get(api, params={"prodotto": prodotto},
                                headers={"Authorization": f"Bearer {codice.strip()}"},
                                timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as errore:
        raise ErroreAccesso(t["rete"].format(e=type(errore).__name__)) from None
    if risposta.status_code in (401, 403):
        raise ErroreAccesso(t[str(risposta.status_code)].format(titolo=PRODOTTI[prodotto]))
    if risposta.status_code != 200:
        raise ErroreAccesso(t["stato"].format(s=risposta.status_code))
    return risposta.content


def verifica(contenuto: bytes) -> dict:
    """Il manifesto dello zip, dopo aver controllato ogni file contro la sua sha256."""
    with zipfile.ZipFile(io.BytesIO(contenuto)) as z:
        manifesto = json.loads(z.read("manifest.json"))
        guasti = [v["percorso"] for v in manifesto["file"]
                  if hashlib.sha256(z.read(v["percorso"])).hexdigest() != v["sha256"]]
    if guasti:
        raise ErroreAccesso(f"{len(guasti)}")
    return manifesto


def destinazione(prodotto: str) -> Path:
    """Il Drive su Colab (montandolo), una cartella accanto al quaderno altrove."""
    if "google.colab" in sys.modules:
        from google.colab import drive

        drive.mount(str(DRIVE))
        return DRIVE / "MyDrive" / "Cryptoverso" / prodotto
    return Path("Cryptoverso").resolve() / prodotto


def installa(prodotto: str, codice: str, lingua: str = "it", api: str = API,
             dove: Path | None = None) -> Path:
    """Scarica, verifica ed estrae il pacchetto; stampa dove sono i quaderni."""
    t = _T[lingua]
    contenuto = richiedi(prodotto, codice, lingua, api)
    try:
        manifesto = verifica(contenuto)
    except ErroreAccesso as guasto:
        raise ErroreAccesso(t["guasto"].format(n=guasto)) from None
    cartella = dove or destinazione(prodotto)
    cartella.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(contenuto)) as z:
        z.extractall(cartella)
    quaderni = [q for q in manifesto["quaderni"]
                if ("/en/" in q) == (lingua == "en")]
    print(t["fatto"].format(titolo=PRODOTTI[prodotto], v=manifesto["versione"],
                            n=len(quaderni), dove=cartella))
    for q in quaderni:
        print(f"  {cartella / q}")
    print(t["apri"].format(p=prodotto))
    return cartella
