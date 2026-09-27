import os
import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from engine.scraper import search_stocks, get_stock_data, fetch_chart_data
from engine.analyzer import analyze_stock
from engine.report_generator import generate_terminal_html

app = FastAPI(title="Indian Stocks Fundamental Terminal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(STATIC_DIR):
    STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
@app.get("/index.html")
def get_index():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(STATIC_DIR, "index.html"),
        os.path.join(base_dir, "index.html"),
        os.path.join(base_dir, "public", "index.html"),
        os.path.join(base_dir, "static", "index.html")
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Fundamental Terminal Server Ready</h1>")

@app.get("/api/search")
@app.get("/search")
def api_search(q: str = Query("", description="Company name or NSE/BSE ticker")):
    results = search_stocks(q)
    return JSONResponse(content={"results": results})

@app.get("/api/chart")
@app.get("/chart")
def api_chart(
    company_id: str = Query(..., description="Screener company ID"),
    metric: str = Query("Price-DMA50-DMA200-Volume", description="Chart metric dataset"),
    days: int = Query(1095, description="Timeframe in days (30, 180, 365, 1095, 1825, 3652, 10000)")
):
    try:
        data = fetch_chart_data(company_id=company_id, metric=metric, days=days)
        return JSONResponse(content={"success": True, "chart": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chart: {str(e)}")

@app.get("/api/report")
@app.get("/report")
def api_report(
    query: str = Query(..., description="Stock ticker or name"),
    horizon: int = Query(3, description="Investment horizon in years: 1 to 10")
):
    try:
        raw_data = get_stock_data(query)
        analyzed = analyze_stock(raw_data, horizon_years=horizon)
        html_content = generate_terminal_html(analyzed)
        return JSONResponse(content={"success": True, "report": analyzed, "html": html_content})
    except Exception as e:
        err_msg = str(e)
        status = 404 if "not found" in err_msg.lower() else 500
        raise HTTPException(status_code=status, detail=err_msg)

@app.get("/api/download")
@app.get("/download")
def api_download(
    query: str = Query(..., description="Stock ticker or name"),
    horizon: int = Query(3, description="Investment horizon in years: 3, 5, or 10")
):
    try:
        raw_data = get_stock_data(query)
        analyzed = analyze_stock(raw_data, horizon_years=horizon)
        html_content = generate_terminal_html(analyzed)
        ticker = analyzed.get("ticker", "STOCK")
        filename = f"{ticker}_Fundamental_Terminal_Report.html"
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
