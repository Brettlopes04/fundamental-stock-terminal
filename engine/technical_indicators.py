# Technical Indicators & Chart Validation Engine
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def validate_and_sort_series(data_points: List[Any]) -> List[Tuple[str, float]]:
    """
    Validates, deduplicates, and sorts a time series of [date_str, value].
    Filters out invalid dates, negative/zero prices, non-numeric values.
    Returns ascending chronological list of (iso_date_str, float_value).
    """
    valid_points = []
    seen_dates = set()

    for item in data_points:
        if not item or len(item) < 2:
            continue
        date_raw = str(item[0]).strip()
        val_raw = item[1]

        if val_raw is None:
            continue
        try:
            val = float(val_raw)
            if val < 0: # Price cannot be negative
                continue
        except (ValueError, TypeError):
            continue

        # Standardize date to YYYY-MM-DD
        clean_date = date_raw[:10]
        if not DATE_REGEX.match(clean_date):
            continue

        if clean_date in seen_dates:
            continue
        seen_dates.add(clean_date)
        valid_points.append((clean_date, val))

    # Sort chronologically
    valid_points.sort(key=lambda x: x[0])
    return valid_points

def compute_sma(prices: List[float], period: int) -> List[Optional[float]]:
    """Computes Simple Moving Average for a given period."""
    sma: List[Optional[float]] = []
    if period <= 0 or not prices:
        return [None] * len(prices)

    rolling_sum = 0.0
    for i, p in enumerate(prices):
        rolling_sum += p
        if i >= period:
            rolling_sum -= prices[i - period]
        if i >= period - 1:
            sma.append(round(rolling_sum / period, 2))
        else:
            sma.append(None)
    return sma

def compute_ema(prices: List[float], period: int) -> List[Optional[float]]:
    """Computes Exponential Moving Average with smoothing multiplier 2 / (period + 1)."""
    ema: List[Optional[float]] = []
    n = len(prices)
    if period <= 0 or n < period:
        return [None] * n

    multiplier = 2.0 / (period + 1.0)
    # First EMA value is SMA of the first period
    initial_sma = sum(prices[:period]) / period
    for _ in range(period - 1):
        ema.append(None)
    ema.append(round(initial_sma, 2))

    current_ema = initial_sma
    for i in range(period, n):
        current_ema = (prices[i] - current_ema) * multiplier + current_ema
        ema.append(round(current_ema, 2))
    return ema

def compute_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """Computes Relative Strength Index (Wilder's RSI formula)."""
    n = len(prices)
    rsi: List[Optional[float]] = [None] * n
    if n <= period or period <= 0:
        return rsi

    gains = []
    losses = []
    for i in range(1, n):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(diff))

    if len(gains) < period:
        return rsi

    # Initial average gain/loss
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        rsi[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi[period] = round(100.0 - (100.0 / (1.0 + rs)), 2)

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            cur_rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            cur_rsi = round(100.0 - (100.0 / (1.0 + rs)), 2)
        rsi[i + 1] = cur_rsi

    return rsi

def compute_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[Optional[float]]]:
    """
    Computes Moving Average Convergence Divergence (MACD).
    Returns dict with macd_line, signal_line, histogram.
    """
    n = len(prices)
    empty_res = {
        'macd_line': [None] * n,
        'signal_line': [None] * n,
        'histogram': [None] * n
    }
    if n < slow:
        return empty_res

    ema_fast = compute_ema(prices, fast)
    ema_slow = compute_ema(prices, slow)

    macd_line: List[Optional[float]] = []
    valid_macd_indices = []
    valid_macd_values = []

    for i in range(n):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            val = round(ema_fast[i] - ema_slow[i], 2)
            macd_line.append(val)
            valid_macd_indices.append(i)
            valid_macd_values.append(val)
        else:
            macd_line.append(None)

    signal_line: List[Optional[float]] = [None] * n
    histogram: List[Optional[float]] = [None] * n

    if len(valid_macd_values) >= signal:
        signal_sub = compute_ema(valid_macd_values, signal)
        for sub_i, orig_i in enumerate(valid_macd_indices):
            sig_val = signal_sub[sub_i]
            signal_line[orig_i] = sig_val
            if sig_val is not None and macd_line[orig_i] is not None:
                histogram[orig_i] = round(macd_line[orig_i] - sig_val, 2)

    return {
        'macd_line': macd_line,
        'signal_line': signal_line,
        'histogram': histogram
    }

