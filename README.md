# ⚡ Bharat Equities Fundamental Terminal

Institutional-grade fundamental analysis web application for all Indian stocks listed on NSE & BSE.

## Features
- **Search Every Indian Listed Stock**: Instant debounced autocomplete covering all 2,000+ NSE and BSE stocks.
- **Investment Horizon Selector**: Choose any individual year from **1 to 10 Years** (`1Y` to `10Y`) to dynamically recalculate forward EPS, Fair Value bands, Margin of Safety, and multi-scenario projections.
- **Complete 7-Tab Interactive Terminal Report** ("Same to same" as CarTrade benchmark):
  - **★ View (Master Synthesis)**: Signal Radar, Fair Value Bar with live CMP cursor, 3 Strengths / 2 Risks / 1 Thing to Track, 10-point Red Flags card, Forward Revenue Scenarios, Top 5 Investor News.
  - **1. Valuation & Fair Value**: P/E, P/B, EV/EBITDA, PEG comparison bars, Valuation Verdict, and Fair Value specification table.
  - **2. Growth & Beat/Miss**: Pre-computed Screener CAGRs, 8 colored EPS beat/miss chips, and Last 8 Quarters full financials.
  - **3. Financial Health & Cash**: Solvency & liquidity ratios, 3-year OCF vs Net Profit quality table, and free cash flow conversion.
  - **4. Returns & Capital Alloc**: ROCE, ROE, core ROIC (ex-cash), WACC benchmark, and 3-point capital allocation scorecard.
  - **5. Management & Guidance**: Guidance disclosure review, strategic targets execution table (`BEAT`, `MET`, `ON TRACK`), and latest earnings call quotes.
  - **6. Ownership & Peers**: Quarterly shareholding pattern (Promoter, Pledging, FII, DII, Public), governance audit note, and live peer comparison matrix.
  - **7. Data Verification Table (25+ Metrics)**: Full audit trail of verified metrics with sources and checkmarks.
- **SEBI Regulatory Disclaimer**: Included on every web and downloaded report.
  - One-click **Download Standalone HTML Report** for offline viewing.
  - Print / PDF export ready.

## Quick Start
1. Double-click `run.bat` or run:
   ```bash
   python main.py
   ```
2. Open your browser at:
   ```
   http://localhost:8000
   ```
3. Type any stock name (e.g. `Reliance`, `TCS`, `CarTrade`, `HDFC Bank`, `Tata Motors`), select an investment horizon, and hit **Enter**!
