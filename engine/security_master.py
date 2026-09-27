"""
Security Master: Canonical Instrument Index & Symbol Resolution System
Indian Listed Equities (NSE & BSE)
"""
import re
from typing import List, Dict, Optional, Any

class TerminalException(Exception):
    def __init__(self, error_code: str, title: str, message: str, suggestions: List[str] = None, http_status: int = 400):
        super().__init__(message)
        self.error_code = error_code
        self.title = title
        self.message = message
        self.suggestions = suggestions or []
        self.http_status = http_status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": False,
            "error_code": self.error_code,
            "title": self.title,
            "message": self.message,
            "suggestions": self.suggestions
        }

class StockNotFoundError(TerminalException):
    def __init__(self, query: str):
        super().__init__(
            error_code="STOCK_NOT_FOUND",
            title="Stock Not Found",
            message=f"Could not resolve '{query}' to an active NSE or BSE listed equity.",
            suggestions=[
                "Check for spelling errors in the company name",
                "Try searching by official NSE ticker (e.g., RELIANCE, TCS, INFY)",
                "Try searching by 6-digit BSE scrip code (e.g., 500325, 543320)",
                "Verify if the stock was recently renamed or listed under a holding company"
            ],
            http_status=404
        )

class ProviderTimeoutError(TerminalException):
    def __init__(self, provider: str = "Market Data"):
        super().__init__(
            error_code="PROVIDER_TIMEOUT",
            title="Data Provider Timeout",
            message=f"The upstream exchange filing provider ({provider}) did not respond within the 7-second latency window.",
            suggestions=[
                "Retry your request in a few seconds",
                "Select a pre-cached horizon or popular equity",
                "Check whether exchange data servers are experiencing high market load"
            ],
            http_status=504
        )

class ProviderRateLimitError(TerminalException):
    def __init__(self, message: Optional[str] = None):
        super().__init__(
            error_code="PROVIDER_RATE_LIMIT",
            title="Upstream Rate Limit Exceeded",
            message=message or "Too many concurrent requests were sent to the upstream market data gateway.",
            suggestions=[
                "Wait 10-15 seconds before issuing another query",
                "Use the existing cached reports"
            ],
            http_status=429
        )

class MissingFinancialsError(TerminalException):
    def __init__(self, company_name: str, symbol: str):
        super().__init__(
            error_code="MISSING_FINANCIALS",
            title="Incomplete Financial Filings",
            message=f"Public filings for '{company_name}' ({symbol}) are missing essential balance sheets or CAGR ratios.",
            suggestions=[
                "Verify if this company is a newly listed IPO with fewer than 2 quarters of history",
                "Check if the company is currently under corporate restructuring or suspension"
            ],
            http_status=422
        )

class ProviderDataError(TerminalException):
    def __init__(self, details: str):
        super().__init__(
            error_code="PROVIDER_ERROR",
            title="Upstream Filing Parse Error",
            message=f"An unexpected data format was returned by the exchange provider: {details}",
            suggestions=[
                "Retry in a few moments",
                "Report this ticker if the problem persists"
            ],
            http_status=502
        )


