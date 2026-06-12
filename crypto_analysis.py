import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm as stats_norm

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------

ASSETS = ["BTC", "ETH"]
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------------------------------------------------
# Data load and utilities
# --------------------------------------------------------------------

def load_asset_from_csv(symbol: str) -> pd.DataFrame:
    """
    Load daily OHLCV data for a symbol from CryptoDataDownload CSV.

    Expects files like Binance_BTCUSDT_d.csv and Binance_ETHUSDT_d.csv
    in the same folder as this script.

    Handles both 'Unix' and 'Date' timestamp formats and generic
    'Volume XXX' columns (e.g. Volume BTC, Volume ETH, Volume USDT).
    """
    filename = f"Binance_{symbol}USDT_d.csv"
    path = os.path.join(os.path.dirname(__file__), filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"CSV file not found: {path}. "
            f"Download {filename} from CryptoDataDownload and place it here."
        )

    # First row is a header/comment, so skip it (CryptoDataDownload convention)
    df_raw = pd.read_csv(path, skiprows=1)

    # Map columns in a case‑insensitive way
    cols_lower = {c.lower(): c for c in df_raw.columns}

    # ---- time column: unix OR date ----
    if "unix" in cols_lower:
        unix_col = cols_lower["unix"]
        df_raw["time"] = pd.to_datetime(df_raw[unix_col], unit="s")
    elif "date" in cols_lower:
        date_col = cols_lower["date"]
        df_raw["time"] = pd.to_datetime(df_raw[date_col])
    else:
        raise KeyError(
            f"No 'Unix' or 'Date' column found in {filename}. "
            f"Columns are: {list(df_raw.columns)}"
        )

    # ---- OHLC columns ----
    open_col = cols_lower.get("open", "Open")
    high_col = cols_lower.get("high", "High")
    low_col = cols_lower.get("low", "Low")
    close_col = cols_lower.get("close", "Close")

    # ---- Volume columns: first Volume* = crypto volume, second Volume* = USDT volume ----
    volume_cols = [orig for lower, orig in cols_lower.items()
                   if lower.startswith("volume")]
    if len(volume_cols) < 2:
        raise KeyError(
            f"Expected at least two volume columns in {filename}, "
            f"found {volume_cols}. Full columns: {list(df_raw.columns)}"
        )

    vol_crypto_col = volume_cols[0]  # e.g. Volume BTC or Volume ETH
    vol_usdt_col = volume_cols[1]    # e.g. Volume USDT

    df_raw.rename(
        columns={
            open_col: "Open",
            high_col: "High",
            low_col: "Low",
            close_col: "Close",
            vol_crypto_col: "VolumeFrom",
            vol_usdt_col: "VolumeTo",
        },
        inplace=True,
    )

    df = df_raw[["time", "Open", "High", "Low", "Close", "VolumeFrom", "VolumeTo"]]
    df.sort_values("time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def compute_log_returns(price_series: pd.Series) -> pd.Series:
    return np.log(price_series).diff()


def save_summary_stats(df: pd.DataFrame, asset: str, rows: list) -> None:
    ret = compute_log_returns(df["Close"]).dropna()
    rows.append(
        {
            "asset": asset,
            "mean_return": ret.mean(),
            "median_return": ret.median(),
            "std_return": ret.std(),
            "min_return": ret.min(),
            "max_return": ret.max(),
        }
    )


# --------------------------------------------------------------------
# Main analysis
# --------------------------------------------------------------------

def main():
    # --------------------------------------------
    # 1. Load data for all assets
    # --------------------------------------------
    all_dfs: dict[str, pd.DataFrame] = {}
    for sym in ASSETS:
        print(f"Loading data for {sym} from CSV ...")
        df = load_asset_from_csv(sym)
        all_dfs[sym] = df
        # Optional: save cleaned version
        df.to_csv(os.path.join(OUTPUT_DIR, f"{sym}_USD_daily_clean.csv"), index=False)

    # --------------------------------------------
    # 2. Build combined price DataFrame
    # --------------------------------------------
    prices: pd.DataFrame | None = None
    for sym, df in all_dfs.items():
        tmp = df[["time", "Close"]].rename(columns={"Close": sym})
        prices = tmp if prices is None else prices.merge(tmp, on="time", how="inner")

    assert prices is not None, "No price data collected."
    prices.sort_values("time", inplace=True)
    prices.reset_index(drop=True, inplace=True)

    # --------------------------------------------
    # 3. BTC close + SMA-50 and SMA-200 (time index on x-axis)
    # --------------------------------------------
    btc = all_dfs["BTC"].copy()
    btc["SMA50"] = btc["Close"].rolling(window=50).mean()
    btc["SMA200"] = btc["Close"].rolling(window=200).mean()

    fig, ax = plt.subplots(figsize=(10, 5))
    x_idx_btc = np.arange(len(btc))
    ax.plot(x_idx_btc, btc["Close"], label="BTC Close", color="black", linewidth=0.6)
    ax.plot(x_idx_btc, btc["SMA50"], label="SMA 50", color="blue")
    ax.plot(x_idx_btc, btc["SMA200"], label="SMA 200", color="orange")
    ax.set_title("BTC/USD Daily Close with SMA-50 and SMA-200")
    ax.set_xlabel("Time index")
    ax.set_ylabel("Price (USD)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "btc_candlestick_sma.png"), dpi=300)
    plt.close(fig)

    # --------------------------------------------
    # 4. Normalized multi-asset prices (index = 100 at start, time index)
    # --------------------------------------------
    norm = prices.copy().dropna()
    for sym in ASSETS:
        norm[sym] = 100 * norm[sym] / norm[sym].iloc[0]

    fig, ax = plt.subplots(figsize=(10, 5))
    x_idx_norm = np.arange(len(norm))
    for sym in ASSETS:
        ax.plot(x_idx_norm, norm[sym], label=sym)
    ax.set_title("Normalized Daily Prices (Index = 100 at Start)")
    ax.set_xlabel("Time index")
    ax.set_ylabel("Index Level")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "normalized_prices.png"), dpi=300)
    plt.close(fig)

    # --------------------------------------------
    # 5. Log-returns for BTC and ETH and rolling volatility (time index)
    # --------------------------------------------
    prices["BTC_ret"] = compute_log_returns(prices["BTC"])
    prices["ETH_ret"] = compute_log_returns(prices["ETH"])
    rets = prices[["time", "BTC_ret", "ETH_ret"]].dropna().copy()

    rets["BTC_vol30"] = rets["BTC_ret"].rolling(window=30).std() * np.sqrt(365)
    rets["ETH_vol30"] = rets["ETH_ret"].rolling(window=30).std() * np.sqrt(365)

    fig, ax = plt.subplots(figsize=(10, 5))
    x_idx_rets = np.arange(len(rets))
    ax.plot(x_idx_rets, rets["BTC_vol30"], label="BTC 30d vol")
    ax.plot(x_idx_rets, rets["ETH_vol30"], label="ETH 30d vol")
    ax.set_title("Rolling 30-Day Annualized Volatility (BTC vs ETH)")
    ax.set_xlabel("Time index")
    ax.set_ylabel("Volatility")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "rolling_volatility.png"), dpi=300)
    plt.close(fig)

    # --------------------------------------------
    # 6. Correlation matrix of daily log-returns
    # --------------------------------------------
    for sym in ASSETS:
        prices[f"{sym}_ret"] = compute_log_returns(prices[sym])

    corr = prices[[f"{sym}_ret" for sym in ASSETS]].dropna().corr()
    corr.to_csv(os.path.join(OUTPUT_DIR, "return_correlation_matrix.csv"), index=False)

    fig, ax = plt.subplots(figsize=(5, 4))
    cax = ax.matshow(corr, vmin=-1, vmax=1, cmap="RdBu")
    fig.colorbar(cax)
    ax.set_xticks(range(len(ASSETS)))
    ax.set_yticks(range(len(ASSETS)))
    ax.set_xticklabels(ASSETS, rotation=45, ha="left")
    ax.set_yticklabels(ASSETS)
    ax.set_title("Correlation Matrix of Daily Log-Returns", pad=20)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "return_correlation_heatmap.png"), dpi=300)
    plt.close(fig)

    # --------------------------------------------
    # 7. Histogram of BTC daily log-returns with normal fit
    # --------------------------------------------
    btc_rets = rets["BTC_ret"].dropna()
    mu, sigma = btc_rets.mean(), btc_rets.std()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(btc_rets, bins=60, density=True, alpha=0.6, label="Empirical")
    x_vals = np.linspace(btc_rets.min(), btc_rets.max(), 200)
    ax.plot(x_vals, stats_norm.pdf(x_vals, mu, sigma), "r-", label="Normal PDF")
    ax.set_title("BTC Daily Log-Returns vs Fitted Normal")
    ax.set_xlabel("Log-Return")
    ax.set_ylabel("Density")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "btc_return_hist_kde.png"), dpi=300)
    plt.close(fig)

    # --------------------------------------------
    # 8. Monthly average BTC trading volume (VolumeTo in USD, month index)
    # --------------------------------------------
    btc["month"] = btc["time"].dt.to_period("M")
    monthly_vol = (
        btc.groupby("month")["VolumeTo"]
        .mean()
        .reset_index()
    )
    monthly_vol.to_csv(os.path.join(OUTPUT_DIR, "btc_monthly_volume.csv"), index=False)

    fig, ax = plt.subplots(figsize=(10, 4))
    x_idx_month = np.arange(len(monthly_vol))
    ax.bar(x_idx_month, monthly_vol["VolumeTo"])
    ax.set_title("Monthly Average BTC Daily Trading Volume (USD)")
    ax.set_xlabel("Month index")
    ax.set_ylabel("Avg Daily Volume (USD)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "btc_monthly_volume.png"), dpi=300)
    plt.close(fig)

    # --------------------------------------------
    # 9. Scatter: volatility vs volume for BTC
    # --------------------------------------------
    merged = rets.merge(btc[["time", "VolumeTo"]], on="time", how="inner")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.scatter(merged["BTC_vol30"], merged["VolumeTo"], alpha=0.5, s=10)
    ax.set_title("BTC Volatility vs Trading Volume")
    ax.set_xlabel("30d Annualized Volatility")
    ax.set_ylabel("Daily Volume (USD)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "btc_vol_vs_volume.png"), dpi=300)
    plt.close(fig)

    # --------------------------------------------
    # 10. 90-day rolling BTC-ETH correlation (time index)
    # --------------------------------------------
    rets["BTC_ETH_rollcorr90"] = rets["BTC_ret"].rolling(window=90).corr(
        rets["ETH_ret"]
    )
    rets[["time", "BTC_ETH_rollcorr90"]].to_csv(
        os.path.join(OUTPUT_DIR, "btc_eth_rolling_corr.csv"),
        index=False,
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x_idx_rets, rets["BTC_ETH_rollcorr90"])
    ax.set_title("90-Day Rolling Correlation (BTC vs ETH)")
    ax.set_xlabel("Time index")
    ax.set_ylabel("Correlation")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "btc_eth_rolling_corr.png"), dpi=300)
    plt.close(fig)

    # --------------------------------------------
    # 11. Summary stats CSV for BTC and ETH
    # --------------------------------------------
    rows: list[dict] = []
    save_summary_stats(btc, "BTC", rows)
    save_summary_stats(all_dfs["ETH"], "ETH", rows)
    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(os.path.join(OUTPUT_DIR, "return_summary_stats.csv"), index=False)

    # --------------------------------------------
    # 12. Extreme events for BTC (top/bottom 10 daily returns)
    # --------------------------------------------
    btc_ret_full = compute_log_returns(btc["Close"]).dropna()
    btc_events = pd.DataFrame({"time": btc["time"].iloc[1:], "ret": btc_ret_full})
    worst10 = btc_events.nsmallest(10, "ret")
    best10 = btc_events.nlargest(10, "ret")
    extreme = pd.concat(
        [worst10.assign(type="worst"), best10.assign(type="best")]
    ).sort_values("time")
    extreme.to_csv(os.path.join(OUTPUT_DIR, "btc_extreme_events.csv"), index=False)

    print("Analysis complete. Outputs saved in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()