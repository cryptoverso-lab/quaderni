# Fonte e licenza dei dati di mercato

*English below.*

## Serie di Binance

I file `BTCUSDT_*`, `ETHUSDT_*`, `SOLUSDT_*` e `BNBUSDT_*` di questa cartella (`.parquet` e
`.csv`, timeframe giornaliero `_D` e a quattro ore `_H4`) sono dati di mercato di **Binance**,
presi dagli archivi pubblici di **Binance Vision** — <https://data.binance.vision> — e
distribuiti con licenza **Creative Commons Attribuzione - Non commerciale - Condividi allo stesso
modo 4.0 Internazionale (CC BY-NC-SA 4.0)**:
<https://creativecommons.org/licenses/by-nc-sa/4.0/deed.it>.

**Come sono stati prodotti.** Dai dump mensili delle *klines* spot (`1d` e `4h`), scaricati da
`data.binance.vision/data/spot/monthly/klines/`, uniti in una sola serie per simbolo, con la barra
datata dall'istante di apertura (la data per il giornaliero, l'istante per le quattro ore), tolte
le barre doppie, tagliate al 15 giugno 2026 e ridotte alle colonne `open`, `high`, `low`,
`close`, `volume`. **I valori non sono modificati**: niente aggiustamenti, riempimenti o
ricampionamenti. Il registro di ogni serie (barre, prima e ultima data, mesi mancanti, impronta
sha256) è in `registro.json` (giornaliero) e `registro-h4.json` (quattro ore).

**Dati derivati.** Le serie sotto `dati/serie/` — i calendari `*_calendario.csv` e i risultati
del motore della ricerca per `BTCUSDT_D`, `ETHUSDT_D`, `SOLUSDT_D` — sono derivate da dati di
mercato di Binance: portano la stessa attribuzione e sono distribuite con la stessa licenza
CC BY-NC-SA 4.0.

## Serie italiane (Yahoo Finance)

I file `ftsemib`, `eni`, `enel`, `intesa`, `generali` e `eurusd` (`.parquet`) sono chiusure
giornaliere di **Yahoo Finance** (ticker `FTSEMIB.MI`, `ENI.MI`, `ENEL.MI`, `ISP.MI`, `G.MI`,
`EURUSD=X`), copiate senza modifiche dallo snapshot di *La matematica di chi perde*
(`registro-serie-italiane.json`). Sono fornite **a solo scopo didattico**, secondo i termini di
servizio di Yahoo; questa pubblicazione non concede su di esse alcuna licenza.

## Che cosa non copre

Queste note riguardano i dati. Il codice ha la sua licenza (il `LICENZA.md` del pacchetto, o il
`LICENSE` della vetrina pubblica). Noi non vendiamo dati: i dati accompagnano la formazione, e
sono quelli pubblici da cui ogni figura e ogni misura si rifanno.

---

# Market data: source and licence

## Binance series

The files `BTCUSDT_*`, `ETHUSDT_*`, `SOLUSDT_*` and `BNBUSDT_*` in this folder (`.parquet` and
`.csv`, daily `_D` and four-hour `_H4`) are **Binance** market data, taken from the public
**Binance Vision** archives — <https://data.binance.vision> — and distributed under the
**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**
licence: <https://creativecommons.org/licenses/by-nc-sa/4.0/>.

**How they were produced.** From the monthly spot *klines* dumps (`1d` and `4h`) downloaded from
`data.binance.vision/data/spot/monthly/klines/`, joined into one series per symbol, each bar keyed
by its opening time (the date for daily bars, the instant for four-hour bars), duplicates removed,
cut at 15 June 2026 and reduced to the `open`, `high`, `low`, `close`, `volume` columns. **Values
are not modified**: no adjustment, filling or resampling. Each series' register (bars, first and
last date, missing months, sha256 fingerprint) is in `registro.json` (daily) and
`registro-h4.json` (four hours).

**Derived data.** The series under `dati/serie/` — the `*_calendario.csv` calendars and the
research engine's results for `BTCUSDT_D`, `ETHUSDT_D`, `SOLUSDT_D` — are derived from Binance
market data: they carry the same attribution and are distributed under the same CC BY-NC-SA 4.0
licence.

## Italian series (Yahoo Finance)

The files `ftsemib`, `eni`, `enel`, `intesa`, `generali` and `eurusd` (`.parquet`) are daily
closes from **Yahoo Finance** (tickers `FTSEMIB.MI`, `ENI.MI`, `ENEL.MI`, `ISP.MI`, `G.MI`,
`EURUSD=X`), copied unchanged from the snapshot of *La matematica di chi perde*
(`registro-serie-italiane.json`). They are provided **for educational purposes only**, under
Yahoo's terms of service; this publication grants no licence over them.

## What this does not cover

These notes are about the data. The code has its own licence (the package's `LICENZA.md`, or the
public showcase's `LICENSE`). We do not sell data: the data come with the teaching, and they are
the public ones from which every figure and measurement can be redone.
