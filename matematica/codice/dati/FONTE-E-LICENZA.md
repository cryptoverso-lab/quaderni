# Fonte e licenza dei dati di mercato

*English below.*

## Serie di Binance

`btcusdt`, `ethusdt`, `solusdt`, `lunausdt` e `fttusdt` (in `snapshot/`, `.parquet`) sono dati di
mercato di **Binance**, presi dagli archivi pubblici di **Binance Vision** —
<https://data.binance.vision> — e distribuiti con licenza **Creative Commons Attribuzione - Non
commerciale - Condividi allo stesso modo 4.0 Internazionale (CC BY-NC-SA 4.0)**:
<https://creativecommons.org/licenses/by-nc-sa/4.0/deed.it>.

**Come sono stati prodotti** (`codice/ingest/binance_dump.py`): dai dump mensili delle *klines*
spot giornaliere (`1d`) di `data.binance.vision/data/spot/monthly/klines/`, uniti in una sola serie
per simbolo, con la barra datata dal giorno di apertura, tolte le barre doppie e ridotte alle
colonne `apertura`, `massimo`, `minimo`, `chiusura`, `volume`, `scambi` (le colonne originali
`open`, `high`, `low`, `close`, `volume`, `number of trades`, rinominate). **I valori non sono
modificati.** Periodo, righe e impronta sha256 di ogni serie sono in `registro.json`.

## Serie di Yahoo Finance

`ftsemib`, `eni`, `enel`, `intesa`, `generali` e `eurusd` sono dati giornalieri di **Yahoo
Finance** (ticker `FTSEMIB.MI`, `ENI.MI`, `ENEL.MI`, `ISP.MI`, `G.MI`, `EURUSD=X`), scaricati con
`yfinance` a prezzi **aggiustati** per dividendi e frazionamenti (`codice/ingest/yahoo_dump.py`),
con le colonne rinominate in italiano; ticker, periodo e impronta sono in `registro.json`. Sono
forniti **a solo scopo didattico**, secondo i termini di servizio di Yahoo; questa pubblicazione non
concede su di essi alcuna licenza.

## Che cosa non copre

Queste note riguardano i dati. Il codice ha la sua licenza (il `LICENZA.md` del pacchetto, o il
`LICENSE` della vetrina pubblica). Noi non vendiamo dati: i dati accompagnano la formazione.

---

# Market data: source and licence

## Binance series

`btcusdt`, `ethusdt`, `solusdt`, `lunausdt` and `fttusdt` (in `snapshot/`, `.parquet`) are
**Binance** market data, taken from the public **Binance Vision** archives —
<https://data.binance.vision> — and distributed under the **Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)** licence:
<https://creativecommons.org/licenses/by-nc-sa/4.0/>.

**How they were produced** (`codice/ingest/binance_dump.py`): from the monthly daily spot *klines*
dumps (`1d`) at `data.binance.vision/data/spot/monthly/klines/`, joined into one series per
symbol, each bar dated by its opening day, duplicates removed and reduced to the columns
`apertura`, `massimo`, `minimo`, `chiusura`, `volume`, `scambi` (the original `open`, `high`, `low`,
`close`, `volume`, `number of trades`, renamed). **Values are not modified.** Period, rows and
sha256 fingerprint of each series are in `registro.json`.

## Yahoo Finance series

`ftsemib`, `eni`, `enel`, `intesa`, `generali` and `eurusd` are daily data from **Yahoo Finance**
(tickers `FTSEMIB.MI`, `ENI.MI`, `ENEL.MI`, `ISP.MI`, `G.MI`, `EURUSD=X`), downloaded with
`yfinance` at prices **adjusted** for dividends and splits (`codice/ingest/yahoo_dump.py`), with the
columns renamed in Italian; ticker, period and fingerprint are in `registro.json`. They are provided
**for educational purposes only**, under Yahoo's terms of service; this publication grants no
licence over them.

## What this does not cover

These notes are about the data. The code has its own licence (the package's `LICENZA.md`, or the
public showcase's `LICENSE`). We do not sell data: the data come with the teaching.