CANONICAL_EQUITIES: List[Dict[str, Any]] = [
    # Mega-Caps & Popular Equities
    {
        "name": "Reliance Industries Ltd",
        "common_name": "Reliance",
        "nse_symbol": "RELIANCE",
        "bse_code": "500325",
        "exchange": "NSE & BSE",
        "instrument_id": "1418587",
        "provider_symbol": "RELIANCE",
        "sector": "Energy & Petrochemicals",
        "industry": "Oil, Gas & Consumer Conglomerate",
        "aliases": ["RELIANCE", "RIL", "JIO", "MUKESH AMBANI", "RELIANCE INDUSTRIES"]
    },
    {
        "name": "Tata Consultancy Services Ltd",
        "common_name": "TCS",
        "nse_symbol": "TCS",
        "bse_code": "532540",
        "exchange": "NSE & BSE",
        "instrument_id": "1418588",
        "provider_symbol": "TCS",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "aliases": ["TCS", "TATA CONSULTANCY SERVICES", "TATA CONSULTANCY", "TCSL"]
    },
    {
        "name": "HDFC Bank Ltd",
        "common_name": "HDFC Bank",
        "nse_symbol": "HDFCBANK",
        "bse_code": "500180",
        "exchange": "NSE & BSE",
        "instrument_id": "1418589",
        "provider_symbol": "HDFCBANK",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "aliases": ["HDFCBANK", "HDFC BANK", "HDFC", "HOUSING DEVELOPMENT FINANCE CORPORATION"]
    },
    {
        "name": "ICICI Bank Ltd",
        "common_name": "ICICI Bank",
        "nse_symbol": "ICICIBANK",
        "bse_code": "532174",
        "exchange": "NSE & BSE",
        "instrument_id": "1418590",
        "provider_symbol": "ICICIBANK",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "aliases": ["ICICIBANK", "ICICI BANK", "ICICI"]
    },
    {
        "name": "Infosys Ltd",
        "common_name": "Infosys",
        "nse_symbol": "INFY",
        "bse_code": "500209",
        "exchange": "NSE & BSE",
        "instrument_id": "1418591",
        "provider_symbol": "INFY",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "aliases": ["INFY", "INFOSYS", "INFOSYS TECHNOLOGIES"]
    },
    {
        "name": "Tata Motors Ltd",
        "common_name": "Tata Motors",
        "nse_symbol": "TATAMOTORS",
        "bse_code": "500570",
        "exchange": "NSE & BSE",
        "instrument_id": "1285768",
        "provider_symbol": "TMCV",
        "sector": "Automobile",
        "industry": "Commercial & Passenger Vehicles",
        "aliases": ["TATAMOTORS", "TATA MOTORS", "TMCV", "JLR", "JAGUAR LAND ROVER"]
    },
    {
        "name": "Zomato Ltd",
        "common_name": "Zomato",
        "nse_symbol": "ZOMATO",
        "bse_code": "543320",
        "exchange": "NSE & BSE",
        "instrument_id": "1274894",
        "provider_symbol": "ETERNAL",
        "sector": "Consumer Technology",
        "industry": "Food Delivery & Quick Commerce (Blinkit, District)",
        "aliases": ["ZOMATO", "ZOMATO LTD", "BLINKIT"]
    },
    {
        "name": "Eternal Ltd",
        "common_name": "Eternal",
        "nse_symbol": "ETERNAL",
        "bse_code": "543320",
        "exchange": "NSE & BSE",
        "instrument_id": "1274894",
        "provider_symbol": "ETERNAL",
        "sector": "Consumer Technology",
        "industry": "Food Delivery & Quick Commerce",
        "aliases": ["ETERNAL", "ETERNAL LTD"]
    },
    {
        "name": "Cartrade Tech Ltd",
        "common_name": "CarTrade",
        "nse_symbol": "CARTRADE",
        "bse_code": "543330",
        "exchange": "NSE & BSE",
        "instrument_id": "1418593",
        "provider_symbol": "CARTRADE",
        "sector": "Consumer Technology",
        "industry": "Auto Marketplace & Classifieds",
        "aliases": ["CARTRADE", "CAR TRADE", "CARTRADE TECH", "CARWALE", "BIKEWALE", "SHRIRAM AUTOMALL"]
    },
    {
        "name": "State Bank of India",
        "common_name": "SBI",
        "nse_symbol": "SBIN",
        "bse_code": "500112",
        "exchange": "NSE & BSE",
        "instrument_id": "1418594",
        "provider_symbol": "SBIN",
        "sector": "Financial Services",
        "industry": "Public Sector Banking",
        "aliases": ["SBIN", "SBI", "STATE BANK OF INDIA", "STATE BANK"]
    },
    {
        "name": "Bharti Airtel Ltd",
        "common_name": "Airtel",
        "nse_symbol": "BHARTIARTL",
        "bse_code": "532454",
        "exchange": "NSE & BSE",
        "instrument_id": "1418595",
        "provider_symbol": "BHARTIARTL",
        "sector": "Telecommunications",
        "industry": "Telecom Services",
        "aliases": ["BHARTIARTL", "AIRTEL", "BHARTI AIRTEL"]
    },
    {
        "name": "ITC Ltd",
        "common_name": "ITC",
        "nse_symbol": "ITC",
        "bse_code": "500875",
        "exchange": "NSE & BSE",
        "instrument_id": "1418596",
        "provider_symbol": "ITC",
        "sector": "FMCG",
        "industry": "Cigarettes, FMCG & Hotels",
        "aliases": ["ITC", "ITC LTD", "INDIAN TOBACCO COMPANY"]
    },
    {
        "name": "Hindustan Unilever Ltd",
        "common_name": "HUL",
        "nse_symbol": "HINDUNILVR",
        "bse_code": "500696",
        "exchange": "NSE & BSE",
        "instrument_id": "1418597",
        "provider_symbol": "HINDUNILVR",
        "sector": "FMCG",
        "industry": "Household & Personal Care",
        "aliases": ["HINDUNILVR", "HUL", "HINDUSTAN UNILEVER", "UNILEVER"]
    },
    {
        "name": "Larsen & Toubro Ltd",
        "common_name": "L&T",
        "nse_symbol": "LT",
        "bse_code": "500510",
        "exchange": "NSE & BSE",
        "instrument_id": "1418598",
        "provider_symbol": "LT",
        "sector": "Capital Goods & Infrastructure",
        "industry": "Engineering & Construction",
        "aliases": ["LT", "L&T", "LARSEN & TOUBRO", "LARSEN AND TOUBRO"]
    },
    {
        "name": "Bajaj Finance Ltd",
        "common_name": "Bajaj Finance",
        "nse_symbol": "BAJFINANCE",
        "bse_code": "500034",
        "exchange": "NSE & BSE",
        "instrument_id": "1418599",
        "provider_symbol": "BAJFINANCE",
        "sector": "Financial Services",
        "industry": "NBFC & Consumer Lending",
        "aliases": ["BAJFINANCE", "BAJAJ FINANCE", "BAJAJ FINSERV"]
    },
    {
        "name": "Kotak Mahindra Bank Ltd",
        "common_name": "Kotak Bank",
        "nse_symbol": "KOTAKBANK",
        "bse_code": "500247",
        "exchange": "NSE & BSE",
        "instrument_id": "1418600",
        "provider_symbol": "KOTAKBANK",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "aliases": ["KOTAKBANK", "KOTAK", "KOTAK MAHINDRA BANK"]
    },
    {
        "name": "Maruti Suzuki India Ltd",
        "common_name": "Maruti Suzuki",
        "nse_symbol": "MARUTI",
        "bse_code": "532500",
        "exchange": "NSE & BSE",
        "instrument_id": "1418601",
        "provider_symbol": "MARUTI",
        "sector": "Automobile",
        "industry": "Passenger Cars & Utility Vehicles",
        "aliases": ["MARUTI", "MARUTI SUZUKI", "SUZUKI"]
    },
    {
        "name": "Sun Pharmaceutical Industries Ltd",
        "common_name": "Sun Pharma",
        "nse_symbol": "SUNPHARMA",
        "bse_code": "524715",
        "exchange": "NSE & BSE",
        "instrument_id": "1418602",
        "provider_symbol": "SUNPHARMA",
        "sector": "Healthcare & Pharmaceuticals",
        "industry": "Pharmaceutical Formulations",
        "aliases": ["SUNPHARMA", "SUN PHARMA", "SUN PHARMACEUTICAL"]
    },
    {
        "name": "Axis Bank Ltd",
        "common_name": "Axis Bank",
        "nse_symbol": "AXISBANK",
        "bse_code": "532215",
        "exchange": "NSE & BSE",
        "instrument_id": "1418603",
        "provider_symbol": "AXISBANK",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "aliases": ["AXISBANK", "AXIS BANK", "UTI BANK"]
    },
    {
        "name": "Mahindra & Mahindra Ltd",
        "common_name": "M&M",
        "nse_symbol": "M&M",
        "bse_code": "500520",
        "exchange": "NSE & BSE",
        "instrument_id": "1418604",
        "provider_symbol": "M&M",
        "sector": "Automobile",
        "industry": "Automotive & Farm Equipment",
        "aliases": ["M&M", "MAHINDRA", "MAHINDRA & MAHINDRA", "MNM"]
    },
    {
        "name": "Titan Company Ltd",
        "common_name": "Titan",
        "nse_symbol": "TITAN",
        "bse_code": "500114",
        "exchange": "NSE & BSE",
        "instrument_id": "1418605",
        "provider_symbol": "TITAN",
        "sector": "Consumer Discretionary",
        "industry": "Jewellery, Watches & Eyewear",
        "aliases": ["TITAN", "TITAN COMPANY", "TANISHQ"]
    },
    {
        "name": "Tata Steel Ltd",
        "common_name": "Tata Steel",
        "nse_symbol": "TATASTEEL",
        "bse_code": "500470",
        "exchange": "NSE & BSE",
        "instrument_id": "1418606",
        "provider_symbol": "TATASTEEL",
        "sector": "Metals & Mining",
        "industry": "Steel Manufacturing",
        "aliases": ["TATASTEEL", "TATA STEEL", "TISCO"]
    },
    {
        "name": "Tata Power Company Ltd",
        "common_name": "Tata Power",
        "nse_symbol": "TATAPOWER",
        "bse_code": "500400",
        "exchange": "NSE & BSE",
        "instrument_id": "1418607",
        "provider_symbol": "TATAPOWER",
        "sector": "Utilities & Power",
        "industry": "Power Generation & Distribution",
        "aliases": ["TATAPOWER", "TATA POWER"]
    },
    {
        "name": "Tata Consumer Products Ltd",
        "common_name": "Tata Consumer",
        "nse_symbol": "TATACONSUM",
        "bse_code": "500800",
        "exchange": "NSE & BSE",
        "instrument_id": "1418608",
        "provider_symbol": "TATACONSUM",
        "sector": "FMCG",
        "industry": "Tea, Coffee, Salt & Packaged Foods",
        "aliases": ["TATACONSUM", "TATA CONSUMER", "TATA TEA", "TATA SALT"]
    },
    {
        "name": "Tata Elxsi Ltd",
        "common_name": "Tata Elxsi",
        "nse_symbol": "TATAELXSI",
        "bse_code": "500408",
        "exchange": "NSE & BSE",
        "instrument_id": "1418609",
        "provider_symbol": "TATAELXSI",
        "sector": "Information Technology",
        "industry": "Design & Technology Services",
        "aliases": ["TATAELXSI", "TATA ELXSI"]
    },
    {
        "name": "Deepak Nitrite Ltd",
        "common_name": "Deepak Nitrite",
        "nse_symbol": "DEEPAKNTR",
        "bse_code": "506401",
        "exchange": "NSE & BSE",
        "instrument_id": "1418610",
        "provider_symbol": "DEEPAKNTR",
        "sector": "Chemicals",
        "industry": "Basic & Specialty Chemicals",
        "aliases": ["DEEPAKNTR", "DEEPAK NITRITE", "DEEPAK"]
    },
    {
        "name": "Adani Enterprises Ltd",
        "common_name": "Adani Enterprises",
        "nse_symbol": "ADANIENT",
        "bse_code": "512599",
        "exchange": "NSE & BSE",
        "instrument_id": "1418611",
        "provider_symbol": "ADANIENT",
        "sector": "Diversified",
        "industry": "Infrastructure & Trading",
        "aliases": ["ADANIENT", "ADANI ENTERPRISES", "ADANI"]
    },
    {
        "name": "Adani Ports and Special Economic Zone Ltd",
        "common_name": "Adani Ports",
        "nse_symbol": "ADANIPORTS",
        "bse_code": "532921",
        "exchange": "NSE & BSE",
        "instrument_id": "1418612",
        "provider_symbol": "ADANIPORTS",
        "sector": "Infrastructure",
        "industry": "Ports & Logistics",
        "aliases": ["ADANIPORTS", "ADANI PORTS", "APSEZ"]
    },
    {
        "name": "NTPC Ltd",
        "common_name": "NTPC",
        "nse_symbol": "NTPC",
        "bse_code": "532555",
        "exchange": "NSE & BSE",
        "instrument_id": "1418613",
        "provider_symbol": "NTPC",
        "sector": "Utilities & Power",
        "industry": "Thermal & Renewable Power",
        "aliases": ["NTPC", "NATIONAL THERMAL POWER CORPORATION"]
    },
    {
        "name": "Power Grid Corporation of India Ltd",
        "common_name": "Power Grid",
        "nse_symbol": "POWERGRID",
        "bse_code": "532898",
        "exchange": "NSE & BSE",
        "instrument_id": "1418614",
        "provider_symbol": "POWERGRID",
        "sector": "Utilities & Power",
        "industry": "Power Transmission",
        "aliases": ["POWERGRID", "POWER GRID", "PGCIL"]
    },
    {
        "name": "Asian Paints Ltd",
        "common_name": "Asian Paints",
        "nse_symbol": "ASIANPAINT",
        "bse_code": "500820",
        "exchange": "NSE & BSE",
        "instrument_id": "1418615",
        "provider_symbol": "ASIANPAINT",
        "sector": "Consumer Discretionary",
        "industry": "Paints & Varnishes",
        "aliases": ["ASIANPAINT", "ASIAN PAINTS", "ASIAN PAINT"]
    },
    {
        "name": "Bajaj Auto Ltd",
        "common_name": "Bajaj Auto",
        "nse_symbol": "BAJAJ-AUTO",
        "bse_code": "532977",
        "exchange": "NSE & BSE",
        "instrument_id": "1418616",
        "provider_symbol": "BAJAJ-AUTO",
        "sector": "Automobile",
        "industry": "2 & 3 Wheelers",
        "aliases": ["BAJAJ-AUTO", "BAJAJ AUTO", "BAJAJAUTO"]
    },
    {
        "name": "HCL Technologies Ltd",
        "common_name": "HCL Tech",
        "nse_symbol": "HCLTECH",
        "bse_code": "532281",
        "exchange": "NSE & BSE",
        "instrument_id": "1418617",
        "provider_symbol": "HCLTECH",
        "sector": "Information Technology",
        "industry": "IT Services & Products",
        "aliases": ["HCLTECH", "HCL TECH", "HCL TECHNOLOGIES"]
    },
    {
        "name": "Wipro Ltd",
        "common_name": "Wipro",
        "nse_symbol": "WIPRO",
        "bse_code": "507685",
        "exchange": "NSE & BSE",
        "instrument_id": "1418618",
        "provider_symbol": "WIPRO",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "aliases": ["WIPRO", "WIPRO LTD"]
    },
    {
        "name": "Coal India Ltd",
        "common_name": "Coal India",
        "nse_symbol": "COALINDIA",
        "bse_code": "533278",
        "exchange": "NSE & BSE",
        "instrument_id": "1418619",
        "provider_symbol": "COALINDIA",
        "sector": "Metals & Mining",
        "industry": "Coal Mining",
        "aliases": ["COALINDIA", "COAL INDIA", "CIL"]
    },
    {
        "name": "UltraTech Cement Ltd",
        "common_name": "UltraTech Cement",
        "nse_symbol": "ULTRACEMCO",
        "bse_code": "532538",
        "exchange": "NSE & BSE",
        "instrument_id": "1418620",
        "provider_symbol": "ULTRACEMCO",
        "sector": "Materials",
        "industry": "Cement & Building Materials",
        "aliases": ["ULTRACEMCO", "ULTRATECH", "ULTRATECH CEMENT"]
    },
    {
        "name": "Oil and Natural Gas Corporation Ltd",
        "common_name": "ONGC",
        "nse_symbol": "ONGC",
        "bse_code": "500312",
        "exchange": "NSE & BSE",
        "instrument_id": "1418621",
        "provider_symbol": "ONGC",
        "sector": "Energy",
        "industry": "Oil & Gas Exploration",
        "aliases": ["ONGC", "OIL AND NATURAL GAS CORPORATION"]
    },
    {
        "name": "Hindalco Industries Ltd",
        "common_name": "Hindalco",
        "nse_symbol": "HINDALCO",
        "bse_code": "500440",
        "exchange": "NSE & BSE",
        "instrument_id": "1418622",
        "provider_symbol": "HINDALCO",
        "sector": "Metals & Mining",
        "industry": "Aluminium & Copper",
        "aliases": ["HINDALCO", "HINDALCO INDUSTRIES", "NOVELIS"]
    },
    {
        "name": "JSW Steel Ltd",
        "common_name": "JSW Steel",
        "nse_symbol": "JSWSTEEL",
        "bse_code": "500228",
        "exchange": "NSE & BSE",
        "instrument_id": "1418623",
        "provider_symbol": "JSWSTEEL",
        "sector": "Metals & Mining",
        "industry": "Steel Manufacturing",
        "aliases": ["JSWSTEEL", "JSW STEEL", "JSW"]
    },
    {
        "name": "Nestle India Ltd",
        "common_name": "Nestle",
        "nse_symbol": "NESTLEIND",
        "bse_code": "500790",
        "exchange": "NSE & BSE",
        "instrument_id": "1418624",
        "provider_symbol": "NESTLEIND",
        "sector": "FMCG",
        "industry": "Packaged Foods & Dairy",
        "aliases": ["NESTLEIND", "NESTLE", "NESTLE INDIA", "MAGGI"]
    },
    {
        "name": "Dr. Reddy's Laboratories Ltd",
        "common_name": "Dr Reddy's",
        "nse_symbol": "DRREDDY",
        "bse_code": "500124",
        "exchange": "NSE & BSE",
        "instrument_id": "1418625",
        "provider_symbol": "DRREDDY",
        "sector": "Healthcare & Pharmaceuticals",
        "industry": "Generic Pharmaceuticals",
        "aliases": ["DRREDDY", "DR REDDYS", "DR REDDY", "DR REDDY LABORATORIES"]
    },
    {
        "name": "Cipla Ltd",
        "common_name": "Cipla",
        "nse_symbol": "CIPLA",
        "bse_code": "500087",
        "exchange": "NSE & BSE",
        "instrument_id": "1418626",
        "provider_symbol": "CIPLA",
        "sector": "Healthcare & Pharmaceuticals",
        "industry": "Pharmaceutical Formulations",
        "aliases": ["CIPLA", "CIPLA LTD"]
    },
    {
        "name": "Bharat Electronics Ltd",
        "common_name": "BEL",
        "nse_symbol": "BEL",
        "bse_code": "500049",
        "exchange": "NSE & BSE",
        "instrument_id": "1418627",
        "provider_symbol": "BEL",
        "sector": "Aerospace & Defence",
        "industry": "Defence Electronics",
        "aliases": ["BEL", "BHARAT ELECTRONICS"]
    },
    {
        "name": "Hindustan Aeronautics Ltd",
        "common_name": "HAL",
        "nse_symbol": "HAL",
        "bse_code": "541154",
        "exchange": "NSE & BSE",
        "instrument_id": "1418628",
        "provider_symbol": "HAL",
        "sector": "Aerospace & Defence",
        "industry": "Aircraft & Defence Equipment",
        "aliases": ["HAL", "HINDUSTAN AERONAUTICS"]
    },
    {
        "name": "Trent Ltd",
        "common_name": "Trent",
        "nse_symbol": "TRENT",
        "bse_code": "500251",
        "exchange": "NSE & BSE",
        "instrument_id": "1418629",
        "provider_symbol": "TRENT",
        "sector": "Consumer Discretionary",
        "industry": "Apparel & Retail (Zudio, Westside)",
        "aliases": ["TRENT", "ZUDIO", "WESTSIDE", "TRENT LTD"]
    },
    {
        "name": "Varun Beverages Ltd",
        "common_name": "Varun Beverages",
        "nse_symbol": "VBL",
        "bse_code": "540180",
        "exchange": "NSE & BSE",
        "instrument_id": "1418630",
        "provider_symbol": "VBL",
        "sector": "FMCG",
        "industry": "Beverages & Bottling (PepsiCo)",
        "aliases": ["VBL", "VARUN BEVERAGES", "PEPSI"]
    },
    {
        "name": "Jio Financial Services Ltd",
        "common_name": "Jio Financial",
        "nse_symbol": "JIOFIN",
        "bse_code": "543940",
        "exchange": "NSE & BSE",
        "instrument_id": "1418631",
        "provider_symbol": "JIOFIN",
        "sector": "Financial Services",
        "industry": "Financial Conglomerate & NBFC",
        "aliases": ["JIOFIN", "JIO FINANCIAL", "JIO FINANCIAL SERVICES"]
    },
    {
        "name": "Bajaj Finserv Ltd",
        "common_name": "Bajaj Finserv",
        "nse_symbol": "BAJAJFINSV",
        "bse_code": "532978",
        "exchange": "NSE & BSE",
        "instrument_id": "1418632",
        "provider_symbol": "BAJAJFINSV",
        "sector": "Financial Services",
        "industry": "Insurance & Financial Conglomerate",
        "aliases": ["BAJAJFINSV", "BAJAJ FINSERV"]
    },
    {
        "name": "Avenue Supermarts Ltd",
        "common_name": "DMart",
        "nse_symbol": "DMART",
        "bse_code": "540376",
        "exchange": "NSE & BSE",
        "instrument_id": "1418633",
        "provider_symbol": "DMART",
        "sector": "Consumer Discretionary",
        "industry": "Hypermarkets & Supermarkets",
        "aliases": ["DMART", "D-MART", "AVENUE SUPERMARTS", "RADHAKISHAN DAMANI"]
    },
    {
        "name": "Siemens Ltd",
        "common_name": "Siemens",
        "nse_symbol": "SIEMENS",
        "bse_code": "500550",
        "exchange": "NSE & BSE",
        "instrument_id": "1418634",
        "provider_symbol": "SIEMENS",
        "sector": "Capital Goods",
        "industry": "Heavy Electrical Equipment",
        "aliases": ["SIEMENS", "SIEMENS LTD", "SIEMENS INDIA"]
    },
    {
        "name": "Polycab India Ltd",
        "common_name": "Polycab",
        "nse_symbol": "POLYCAB",
        "bse_code": "542652",
        "exchange": "NSE & BSE",
        "instrument_id": "1418635",
        "provider_symbol": "POLYCAB",
        "sector": "Capital Goods",
        "industry": "Wires, Cables & Fast Moving Electrical Goods",
        "aliases": ["POLYCAB", "POLYCAB INDIA"]
    },
    {
        "name": "Suzlon Energy Ltd",
        "common_name": "Suzlon",
        "nse_symbol": "SUZLON",
        "bse_code": "532667",
        "exchange": "NSE & BSE",
        "instrument_id": "1418636",
        "provider_symbol": "SUZLON",
        "sector": "Renewable Energy",
        "industry": "Wind Turbines & Green Energy",
        "aliases": ["SUZLON", "SUZLON ENERGY"]
    },
    {
        "name": "Yes Bank Ltd",
        "common_name": "Yes Bank",
        "nse_symbol": "YESBANK",
        "bse_code": "532648",
        "exchange": "NSE & BSE",
        "instrument_id": "1418637",
        "provider_symbol": "YESBANK",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "aliases": ["YESBANK", "YES BANK"]
    },
    {
        "name": "Punjab National Bank",
        "common_name": "PNB",
        "nse_symbol": "PNB",
        "bse_code": "532461",
        "exchange": "NSE & BSE",
        "instrument_id": "1418638",
        "provider_symbol": "PNB",
        "sector": "Financial Services",
        "industry": "Public Sector Banking",
        "aliases": ["PNB", "PUNJAB NATIONAL BANK"]
    },
    {
        "name": "Indian Railway Catering and Tourism Corporation Ltd",
        "common_name": "IRCTC",
        "nse_symbol": "IRCTC",
        "bse_code": "542830",
        "exchange": "NSE & BSE",
        "instrument_id": "1418639",
        "provider_symbol": "IRCTC",
        "sector": "Consumer Services",
        "industry": "Rail Ticketing, Tourism & Catering",
        "aliases": ["IRCTC", "RAILWAY"]
    },
    {
        "name": "Indian Railway Finance Corporation Ltd",
        "common_name": "IRFC",
        "nse_symbol": "IRFC",
        "bse_code": "543257",
        "exchange": "NSE & BSE",
        "instrument_id": "1418640",
        "provider_symbol": "IRFC",
        "sector": "Financial Services",
        "industry": "Rail Infrastructure NBFC",
        "aliases": ["IRFC", "INDIAN RAILWAY FINANCE"]
    },
    {
        "name": "Rail Vikas Nigam Ltd",
        "common_name": "RVNL",
        "nse_symbol": "RVNL",
        "bse_code": "542649",
        "exchange": "NSE & BSE",
        "instrument_id": "1418641",
        "provider_symbol": "RVNL",
        "sector": "Infrastructure",
        "industry": "Rail Construction & Infrastructure",
        "aliases": ["RVNL", "RAIL VIKAS NIGAM"]
    }
]

