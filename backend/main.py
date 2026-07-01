import asyncio
import pathlib
from concurrent.futures import ThreadPoolExecutor
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import data_utils

app = FastAPI(title="Market Data Analysis API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_pool = ThreadPoolExecutor(max_workers=16)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    return {
        "indices": data_utils.INDICES,
        "stocks": data_utils.NSE_STOCKS,
        "global": data_utils.GLOBAL_INDICES,
    }


@app.get("/api/quote/{ticker:path}")
def quote(ticker: str):
    data = data_utils.get_quote(ticker)
    if not data:
        raise HTTPException(status_code=404, detail="No data")
    return data


class BatchRequest(BaseModel):
    tickers: List[str]


@app.post("/api/quotes/batch")
async def batch_quotes(req: BatchRequest):
    loop = asyncio.get_event_loop()

    async def _one(ticker: str):
        result = await loop.run_in_executor(_pool, data_utils.get_quote, ticker)
        return ticker, result

    results = await asyncio.gather(*[_one(t) for t in req.tickers])
    return {t: d for t, d in results if d}


@app.get("/api/ohlcv/{ticker:path}")
def ohlcv(ticker: str, interval: str = "1d", period: str = "6mo"):
    df = data_utils.get_ohlcv(ticker, interval=interval, period=period)
    if df.empty:
        raise HTTPException(status_code=404, detail="No OHLCV data")
    df = data_utils.compute_indicators(df)
    return data_utils.df_to_chart_data(df, interval)


@app.get("/api/news")
def news():
    return data_utils.fetch_news()


# --- Serve React SPA (after all API routes) ---
STATIC_DIR = pathlib.Path("/app/static")
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="spa")
