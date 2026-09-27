# ⚡ Bharat Equities Fundamental Terminal

Institutional-grade fundamental analysis & technical charting web application for Indian equities listed on the **National Stock Exchange (NSE)** and **Bombay Stock Exchange (BSE)**.

**Live Production URL**: [https://fundamental-stock-terminal.vercel.app/](https://fundamental-stock-terminal.vercel.app/)  
**GitHub Repository**: [https://github.com/Brettlopes04/fundamental-stock-terminal](https://github.com/Brettlopes04/fundamental-stock-terminal)

---

## 🌟 Key Architecture & Capabilities

### 1. Canonical Security Master & Robust Symbol Resolution
- **Zero-Latency Local Indexing**: Over 500+ top Indian equities pre-indexed across Nifty 50, Next 50, Midcaps, and BSE scrip codes.
- **Dynamic Fallback**: Instant upstream fallback for small-cap and newly listed SME companies.
- **Smart Disambiguation**: Resolves ambiguous brand names and company conglomerates (e.g. `Tata` → Tata Motors, TCS, Tata Steel, Tata Power, Tata Consumer).
- **Corporate Reclassifications & Aliases**: Seamlessly resolves legacy and renamed entities:
  - `ZOMATO` → **Eternal Ltd** (`ETERNAL` / BSE: `543320`)
  - `TATA MOTORS` → **Tata Motors Ltd** (`TMCV` / BSE: `500570`)
  - `CARTRADE` → **Cartrade Tech Ltd** (`CARTRADE` / BSE: `543333`)
  - 6-digit BSE Scrip Codes (e.g. `500325` → `RELIANCE`)

### 2. Authentic 8-Tab Terminal Report
Every generated stock research report features 8 comprehensive sections:
1. **★ Master View**: Radar signal matrix, Fair Value band with CMP cursor, 3 Strengths / 2 Risks / 1 Thing to Track, 10-point Red Flags audit, Forward Revenue Scenarios.
2. **1. Valuation & Fair Value**: Historical P/E vs 10Y Median, Price-to-Book, EV/EBITDA, PEG classification, and multi-scenario valuation models.
3. **2. Growth & Beat/Miss**: Pre-computed exchange CAGRs (Sales, Profit, ROCE, ROE), 8-quarter EPS beat/miss history with badge indicators, and 8 quarters of financial statements.
4. **3. Financial Health & Cash**: Solvency analysis, Altman Z-Score / Beneish M-Score style forensic flags, 3-year Operating Cash Flow vs Reported PAT quality audit, Free Cash Flow conversion.
5. **4. Returns & Capital Allocation**: ROCE, ROE, core ROIC (ex-cash), incremental ROIC, WACC comparison, and 3-point capital allocation scorecard.
6. **5. Management & Guidance**: Guidance disclosure review, multi-year strategic target execution tracking (`BEAT`, `MET`, `ON TRACK`), and earnings conference call commentary.
7. **6. Ownership & Peer Matrix**: Quarterly shareholding pattern (Promoter, Pledging, FII, DII, Public), governance score, and live peer comparison table.
8. **8. CHART (Official Screener.in & Chartink / TradingView)**:
   - **Authentic Historical Price Stream**: Daily closing prices and volume directly from Screener.in official chart API. Zero synthetic or random candles.
   - **Technical Indicators**: Computed directly over genuine historical closing prices:
     - Simple Moving Averages: **SMA 20**, **SMA 50**, **SMA 100**, **SMA 200**
     - Exponential Moving Averages: **EMA 20**, **EMA 50**
     - Relative Strength Index: **RSI (14)** with Overbought/Oversold/Momentum badges
     - Moving Average Convergence Divergence: **MACD (12, 26, 9)** line, signal, and histogram
     - Volume: Total daily shares exchanged with delivery ratio indication
   - **Interactive Overlay Toggles**: One-click toggles for individual moving average overlays without reloading.
   - **Multi-Timeframe Controls**: `1M`, `3M`, `6M`, `1Yr`, `3Yr`, `5Yr`, `10Yr`, `Max`.
   - **Live Institutional Candlestick Widget**: Integrated TradingView candlestick chart (`NSE:{symbol}` or `BSE:{code}`).
   - **Direct Technical Scanners**: Instant one-click jump to Chartink live technical breakouts and Screener filings.
   - **Strict Data Decoupling**: Independent error boundary ensures chart errors never block the 7 fundamental audit sections. Historical market actuals are visibly distinguished from model fair-value targets.

### 3. Non-Blocking Terminal Error Handling
- Blocking browser `alert()` popups have been eliminated and replaced by sleek in-page error cards.
- Typed exceptions categorize errors (`STOCK_NOT_FOUND`, `PROVIDER_TIMEOUT`, `PROVIDER_RATE_LIMIT`, `MISSING_FINANCIALS`) with actionable suggestions and direct retry options.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.9+
- pip

### Installation & Run
```bash
# Clone the repository
git clone https://github.com/Brettlopes04/fundamental-stock-terminal.git
cd fundamental-stock-terminal

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python main.py
```
Open your browser at `http://127.0.0.1:8000`.

---

## 🧪 Automated Testing Suite (23 Scenarios)

The project includes an automated test suite verifying 23 scenarios across symbol resolution, data integrity, technical indicators, and error boundaries:
```bash
python -m unittest tests/test_terminal.py -v
```

### Verified Test Cases:
1. Stock search by NSE ticker (`RELIANCE`)
2. Stock search by company name (`Tata Consultancy Services`)
3. Stock search by recognized alias (`ZOMATO` → `ETERNAL`)
4. Ambiguous stock search ranking (`Tata` → multiple entities)
5. 6-digit BSE scrip code lookup (`500325`)
6. Unsupported symbol handling (structured 404 response)
7. Upstream timeout handling (`PROVIDER_TIMEOUT` 504)
8. Upstream rate limit handling (`PROVIDER_RATE_LIMIT` 429)
9. Malformed API response handling
10. Missing price history handling
11. Historical time series chronological sorting & validation
12. Invalid OHLC/price filtering (negative & non-numeric values discarded)
13. Duplicate timestamp deduplication
14. Missing volume fallback handling
15. Historical range selection (`1M` to `Max`)
16. Investment horizon mapping (`1Y` to `10Y`)
17. Switching between different stocks with state isolation
18. Stale chart data prevention
19. Chart endpoint and health check readiness (`/api/health`)
20. Decoupled chart error boundary (fundamental report resilience)
21. Chart unavailable state rendering
22. API key and secret credential protection
23. Vercel serverless deployment compatibility

---

## 🌐 Production Deployment

The project is configured for Vercel deployment:
- Entry point: `main.py` (FastAPI detected by Vercel Fluid Compute)
- Static assets: `public/` and `static/`
- Serverless cache: `/tmp/fundamental_cache` (ephemeral serverless filesystem compatible)

To deploy to production:
```bash
vercel --prod --yes
```

---

## ⚖️ SEBI Regulatory Disclaimer
This application is developed strictly for educational, informational, and academic research purposes. It does not constitute investment advice, financial advisory services, or an endorsement to buy, hold, or sell any security under SEBI (Investment Advisers) Regulations, 2013 or SEBI (Research Analysts) Regulations, 2014. Financial metrics and filings are compiled from public exchange disclosures. Please consult a SEBI-registered investment advisor before making financial decisions.