# Build High-Speed In-Memory Lookup Indices
_NSE_INDEX: Dict[str, Dict[str, Any]] = {}
_BSE_INDEX: Dict[str, Dict[str, Any]] = {}
_NAME_INDEX: Dict[str, Dict[str, Any]] = {}
_ALIAS_INDEX: Dict[str, Dict[str, Any]] = {}

def _normalize(s: str) -> str:
    if not s:
        return ""
    # remove punctuation, extra spaces, to uppercase
    return re.sub(r"[^A-Z0-9]", "", s.upper())

def _init_indices():
    for item in CANONICAL_EQUITIES:
        nse = _normalize(item.get("nse_symbol", ""))
        bse = _normalize(item.get("bse_code", ""))
        name = _normalize(item.get("name", ""))
        common = _normalize(item.get("common_name", ""))
        
        if nse:
            _NSE_INDEX[nse] = item
        if bse:
            _BSE_INDEX[bse] = item
        if name:
            _NAME_INDEX[name] = item
        if common:
            _NAME_INDEX[common] = item
            
        for al in item.get("aliases", []):
            norm_al = _normalize(al)
            if norm_al:
                _ALIAS_INDEX[norm_al] = item

_init_indices()

def resolve_symbol(query: str) -> Optional[Dict[str, Any]]:
    """
    Resolve user query to canonical record using exact symbol, BSE code, name, or alias match.
    """
    if not query:
        return None
        
    raw = query.strip()
    norm = _normalize(raw)
    
    # 1. Exact NSE symbol match
    if norm in _NSE_INDEX:
        return _NSE_INDEX[norm]
        
    # 2. Exact BSE code match (e.g. 500325)
    if norm in _BSE_INDEX:
        return _BSE_INDEX[norm]
        
    # 3. Exact Alias match (e.g. ZOMATO -> ETERNAL)
    if norm in _ALIAS_INDEX:
        return _ALIAS_INDEX[norm]
        
    # 4. Exact Name match
    if norm in _NAME_INDEX:
        return _NAME_INDEX[norm]
        
    return None

