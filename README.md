# Analysis of Cryptocurrency Market Dynamics

This repository contains the source code, data, and report for a Python-based analysis of Bitcoin (BTC) and Ethereum (ETH) market dynamics. The project was completed for a course assignment and is documented in an IEEE-style technical report (`main.tex` / compiled `Project_1.pdf`).

The analysis focuses on three questions:

1. How do price trends evolve across different time horizons for BTC and ETH?
2. How does volatility cluster over time, and how does it compare between BTC and ETH?
3. What correlations exist between BTC and ETH, and how do they behave in high-volatility regimes?

## Repository Structure

```text
.
├── crypto_analysis.py          # Main Python analysis script
├── main.tex                    # LaTeX source for IEEE-style report
├── Project_1.pdf               # Compiled report (optional in repo)
├── Binance_BTCUSDT_d.csv       # Raw BTC/USDT daily OHLCV (from CryptoDataDownload)
├── Binance_ETHUSDT_d.csv       # Raw ETH/USDT daily OHLCV (from CryptoDataDownload)
├── BTC_USD_daily.csv           # Cleaned BTC OHLCV (script output)
├── ETH_USD_daily_clean.csv     # Cleaned ETH OHLCV (script output)
├── btc_eth_rolling_corr.csv    # 90‑day rolling correlation results
├── btc_extreme_events.csv      # Top/bottom 10 BTC daily log‑return events
├── return_summary_stats.csv    # Summary stats for BTC/ETH daily log‑returns
├── btc_candlestick_sma.png     # BTC close with SMA‑50 and SMA‑200
├── normalized_prices.png       # Normalized BTC/ETH prices (index = 100 at start)
├── rolling_volatility.png      # Rolling 30‑day annualized volatility (BTC vs ETH)
├── btc_monthly_volume.png      # Monthly average BTC trading volume
├── btc_return_hist_kde.png     # BTC return distribution vs fitted normal
├── return_correlation_heatmap.jpg  # BTC/ETH return correlation heatmap
└── btc_eth_rolling_corr.png    # 90‑day rolling BTC–ETH correlation
```

## Data

- **Source:** [CryptoDataDownload – Binance Spot Data](https://www.cryptodatadownload.com)  
- **Pairs used:** `BTCUSDT` and `ETHUSDT`, daily frequency.  
- **Fields:** Unix time, date, symbol, open, high, low, close, volume in base asset (e.g. `Volume BTC` / `Volume ETH`), volume in USDT, and trade count.

The raw CSVs from CryptoDataDownload are placed directly in the project root and loaded by `crypto_analysis.py`. The script then produces cleaned BTC/ETH OHLCV files.

## Environment and Requirements

This project was developed with **Python 3** on macOS using a **virtual environment**.

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS / Linux
```

### 2. Install dependencies

```bash
pip install pandas numpy matplotlib scipy
```

## How to Run the Analysis

From the project root:

```bash
source .venv/bin/activate
python3 crypto_analysis.py
```

This will:

- Load BTC and ETH daily OHLCV data from `Binance_BTCUSDT_d.csv` and `Binance_ETHUSDT_d.csv`.
- Compute:
  - Daily log‑returns for BTC and ETH
  - 50‑day and 200‑day simple moving averages (SMA) for BTC
  - Rolling 30‑day annualized volatility for BTC and ETH
  - Summary statistics (mean, median, std, min, max) for daily log‑returns
  - Top/bottom 10 BTC daily log‑return “extreme events”
  - Static BTC/ETH return correlation matrix
  - 90‑day rolling BTC–ETH correlation
- Generate the plots used in the report:
  - BTC price with SMA‑50 and SMA‑200
  - Normalized BTC/ETH price series
  - Rolling 30‑day volatility (BTC vs ETH)
  - BTC monthly average volume
  - BTC return distribution vs fitted normal
  - BTC volatility vs volume scatter
  - BTC/ETH correlation heatmap
  - BTC/ETH 90‑day rolling correlation

Outputs are written as CSVs and images in the project directory (or in the `output/` folder, depending on the script version).


## Key Results (High-Level)

- BTC and ETH exhibit **high volatility** and **heavy‑tailed** return distributions.
- Volatility shows clear **clustering**: periods of high volatility tend to persist.
- BTC and ETH returns are **strongly positively correlated**, especially during market stress, limiting diversification benefits.
- Trading volume for BTC generally **increases during volatile periods**, suggesting a link between market activity and price variability.

## Contact

- **Author:** CHRISTOPHER NTIM  
- **Email:** ntimc@kean.edu 