def process_technical_indicators(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes raw Screener chart data, validates and calculates:
    - SMA 20, 50, 100, 200
    - EMA 20, 50
    - RSI 14
    - MACD (12, 26, 9)
    - Technical summary and trend signals
    """
    if not chart_data or not isinstance(chart_data, dict):
        return {"datasets": [], "technical_summary": {}, "dates": []}

    datasets = chart_data.get("datasets", [])
    price_dataset = None
    volume_dataset = None

    for ds in datasets:
        metric = ds.get("metric", "")
        if metric == "Price":
            price_dataset = ds
        elif metric == "Volume":
            volume_dataset = ds

    if not price_dataset or not price_dataset.get("values"):
        return chart_data

    # Clean and sort price points
    clean_series = validate_and_sort_series(price_dataset.get("values", []))
    if not clean_series:
        return chart_data

    dates = [p[0] for p in clean_series]
    prices = [p[1] for p in clean_series]

    # Calculate indicators
    sma_20 = compute_sma(prices, 20)
    sma_50 = compute_sma(prices, 50)
    sma_100 = compute_sma(prices, 100)
    sma_200 = compute_sma(prices, 200)

    ema_20 = compute_ema(prices, 20)
    ema_50 = compute_ema(prices, 50)

    rsi_14 = compute_rsi(prices, 14)
    macd = compute_macd(prices, 12, 26, 9)

    # Clean volume aligned with dates
    vol_dict = {}
    if volume_dataset and volume_dataset.get("values"):
        clean_vols = validate_and_sort_series(volume_dataset.get("values", []))
        vol_dict = {v[0]: v[1] for v in clean_vols}

    aligned_vols = [vol_dict.get(d, 0.0) for d in dates]

    # Build technical datasets for Chart.js
    def to_val_pairs(vals):
        return [[dates[i], vals[i]] for i in range(len(dates)) if vals[i] is not None]

    computed_datasets = [
        {
            "metric": "Price",
            "label": "Closing Price (₹)",
            "values": [[dates[i], prices[i]] for i in range(len(dates))],
            "color": "#3b82f6",
            "type": "line",
            "yAxisID": "y"
        },
        {
            "metric": "SMA20",
            "label": "20 SMA (Short Term)",
            "values": to_val_pairs(sma_20),
            "color": "#ec4899",
            "type": "line",
            "yAxisID": "y",
            "hidden": True
        },
        {
            "metric": "SMA50",
            "label": "50 SMA (Medium Term)",
            "values": to_val_pairs(sma_50),
            "color": "#10b981",
            "type": "line",
            "yAxisID": "y",
            "hidden": False
        },
        {
            "metric": "SMA100",
            "label": "100 SMA",
            "values": to_val_pairs(sma_100),
            "color": "#f59e0b",
            "type": "line",
            "yAxisID": "y",
            "hidden": True
        },
        {
            "metric": "SMA200",
            "label": "200 SMA (Long Term Baseline)",
            "values": to_val_pairs(sma_200),
            "color": "#ef4444",
            "type": "line",
            "yAxisID": "y",
            "hidden": False
        },
        {
            "metric": "EMA20",
            "label": "20 EMA",
            "values": to_val_pairs(ema_20),
            "color": "#8b5cf6",
            "type": "line",
            "yAxisID": "y",
            "hidden": True
        },
        {
            "metric": "EMA50",
            "label": "50 EMA",
            "values": to_val_pairs(ema_50),
            "color": "#06b6d4",
            "type": "line",
            "yAxisID": "y",
            "hidden": True
        },
        {
            "metric": "Volume",
            "label": "Volume",
            "values": [[dates[i], aligned_vols[i]] for i in range(len(dates))],
            "color": "rgba(148, 163, 184, 0.25)",
            "type": "bar",
            "yAxisID": "yVolume",
            "hidden": False
        }
    ]

    # Last values for dashboard summary
    last_price = prices[-1] if prices else 0.0
    last_sma20 = next((x for x in reversed(sma_20) if x is not None), None)
    last_sma50 = next((x for x in reversed(sma_50) if x is not None), None)
    last_sma100 = next((x for x in reversed(sma_100) if x is not None), None)
    last_sma200 = next((x for x in reversed(sma_200) if x is not None), None)
    last_ema20 = next((x for x in reversed(ema_20) if x is not None), None)
    last_ema50 = next((x for x in reversed(ema_50) if x is not None), None)
    last_rsi = next((x for x in reversed(rsi_14) if x is not None), None)
    last_macd_val = next((x for x in reversed(macd['macd_line']) if x is not None), None)
    last_signal_val = next((x for x in reversed(macd['signal_line']) if x is not None), None)
    last_hist_val = next((x for x in reversed(macd['histogram']) if x is not None), None)

    # Technical trend classification
    trend_badge = "Neutral"
    trend_color = "sa"
    trend_desc = "Price in range consolidation"

    if last_sma50 and last_sma200:
        if last_price >= last_sma50 and last_price >= last_sma200 and last_sma50 >= last_sma200:
            trend_badge = "Strong Bullish"
            trend_color = "sg"
            trend_desc = "Trading above 50 & 200 SMA with Golden Cross structure"
        elif last_price >= last_sma200 and last_sma50 >= last_sma200:
            trend_badge = "Bullish"
            trend_color = "sg"
            trend_desc = "Holding institutional support above 200 SMA"
        elif last_price < last_sma50 and last_price < last_sma200 and last_sma50 < last_sma200:
            trend_badge = "Bearish"
            trend_color = "sr"
            trend_desc = "Trading below 50 & 200 SMA under distribution"
        elif last_price < last_sma50 and last_price >= last_sma200:
            trend_badge = "Healthy Pullback"
            trend_color = "sa"
            trend_desc = "Above 200 SMA baseline, testing 50 SMA intermediate support"
        else:
            trend_badge = "Consolidation"
            trend_color = "sa"
            trend_desc = "Base building / range bound"

    rsi_desc = "Neutral (40-60)"
    if last_rsi is not None:
        if last_rsi >= 70:
            rsi_desc = f"Overbought ({last_rsi})"
        elif last_rsi <= 30:
            rsi_desc = f"Oversold ({last_rsi})"
        elif last_rsi > 60:
            rsi_desc = f"Bullish Momentum ({last_rsi})"
        elif last_rsi < 40:
            rsi_desc = f"Weak Momentum ({last_rsi})"
        else:
            rsi_desc = f"Neutral ({last_rsi})"

    macd_desc = "Neutral"
    if last_macd_val is not None and last_signal_val is not None:
        if last_macd_val > last_signal_val and (last_hist_val or 0) > 0:
            macd_desc = "Bullish Crossover (Expanding)"
        elif last_macd_val > last_signal_val:
            macd_desc = "Bullish Momentum"
        elif last_macd_val < last_signal_val and (last_hist_val or 0) < 0:
            macd_desc = "Bearish Crossover (Expanding)"
        else:
            macd_desc = "Bearish Momentum"

    technical_summary = {
        "last_price": last_price,
        "sma_20": last_sma20,
        "sma_50": last_sma50,
        "sma_100": last_sma100,
        "sma_200": last_sma200,
        "ema_20": last_ema20,
        "ema_50": last_ema50,
        "rsi_14": last_rsi,
        "rsi_desc": rsi_desc,
        "macd_line": last_macd_val,
        "signal_line": last_signal_val,
        "histogram": last_hist_val,
        "macd_desc": macd_desc,
        "trend_badge": trend_badge,
        "trend_color": trend_color,
        "trend_desc": trend_desc,
        "data_points_count": len(clean_series),
        "start_date": dates[0] if dates else "",
        "end_date": dates[-1] if dates else ""
    }

    # Return updated dictionary preserving original datasets, plus enriched indicators
    result = dict(chart_data)
    result["datasets"] = computed_datasets
    result["rsi_dataset"] = {
        "values": to_val_pairs(rsi_14),
        "label": "RSI (14)"
    }
    result["macd_datasets"] = {
        "macd": to_val_pairs(macd['macd_line']),
        "signal": to_val_pairs(macd['signal_line']),
        "histogram": to_val_pairs(macd['histogram'])
    }
    result["technical_summary"] = technical_summary
    result["dates"] = dates
    return result
