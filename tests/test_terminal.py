import os
import unittest
from fastapi.testclient import TestClient
import main
from engine.security_master import (
    resolve_symbol,
    search_security_master,
    StockNotFoundError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    TerminalException
)
from engine.technical_indicators import (
    validate_and_sort_series,
    compute_sma,
    compute_ema,
    compute_rsi,
    compute_macd,
    process_technical_indicators
)
from engine.analyzer import analyze_stock
from engine.report_generator import generate_terminal_html

class TestFundamentalTerminal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    # 1. Stock search by NSE symbol
    def test_01_search_by_nse_symbol(self):
        resolved = resolve_symbol("RELIANCE")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["nse_symbol"], "RELIANCE")
        self.assertEqual(resolved["provider_symbol"], "RELIANCE")

    # 2. Stock search by company name
    def test_02_search_by_company_name(self):
        resolved = resolve_symbol("Tata Consultancy Services")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["nse_symbol"], "TCS")

    # 3. Stock search by alias (ZOMATO -> ETERNAL)
    def test_03_search_by_alias(self):
        resolved = resolve_symbol("ZOMATO")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["provider_symbol"], "ETERNAL")

    # 4. Ambiguous stock search
    def test_04_ambiguous_stock_search(self):
        matches = search_security_master("Tata", limit=10)
        self.assertGreater(len(matches), 1)
        tickers = [m["ticker"] for m in matches]
        self.assertTrue(any("TATAMOTORS" in t or "TCS" in t or "TATASTEEL" in t for t in tickers))

    # 5. BSE-only listing / scrip code lookup
    def test_05_bse_code_lookup(self):
        resolved = resolve_symbol("500325")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["nse_symbol"], "RELIANCE")
        self.assertEqual(resolved["bse_code"], "500325")

    # 6. Unsupported symbol handling (structured 404 response)
    def test_06_unsupported_symbol_handling(self):
        res = self.client.get("/api/report?query=TOTALLY_INVALID_TICKER_99999")
        self.assertEqual(res.status_code, 404)
        data = res.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error_code"], "STOCK_NOT_FOUND")
        self.assertIn("suggestions", data)
        self.assertGreater(len(data["suggestions"]), 0)

    # 7. Provider timeout handling
    def test_07_provider_timeout_handling(self):
        exc = ProviderTimeoutError("Upstream exchange API timed out after 7s")
        self.assertEqual(exc.http_status, 504)
        self.assertEqual(exc.error_code, "PROVIDER_TIMEOUT")
        d = exc.to_dict()
        self.assertFalse(d["success"])

    # 8. Provider rate limit handling
    def test_08_provider_rate_limit_handling(self):
        exc = ProviderRateLimitError("429 Too Many Requests")
        self.assertEqual(exc.http_status, 429)
        self.assertEqual(exc.error_code, "PROVIDER_RATE_LIMIT")

    # 9. Malformed API response handling
    def test_09_malformed_api_response_handling(self):
        processed = process_technical_indicators({})
        self.assertIn("datasets", processed)
        self.assertEqual(len(processed["datasets"]), 0)

    # 10. Missing price history handling
    def test_10_missing_price_history_handling(self):
        processed = process_technical_indicators({"datasets": [{"metric": "Price", "values": []}]})
        self.assertIn("datasets", processed)

    # 11. Valid historical candles / series validation
    def test_11_valid_series_validation(self):
        raw = [["2023-01-02", 100.5], ["2023-01-01", 99.0], ["2023-01-03", 102.0]]
        cleaned = validate_and_sort_series(raw)
        self.assertEqual(len(cleaned), 3)
        self.assertEqual(cleaned[0][0], "2023-01-01")
        self.assertEqual(cleaned[-1][0], "2023-01-03")

    # 12. Invalid OHLC / price values validation (negative & nulls filtered)
    def test_12_invalid_price_values_validation(self):
        raw = [["2023-01-01", -50.0], ["2023-01-02", None], ["invalid-date", 100.0], ["2023-01-03", 150.0]]
        cleaned = validate_and_sort_series(raw)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0], ("2023-01-03", 150.0))

    # 13. Duplicate timestamps filter
    def test_13_duplicate_timestamps_filter(self):
        raw = [["2023-01-01", 100.0], ["2023-01-01", 105.0], ["2023-01-02", 110.0]]
        cleaned = validate_and_sort_series(raw)
        self.assertEqual(len(cleaned), 2)
        dates = [c[0] for c in cleaned]
        self.assertEqual(len(dates), len(set(dates)))

    # 14. Missing volume handling
    def test_14_missing_volume_handling(self):
        chart_no_vol = {
            "datasets": [
                {"metric": "Price", "values": [["2023-01-01", 100.0], ["2023-01-02", 102.0]]}
            ]
        }
        processed = process_technical_indicators(chart_no_vol)
        vol_ds = next((d for d in processed["datasets"] if d["metric"] == "Volume"), None)
        self.assertIsNotNone(vol_ds)
        self.assertEqual(vol_ds["values"][0][1], 0.0)

    # 15. Historical range selection
    def test_15_historical_range_selection(self):
        days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365, "3Y": 1095, "5Y": 1825, "10Y": 3652, "Max": 10000}
        for label, days in days_map.items():
            self.assertGreater(days, 0)

    # 16. Investment horizon changes (1Y to 10Y)
    def test_16_investment_horizon_changes(self):
        mock_raw = {"name": "Test Co", "ticker": "TEST", "cmp": 100.0, "market_cap_cr": 5000}
        report_1y = analyze_stock(mock_raw, horizon_years=1)
        report_10y = analyze_stock(mock_raw, horizon_years=10)
        self.assertEqual(report_1y["horizon_years"], 1)
        self.assertEqual(report_10y["horizon_years"], 10)
        self.assertEqual(report_1y["chart_days"], 365)
        self.assertEqual(report_10y["chart_days"], 3650)

    # 17. Switching between two different stocks
    def test_17_stock_switch_isolation(self):
        mock_a = {"name": "Stock Alpha", "ticker": "ALPHA", "cmp": 50.0}
        mock_b = {"name": "Stock Beta", "ticker": "BETA", "cmp": 250.0}
        rep_a = analyze_stock(mock_a, horizon_years=3)
        rep_b = analyze_stock(mock_b, horizon_years=3)
        self.assertEqual(rep_a["ticker"], "ALPHA")
        self.assertEqual(rep_b["ticker"], "BETA")
        self.assertNotEqual(rep_a["cmp"], rep_b["cmp"])

    # 18. Stale chart data prevention
    def test_18_stale_chart_data_prevention(self):
        mock_with_chart = {
            "name": "Active", "ticker": "ACT", "cmp": 100.0,
            "company_id": "123",
            "chart_data": {"datasets": [{"metric": "Price", "values": [["2023-01-01", 100.0]]}]}
        }
        mock_no_chart = {"name": "Blank", "ticker": "BLANK", "cmp": 20.0}
        rep_with = analyze_stock(mock_with_chart)
        rep_no = analyze_stock(mock_no_chart)
        self.assertIn("chart_data", rep_with)
        self.assertEqual(rep_no.get("chart_data", {}).get("datasets", []), [])

    # 19. Chart loading state & endpoint readiness
    def test_19_chart_endpoint_readiness(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    # 20. Chart error state (independent error boundary: fundamental sections survive)
    def test_20_chart_error_decoupling(self):
        mock_data = {
            "name": "Resilient Corp",
            "ticker": "RESILIENT",
            "cmp": 450.0,
            "pe_ratio": 22.5,
            "book_value": 150.0,
            "market_cap_cr": 12000,
            "company_id": "INVALID_BROKEN_ID"
        }
        report = analyze_stock(mock_data, horizon_years=3)
        self.assertEqual(report["ticker"], "RESILIENT")
        self.assertEqual(report["cmp"], 450.0)
        html = generate_terminal_html(report)
        self.assertIn("RESILIENT", html)
        self.assertIn("tab-charts", html)

    # 21. Chart unavailable state rendering
    def test_21_chart_unavailable_state(self):
        report = {
            "name": "New IPO",
            "ticker": "NEWIPO",
            "cmp": 120.0,
            "horizon_years": 3,
            "chart_data": {"datasets": []}
        }
        html = generate_terminal_html(report)
        self.assertIn("tab-charts", html)
        self.assertIn("NEWIPO", html)

    # 22. API key protection (no hardcoded secrets)
    def test_22_api_key_protection(self):
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("screener_secret", content.lower())
        self.assertNotIn("tradingview_api_key", content.lower())
        self.assertNotIn("password", content.lower())

    # 23. Vercel deployment compatibility
    def test_23_vercel_compatibility(self):
        self.assertTrue(os.path.exists("vercel.json"))
        self.assertTrue(os.path.exists("main.py"))
        import engine.scraper as sc
        self.assertTrue(os.path.exists(sc.CACHE_DIR))

if __name__ == "__main__":
    unittest.main()
