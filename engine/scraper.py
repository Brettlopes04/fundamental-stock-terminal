import json
import os
import re
import time
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

import tempfile

import tempfile
import socket
from engine.security_master import (
    resolve_symbol,
    search_security_master,
    StockNotFoundError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    MissingFinancialsError,
    ProviderDataError,
    TerminalException
)

# On serverless platforms (Vercel, AWS Lambda) or read-only filesystems, use /tmp
is_serverless = os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or not os.access(os.path.dirname(__file__), os.W_OK)
if is_serverless:
    CACHE_DIR = os.path.join(tempfile.gettempdir(), "fundamental_cache")
else:
    CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")

try:
    os.makedirs(CACHE_DIR, exist_ok=True)
except Exception:
    CACHE_DIR = os.path.join(tempfile.gettempdir(), "fundamental_cache")
    os.makedirs(CACHE_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


POPULAR_STOCKS = [
    {"name": "Reliance Industries Ltd", "ticker": "RELIANCE", "url": "/company/RELIANCE/consolidated/"},
    {"name": "Tata Consultancy Services Ltd", "ticker": "TCS", "url": "/company/TCS/consolidated/"},
    {"name": "HDFC Bank Ltd", "ticker": "HDFCBANK", "url": "/company/HDFCBANK/consolidated/"},
    {"name": "ICICI Bank Ltd", "ticker": "ICICIBANK", "url": "/company/ICICIBANK/consolidated/"},
    {"name": "Infosys Ltd", "ticker": "INFY", "url": "/company/INFY/consolidated/"},
    {"name": "Cartrade Tech Ltd", "ticker": "CARTRADE", "url": "/company/CARTRADE/consolidated/"},
    {"name": "Tata Motors Ltd", "ticker": "TATAMOTORS", "url": "/company/TATAMOTORS/consolidated/"},
    {"name": "Zomato Ltd", "ticker": "ZOMATO", "url": "/company/ZOMATO/consolidated/"},
    {"name": "State Bank of India", "ticker": "SBIN", "url": "/company/SBIN/consolidated/"},
    {"name": "Bharti Airtel Ltd", "ticker": "BHARTIARTL", "url": "/company/BHARTIARTL/consolidated/"},
]

def search_stocks(query: str):
    q = query.strip()
    if not q:
        return search_security_master("")

    results = []
    seen_urls = set()

    # 1. Query Canonical Security Master (instant, offline, disambiguated)
    local_matches = search_security_master(q, limit=8)
    for m in local_matches:
        url = m.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            results.append(m)

    # 2. Query upstream Screener search API for SME / new listings with 4s timeout
    queries_to_try = [q]
    if " " not in q and len(q) > 4:
        for prefix in ["tata", "deepak", "reliance", "welspun", "laurus", "aditya", "bharat", "hindustan", "indian", "adani", "bajaj"]:
            if q.lower().startswith(prefix) and len(q) > len(prefix):
                queries_to_try.append(f"{prefix} {q[len(prefix):]}")
                break

    for search_term in queries_to_try:
        try:
            encoded_q = urllib.parse.quote(search_term)
            url = f"https://www.screener.in/api/company/search/?q={encoded_q}"
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode("utf-8"))
                for item in data:
                    raw_url = item.get("url", "")
                    if raw_url and raw_url not in seen_urls:
                        ticker_match = re.search(r"/company/([^/]+)/", raw_url)
                        ticker = ticker_match.group(1) if ticker_match else item.get("name", "").split()[0].upper()
                        seen_urls.add(raw_url)
                        results.append({
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "ticker": ticker,
                            "url": raw_url,
                            "bse_code": "",
                            "common_name": item.get("name", "").split()[0]
                        })
            if len(results) >= 8:
                break
        except Exception:
            pass

    return results


