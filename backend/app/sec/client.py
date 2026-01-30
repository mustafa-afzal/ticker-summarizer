"""SEC EDGAR client with caching and rate limiting."""

import asyncio
import hashlib
import json
import ssl
import time
from pathlib import Path
from typing import Optional

import aiohttp
import certifi

from app.config import CACHE_DIR, SEC_BASE_URL, SEC_USER_AGENT, SEC_RATE_LIMIT_DELAY

_ssl_context = ssl.create_default_context(cafile=certifi.where())

_last_request_time = 0.0
_lock = asyncio.Lock()


def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _cache_path(url: str) -> Path:
    return CACHE_DIR / f"{_cache_key(url)}.json"


def _meta_path(url: str) -> Path:
    return CACHE_DIR / f"{_cache_key(url)}.meta.json"


async def _rate_limit():
    global _last_request_time
    async with _lock:
        now = time.monotonic()
        elapsed = now - _last_request_time
        if elapsed < SEC_RATE_LIMIT_DELAY:
            await asyncio.sleep(SEC_RATE_LIMIT_DELAY - elapsed)
        _last_request_time = time.monotonic()


async def fetch_json(url: str, use_cache: bool = True) -> dict:
    """Fetch JSON from SEC with caching and rate limiting."""
    cache = _cache_path(url)
    meta = _meta_path(url)

    if use_cache and cache.exists():
        return json.loads(cache.read_text())

    await _rate_limit()

    headers = {
        "User-Agent": SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/json",
    }

    # Check etag for conditional request
    etag = None
    if meta.exists():
        meta_data = json.loads(meta.read_text())
        etag = meta_data.get("etag")
        if etag:
            headers["If-None-Match"] = etag

    connector = aiohttp.TCPConnector(ssl=_ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 304 and cache.exists():
                return json.loads(cache.read_text())

            if resp.status != 200:
                raise Exception(
                    f"SEC API returned {resp.status} for {url}: {await resp.text()}"
                )

            data = await resp.json(content_type=None)

            # Cache response
            cache.write_text(json.dumps(data))

            # Cache metadata
            meta_info = {"url": url, "fetched_at": time.time()}
            if "ETag" in resp.headers:
                meta_info["etag"] = resp.headers["ETag"]
            meta.write_text(json.dumps(meta_info))

            return data


async def load_company_tickers() -> dict[str, dict]:
    """Load and cache the SEC company tickers mapping.

    Returns dict keyed by uppercase ticker -> {cik_str, title, ticker}.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    raw = await fetch_json(url)

    result = {}
    for entry in raw.values():
        ticker = entry.get("ticker", "").upper()
        cik = str(entry.get("cik_str", entry.get("cik", "")))
        result[ticker] = {
            "cik_str": cik.zfill(10),
            "title": entry.get("title", ""),
            "ticker": ticker,
        }
    return result


async def resolve_cik(ticker: str) -> dict:
    """Resolve ticker to CIK info. Returns {cik_str, title, ticker}."""
    tickers = await load_company_tickers()
    info = tickers.get(ticker.upper())
    if not info:
        raise ValueError(f"Ticker '{ticker}' not found in SEC company tickers")
    return info


async def fetch_company_facts(cik: str) -> dict:
    """Fetch XBRL company facts for a CIK."""
    cik_padded = cik.zfill(10)
    url = f"{SEC_BASE_URL}/api/xbrl/companyfacts/CIK{cik_padded}.json"
    return await fetch_json(url)


async def fetch_submissions(cik: str) -> dict:
    """Fetch filing submissions metadata for a CIK."""
    cik_padded = cik.zfill(10)
    url = f"{SEC_BASE_URL}/submissions/CIK{cik_padded}.json"
    return await fetch_json(url)