def search_security_master(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fast local search with relevance ranking across symbols, names, and aliases.
    Supports disambiguation when multiple companies match (e.g. 'Tata', 'Adani').
    """
    q = query.strip()
    if not q:
        return [
            {
                "name": eq["name"],
                "ticker": eq["nse_symbol"] or eq["provider_symbol"],
                "bse_code": eq["bse_code"],
                "url": f"/company/{eq['provider_symbol']}/consolidated/",
                "common_name": eq["common_name"],
                "sector": eq["sector"]
            }
            for eq in CANONICAL_EQUITIES[:8]
        ]
        
    norm_q = _normalize(q)
    matches = []
    seen_symbols = set()
    
    # Score 1: Exact matches
    exact = resolve_symbol(q)
    if exact:
        sym = exact["nse_symbol"]
        matches.append((100, exact))
        seen_symbols.add(sym)
        
    # Score 2: Prefix matches on NSE symbol or common name
    for item in CANONICAL_EQUITIES:
        sym = item.get("nse_symbol", "")
        if sym in seen_symbols:
            continue
            
        score = 0
        norm_sym = _normalize(sym)
        norm_name = _normalize(item.get("name", ""))
        norm_common = _normalize(item.get("common_name", ""))
        bse = item.get("bse_code", "")
        
        if norm_sym.startswith(norm_q):
            score = 90
        elif norm_common.startswith(norm_q):
            score = 85
        elif norm_name.startswith(norm_q):
            score = 80
        elif bse.startswith(norm_q):
            score = 75
        else:
            # Check aliases
            for al in item.get("aliases", []):
                norm_al = _normalize(al)
                if norm_al.startswith(norm_q):
                    score = 70
                    break
                elif norm_q in norm_al:
                    score = 50
                    break
            if score == 0 and (norm_q in norm_name or norm_q in norm_common):
                score = 40
                
        if score > 0:
            matches.append((score, item))
            seen_symbols.add(sym)
            
    # Sort by score descending
    matches.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for _, eq in matches[:limit]:
        results.append({
            "name": eq["name"],
            "ticker": eq["nse_symbol"] or eq["provider_symbol"],
            "bse_code": eq["bse_code"],
            "url": f"/company/{eq['provider_symbol']}/consolidated/",
            "common_name": eq["common_name"],
            "sector": eq["sector"],
            "exchange": eq["exchange"]
        })
        
    return results