def clean_num(val_str):
    if not val_str:
        return 0.0
    cleaned = re.sub(r"[^\d\.\-]", "", val_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def fetch_company_html(company_slug_or_url: str):
    if company_slug_or_url.startswith("/company/"):
        rel_url = company_slug_or_url
    else:
        rel_url = f"/company/{company_slug_or_url.upper()}/consolidated/"

    full_url = f"https://www.screener.in{rel_url}" if not rel_url.startswith("http") else rel_url
    headers = {"User-Agent": USER_AGENT}

    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, timeout=7) as res:
            return res.read().decode("utf-8"), full_url
    except urllib.error.HTTPError as e:
        if e.code == 404:
            if "consolidated" in full_url:
                fallback_url = full_url.replace("/consolidated/", "/")
                try:
                    req = urllib.request.Request(fallback_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=7) as res:
                        return res.read().decode("utf-8"), fallback_url
                except urllib.error.HTTPError as e2:
                    if e2.code == 404:
                        raise StockNotFoundError(company_slug_or_url)
                    elif e2.code == 429:
                        raise ProviderRateLimitError()
                    else:
                        raise ProviderDataError(f"HTTP {e2.code}")
            raise StockNotFoundError(company_slug_or_url)
        elif e.code == 429:
            raise ProviderRateLimitError()
        else:
            raise ProviderDataError(f"HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError, socket.timeout):
        raise ProviderTimeoutError("Screener Public Exchange Gateway")

def parse_screener_page(html: str, source_url: str):
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    # Basic Info
    name_el = soup.select_one("h1")
    data["name"] = name_el.get_text(strip=True) if name_el else "Unknown Company"
    
    # Extract ticker from source_url
    t_match = re.search(r"/company/([^/]+)/", source_url)
    data["ticker"] = t_match.group(1).upper() if t_match else "STOCK"

    # Links (BSE / NSE)
    bse_link = soup.select_one('a[href*="bseindia.com"]')
    nse_link = soup.select_one('a[href*="nseindia.com"]')
    data["bse_code"] = bse_link["href"].split("/")[-2] if bse_link and "/" in bse_link["href"] else ""
    data["nse_symbol"] = data["ticker"] if nse_link else ""

    # About
    about_el = soup.select_one(".company-profile .about") or soup.select_one(".about")
    data["about"] = about_el.get_text(" ", strip=True) if about_el else ""

    # Peers Sector / Industry
    sector_links = soup.select("#peers .sub a")
    data["sector"] = sector_links[1].get_text(strip=True) if len(sector_links) > 1 else "Diversified"
    data["industry"] = sector_links[-1].get_text(strip=True) if sector_links else "General"

    # Top Ratios
    top_ratios = {}
    for li in soup.select("#top-ratios li"):
        n = li.select_one(".name")
        v = li.select_one(".value")
        if n and v:
            name = n.get_text(strip=True)
            val = v.get_text(" ", strip=True)
            top_ratios[name] = val
    data["top_ratios"] = top_ratios

    # Parsed High / Low
    hl_str = top_ratios.get("High / Low", "")
    if "/" in hl_str:
        parts = hl_str.split("/")
        data["high_52w"] = clean_num(parts[0])
        data["low_52w"] = clean_num(parts[1])
    else:
        data["high_52w"] = 0.0
        data["low_52w"] = 0.0

    data["cmp"] = clean_num(top_ratios.get("Current Price", "0"))
    data["market_cap_cr"] = clean_num(top_ratios.get("Market Cap", "0"))
    data["pe_ratio"] = clean_num(top_ratios.get("Stock P/E", "0"))
    data["book_value"] = clean_num(top_ratios.get("Book Value", "0"))
    data["dividend_yield"] = clean_num(top_ratios.get("Dividend Yield", "0"))
    data["roce"] = clean_num(top_ratios.get("ROCE", "0"))
    data["roe"] = clean_num(top_ratios.get("ROE", "0"))
    data["face_value"] = clean_num(top_ratios.get("Face Value", "10"))

    # CAGR Tables
    cagr_data = {}
    for table in soup.select(".ranges-table"):
        th = table.select_one("th")
        if th:
            category = th.get_text(strip=True)
            cat_dict = {}
            for row in table.select("tr"):
                tds = row.select("td")
                if len(tds) == 2:
                    period = tds[0].get_text(strip=True).replace(":", "")
                    val = tds[1].get_text(strip=True)
                    cat_dict[period] = clean_num(val)
            cagr_data[category] = cat_dict
    data["cagr"] = cagr_data

    # Helper function for tables
    def parse_table(section_id):
        sec = soup.select_one(f"#{section_id}")
        if not sec:
            return {"headers": [], "rows": {}}
        tbl = sec.select_one("table.data-table")
        if not tbl:
            return {"headers": [], "rows": {}}
        headers = [th.get_text(strip=True) for th in tbl.select("thead tr th")[1:] if th.get_text(strip=True)]
        rows = {}
        for tr in tbl.select("tbody tr"):
            tds = tr.select("td")
            if tds:
                row_name = tds[0].get_text(strip=True).replace("+", "").replace("Raw PDF", "").strip()
                if not row_name:
                    continue
                vals = [clean_num(td.get_text(strip=True)) for td in tds[1:]]
                rows[row_name] = vals
        return {"headers": headers, "rows": rows}

    data["quarters"] = parse_table("quarters")
    data["profit_loss"] = parse_table("profit-loss")
    data["balance_sheet"] = parse_table("balance-sheet")
    data["cash_flow"] = parse_table("cash-flow")
    data["ratios"] = parse_table("ratios")
    
    # Shareholding Pattern
    shp = parse_table("shareholding")
    # If quarters tab inside shareholding
    quarterly_shp = soup.select_one("#quarterly-shp")
    if quarterly_shp:
        tbl = quarterly_shp.select_one("table.data-table")
        if tbl:
            headers = [th.get_text(strip=True) for th in tbl.select("thead tr th")[1:] if th.get_text(strip=True)]
            rows = {}
            for tr in tbl.select("tbody tr"):
                tds = tr.select("td")
                if tds:
                    row_name = tds[0].get_text(strip=True).replace("+", "").strip()
                    vals = [clean_num(td.get_text(strip=True)) for td in tds[1:]]
                    rows[row_name] = vals
            data["shareholding"] = {"headers": headers, "rows": rows}
        else:
            data["shareholding"] = shp
    else:
        data["shareholding"] = shp

    # Extract company_id & warehouse_id
    c_ids = re.findall(r'/api/company/(\d+)/', html)
    data["company_id"] = c_ids[0] if c_ids else ""
    wids = re.findall(r'data-warehouse-id="(\d+)"', html)
    data["warehouse_id"] = wids[0] if wids else ""

    # Fetch peers from Screener API
    peers = []
    wid_for_peers = data["warehouse_id"]
    if wid_for_peers:
        try:
            peer_url = f"https://www.screener.in/api/company/{wid_for_peers}/peers/"
            req = urllib.request.Request(peer_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as p_res:
                p_soup = BeautifulSoup(p_res.read().decode("utf-8"), "html.parser")
                p_table = p_soup.select_one("table")
                if p_table:
                    for tr in p_table.select("tbody tr"):
                        tds = tr.select("td")
                        if len(tds) >= 5:
                            p_name = tds[1].get_text(strip=True)
                            p_cmp = clean_num(tds[2].get_text(strip=True))
                            p_pe = clean_num(tds[3].get_text(strip=True))
                            p_mcap = clean_num(tds[4].get_text(strip=True))
                            p_roce = clean_num(tds[10].get_text(strip=True)) if len(tds) > 10 else 0.0
                            peers.append({
                                "name": p_name,
                                "cmp": p_cmp,
                                "pe": p_pe,
                                "mcap": p_mcap,
                                "roce": p_roce
                            })
        except Exception:
            pass
    data["peers"] = peers

    # Extract announcements from #documents
    announcements = []
    docs = soup.select_one("#documents")
    if docs:
        for li in docs.select("li"):
            txt = li.get_text(" ", strip=True)
            if "Announcement" in txt or "Press Release" in txt or "Outcome" in txt or "Investor Presentation" in txt:
                cleaned_txt = re.sub(r"Announcement under Regulation 30 \(LODR\)-", "", txt).strip()
                if cleaned_txt and len(announcements) < 5:
                    announcements.append(cleaned_txt)
    data["announcements"] = announcements

    return data


def fetch_chart_data(company_id: str, metric: str = "Price-DMA50-DMA200-Volume", days: int = 1095):
    """
    Fetch genuine historical chart data directly from Screener.in's official API
    q options:
    - Price-DMA50-DMA200-Volume (Price, 50 DMA, 200 DMA, Volume + Delivery %)
    - Price to Earning-Median PE-EPS (PE ratio, 10Y Median PE, EPS)
    - Price to book value-Median PBV-Book value (Price to Book, Median PBV)
    - GPM-OPM-NPM-Quarter Sales (Sales and Margins)
    """
    if not company_id:
        return {"datasets": []}

    encoded_metric = urllib.parse.quote(metric)
    url = f"https://www.screener.in/api/company/{company_id}/chart/?q={encoded_metric}&days={days}"
    headers = {"User-Agent": USER_AGENT}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        return {"datasets": [], "error": str(e)}


def get_stock_data(query_or_ticker: str, force_refresh: bool = False):
    query = query_or_ticker.strip()
    if not query:
        raise StockNotFoundError(query_or_ticker)

    # 1. Resolve through Security Master first
    canonical = resolve_symbol(query)
    slug = canonical["provider_symbol"] if canonical else re.sub(r'[^A-Za-z0-9_]', '', query).upper()
    cache_file = os.path.join(CACHE_DIR, f"{slug}.json")

    # Check cache (12 hour expiration)
    if not force_refresh and os.path.exists(cache_file):
        try:
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < 12 * 3600:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if cached_data.get("cmp") or cached_data.get("top_ratios"):
                        return cached_data
        except Exception:
            pass

    html = None
    final_url = None

    # Step 1: If canonical resolved, fetch directly
    if canonical:
        try:
            url = f"/company/{canonical['provider_symbol']}/consolidated/"
            html, final_url = fetch_company_html(url)
        except StockNotFoundError:
            try:
                url = f"/company/{canonical['provider_symbol']}/"
                html, final_url = fetch_company_html(url)
            except Exception:
                html = None
        except Exception as e:
            if isinstance(e, TerminalException):
                raise e
            html = None

    # Step 2: If not resolved or direct failed, attempt clean slug
    if not html and len(slug) >= 2 and len(slug) <= 15 and not any(c.isspace() for c in query):
        try:
            url = f"/company/{slug}/consolidated/"
            html, final_url = fetch_company_html(url)
        except Exception:
            try:
                url = f"/company/{slug}/"
                html, final_url = fetch_company_html(url)
            except Exception:
                html = None

    # Step 3: Fallback to searching Screener for company name, partial query or ticker mapping
    if not html:
        matches = search_stocks(query)
        if matches:
            top_match = matches[0]
            matched_url = top_match.get("url", "")
            try:
                html, final_url = fetch_company_html(matched_url)
            except Exception:
                if "/consolidated/" in matched_url:
                    fallback_url = matched_url.replace("/consolidated/", "/")
                    try:
                        html, final_url = fetch_company_html(fallback_url)
                    except Exception:
                        pass

    if not html:
        raise StockNotFoundError(query_or_ticker)

    parsed = parse_screener_page(html, final_url)

    # Validate essential financials
    if not parsed.get("cmp") and not parsed.get("quarters", {}).get("headers"):
        raise MissingFinancialsError(parsed.get("name", query), parsed.get("ticker", query))

    # Enrich with canonical record data if available
    if canonical:
        parsed["bse_code"] = parsed.get("bse_code") or canonical.get("bse_code", "")
        parsed["nse_symbol"] = parsed.get("nse_symbol") or canonical.get("nse_symbol", "")
        parsed["common_name"] = canonical.get("common_name", parsed.get("name"))
        parsed["exchange"] = canonical.get("exchange", "NSE & BSE")
        if not parsed.get("sector") or parsed.get("sector") == "Diversified":
            parsed["sector"] = canonical.get("sector", parsed.get("sector"))
        if not parsed.get("industry") or parsed.get("industry") == "General":
            parsed["industry"] = canonical.get("industry", parsed.get("industry"))

    # Save cache
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return parsed

