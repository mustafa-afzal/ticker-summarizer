# PitchSheet Agent

A local-first web app that converts a public company's SEC filings into a pitch-ready Excel model. Enter a ticker, pick annual or quarterly, and download a formatted `.xlsx` workbook with standardized financial statements, key ratios, and charts.

## Architecture

```
┌─────────────────────┐     ┌─────────────────────────────────────┐
│   Next.js Frontend  │     │         FastAPI Backend              │
│   (localhost:3000)   │────▶│         (localhost:8000)             │
│                     │     │                                     │
│  / Home             │     │  POST /api/run        → start run   │
│  /run/[id]  Status  │     │  GET  /api/run/{id}   → status/logs │
│  /history   History │     │  GET  /api/run/{id}/download → xlsx │
└─────────────────────┘     │  GET  /api/history    → past runs   │
                            │                                     │
                            │  ┌─ Pipeline Engine ──────────────┐ │
                            │  │ 1. resolve_company(ticker)     │ │
                            │  │ 2. fetch_submissions(cik)      │ │
                            │  │ 3. fetch_companyfacts(cik)     │ │
                            │  │ 4. map_to_templates(facts)     │ │
                            │  │ 5. normalize_periods(stmts)    │ │
                            │  │ 6. compute_metrics(stmts)      │ │
                            │  │ 7. generate_charts(metrics)    │ │
                            │  │ 8. export_xlsx(all)            │ │
                            │  └────────────────────────────────┘ │
                            │                                     │
                            │  ┌─ Data Layer ───────────────────┐ │
                            │  │ SEC EDGAR Client (rate-limited)│ │
                            │  │ SQLite (run history + logs)    │ │
                            │  │ Filesystem cache (JSON + xlsx) │ │
                            │  └────────────────────────────────┘ │
                            └─────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Option 1: Start Script

```bash
chmod +x start.sh
./start.sh
```

This starts both backend (`:8000`) and frontend (`:3000`).

### Option 2: Manual

**Backend:**

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Option 3: Docker Compose

```bash
docker-compose up --build
```

Then open [http://localhost:3000](http://localhost:3000).

## Usage

1. Open `http://localhost:3000`
2. Enter a ticker (e.g., `AAPL`, `MSFT`, `TSLA`)
3. Select **Annual (10-K)** or **Quarterly (10-Q)**
4. Set number of periods (default: 5 years or 12 quarters)
5. Click **Generate Model**
6. Watch the pipeline progress in real time
7. Download the `.xlsx` workbook when complete

## Excel Workbook Format

The generated workbook (`{TICKER}_{10K|10Q}_{DATE}.xlsx`) contains:

| Sheet | Contents |
|-------|----------|
| `Income_Statement` | Revenue, COGS, Gross Profit, R&D, SG&A, Operating Income, Net Income, EPS |
| `Balance_Sheet` | Cash, Current Assets, Total Assets, Current Liabilities, Total Liabilities, Debt, Equity |
| `Cash_Flow` | Operating CF, Capex, Free Cash Flow, Investing CF, Financing CF |
| `Key_Ratios` | Revenue growth, margins, FCF margin, D/E, shares trend, quality flags |
| `Charts` | Revenue, gross margin, operating margin, FCF, shares over time (embedded PNGs) |
| `Run_Metadata` | Run config, data source URLs, timestamps, mapping version, warnings |

Values are formatted with comma separators and negatives in parentheses.

## Data Sources

All data comes from SEC EDGAR's free public APIs:

- **Company lookup:** `https://www.sec.gov/files/company_tickers.json`
- **XBRL facts:** `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
- **Submissions:** `https://data.sec.gov/submissions/CIK{cik}.json`

SEC fair-access compliance:
- `User-Agent: PitchSheetAgent (mafz@umich.edu)`
- Rate limiting: 150ms minimum between requests
- Response caching to disk (keyed by URL hash + ETag)

## Caching

```
cache/
├── {sha256_of_url}.json       # Cached API response
├── {sha256_of_url}.meta.json  # ETag + fetch timestamp
artifacts/
├── {run_id}/
│   ├── charts/                # Generated PNGs
│   └── TICKER_10K_DATE.xlsx   # Final workbook
```

- SEC JSON responses are cached indefinitely (cache is keyed by URL).
- Re-fetches use `If-None-Match` with stored ETags for conditional requests.
- Final workbooks are stored in `artifacts/{run_id}/`.
- Run history and step logs are persisted in `pitchsheet.db` (SQLite).

## XBRL Tag Mapping

The mapper uses a priority list of US-GAAP XBRL tags per line item. For example, Revenue tries:

1. `Revenues`
2. `RevenueFromContractWithCustomerExcludingAssessedTax`
3. `RevenueFromContractWithCustomerIncludingAssessedTax`
4. `SalesRevenueNet`
5. ...and more fallbacks

The first tag with matching data (correct units, correct form, correct period duration) is used. Missing items are left blank with a warning.

## Computed Metrics

- Revenue Growth YoY, CAGR (3Y/5Y)
- Gross Margin, Operating Margin, Net Margin, FCF Margin
- Debt / Equity
- Shares Change YoY (dilution/buyback indicator)
- Quality Flags: alerts for >50% revenue swings or >100% net income changes

## Running Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

Tests use cached fixtures (no SEC API calls). Coverage includes:
- Tag mapping selection and fallback logic
- Period normalization and alignment
- Metrics computation and schema validation
- FCF derivation

## Known Limitations

- **XBRL mapping is not exhaustive.** Some companies use non-standard tags. Missing items produce warnings.
- **Quarterly data (10-Q)** can be inconsistent — some companies report cumulative YTD figures instead of single-quarter values.
- **International companies** using IFRS taxonomy are not supported (US-GAAP only).
- **R&D and SG&A** may be combined under a single tag for some filers.
- **Balance sheet items** are point-in-time; the mapper picks filings based on available period-end dates which may not always align perfectly with income/CF periods.
- **No authentication or multi-user support** — designed for local single-user use.

## Project Structure

```
ticker-summarizer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + endpoints
│   │   ├── config.py            # Paths, SEC config, constants
│   │   ├── models.py            # Pydantic models
│   │   ├── db/database.py       # SQLite operations
│   │   ├── sec/client.py        # SEC EDGAR client + cache
│   │   ├── mapping/
│   │   │   ├── templates.py     # XBRL tag → line item mappings
│   │   │   ├── mapper.py        # Fact extraction + normalization
│   │   │   └── metrics.py       # Ratio + trend computation
│   │   ├── charts/generator.py  # Matplotlib chart generation
│   │   ├── export/workbook.py   # openpyxl Excel export
│   │   └── pipeline/engine.py   # Workflow engine (8-step pipeline)
│   ├── tests/
│   │   ├── conftest.py          # Test fixtures
│   │   └── test_mapping.py      # Unit tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/                 # Next.js pages
│   ├── src/lib/api.ts           # API client
│   └── Dockerfile
├── cache/                       # Cached SEC responses
├── artifacts/                   # Generated workbooks + charts
├── docker-compose.yml
├── start.sh
└── README.md
```

## License

MIT
