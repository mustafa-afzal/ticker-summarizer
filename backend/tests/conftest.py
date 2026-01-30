import json
import os
import pytest
from pathlib import Path

# Set up test environment before importing app modules
os.environ["PITCHSHEET_TEST"] = "1"

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def aapl_company_facts():
    """Minimal AAPL company facts fixture for testing."""
    return {
        "cik": 320193,
        "entityName": "Apple Inc.",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "label": "Revenues",
                    "units": {
                        "USD": [
                            {"end": "2020-09-26", "val": 274515000000, "form": "10-K", "start": "2019-09-29"},
                            {"end": "2021-09-25", "val": 365817000000, "form": "10-K", "start": "2020-09-27"},
                            {"end": "2022-09-24", "val": 394328000000, "form": "10-K", "start": "2021-09-26"},
                            {"end": "2023-09-30", "val": 383285000000, "form": "10-K", "start": "2022-09-25"},
                            {"end": "2024-09-28", "val": 391035000000, "form": "10-K", "start": "2023-10-01"},
                        ]
                    }
                },
                "CostOfGoodsAndServicesSold": {
                    "label": "Cost of Goods and Services Sold",
                    "units": {
                        "USD": [
                            {"end": "2020-09-26", "val": 169559000000, "form": "10-K", "start": "2019-09-29"},
                            {"end": "2021-09-25", "val": 212981000000, "form": "10-K", "start": "2020-09-27"},
                            {"end": "2022-09-24", "val": 223546000000, "form": "10-K", "start": "2021-09-26"},
                            {"end": "2023-09-30", "val": 214137000000, "form": "10-K", "start": "2022-09-25"},
                            {"end": "2024-09-28", "val": 210352000000, "form": "10-K", "start": "2023-10-01"},
                        ]
                    }
                },
                "GrossProfit": {
                    "label": "Gross Profit",
                    "units": {
                        "USD": [
                            {"end": "2020-09-26", "val": 104956000000, "form": "10-K", "start": "2019-09-29"},
                            {"end": "2021-09-25", "val": 152836000000, "form": "10-K", "start": "2020-09-27"},
                            {"end": "2022-09-24", "val": 170782000000, "form": "10-K", "start": "2021-09-26"},
                            {"end": "2023-09-30", "val": 169148000000, "form": "10-K", "start": "2022-09-25"},
                            {"end": "2024-09-28", "val": 180683000000, "form": "10-K", "start": "2023-10-01"},
                        ]
                    }
                },
                "OperatingIncomeLoss": {
                    "label": "Operating Income (Loss)",
                    "units": {
                        "USD": [
                            {"end": "2020-09-26", "val": 66288000000, "form": "10-K", "start": "2019-09-29"},
                            {"end": "2021-09-25", "val": 108949000000, "form": "10-K", "start": "2020-09-27"},
                            {"end": "2022-09-24", "val": 119437000000, "form": "10-K", "start": "2021-09-26"},
                            {"end": "2023-09-30", "val": 114301000000, "form": "10-K", "start": "2022-09-25"},
                            {"end": "2024-09-28", "val": 123216000000, "form": "10-K", "start": "2023-10-01"},
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "label": "Net Income (Loss)",
                    "units": {
                        "USD": [
                            {"end": "2020-09-26", "val": 57411000000, "form": "10-K", "start": "2019-09-29"},
                            {"end": "2021-09-25", "val": 94680000000, "form": "10-K", "start": "2020-09-27"},
                            {"end": "2022-09-24", "val": 99803000000, "form": "10-K", "start": "2021-09-26"},
                            {"end": "2023-09-30", "val": 96995000000, "form": "10-K", "start": "2022-09-25"},
                            {"end": "2024-09-28", "val": 93736000000, "form": "10-K", "start": "2023-10-01"},
                        ]
                    }
                },
                "Assets": {
                    "label": "Assets",
                    "units": {
                        "USD": [
                            {"end": "2020-09-26", "val": 323888000000, "form": "10-K"},
                            {"end": "2021-09-25", "val": 351002000000, "form": "10-K"},
                            {"end": "2022-09-24", "val": 352755000000, "form": "10-K"},
                            {"end": "2023-09-30", "val": 352583000000, "form": "10-K"},
                            {"end": "2024-09-28", "val": 364980000000, "form": "10-K"},
                        ]
                    }
                },
                "StockholdersEquity": {
                    "label": "Stockholders' Equity",
                    "units": {
                        "USD": [
                            {"end": "2020-09-26", "val": 65339000000, "form": "10-K"},
                            {"end": "2021-09-25", "val": 63090000000, "form": "10-K"},
                            {"end": "2022-09-24", "val": 50672000000, "form": "10-K"},
                            {"end": "2023-09-30", "val": 62146000000, "form": "10-K"},
                            {"end": "2024-09-28", "val": 56950000000, "form": "10-K"},
                        ]
                    }
                },
                "NetCashProvidedByUsedInOperatingActivities": {
                    "label": "Net Cash from Operations",
                    "units": {
                        "USD": [
                            {"end": "2020-09-26", "val": 80674000000, "form": "10-K", "start": "2019-09-29"},
                            {"end": "2021-09-25", "val": 104038000000, "form": "10-K", "start": "2020-09-27"},
                            {"end": "2022-09-24", "val": 122151000000, "form": "10-K", "start": "2021-09-26"},
                            {"end": "2023-09-30", "val": 110543000000, "form": "10-K", "start": "2022-09-25"},
                            {"end": "2024-09-28", "val": 118254000000, "form": "10-K", "start": "2023-10-01"},
                        ]
                    }
                },
                "PaymentsToAcquirePropertyPlantAndEquipment": {
                    "label": "Capital Expenditures",
                    "units": {
                        "USD": [
                            {"end": "2020-09-26", "val": 7309000000, "form": "10-K", "start": "2019-09-29"},
                            {"end": "2021-09-25", "val": 11085000000, "form": "10-K", "start": "2020-09-27"},
                            {"end": "2022-09-24", "val": 10708000000, "form": "10-K", "start": "2021-09-26"},
                            {"end": "2023-09-30", "val": 10959000000, "form": "10-K", "start": "2022-09-25"},
                            {"end": "2024-09-28", "val": 9959000000, "form": "10-K", "start": "2023-10-01"},
                        ]
                    }
                },
                "WeightedAverageNumberOfDilutedSharesOutstanding": {
                    "label": "Diluted Shares",
                    "units": {
                        "shares": [
                            {"end": "2020-09-26", "val": 17528214000, "form": "10-K", "start": "2019-09-29"},
                            {"end": "2021-09-25", "val": 16864919000, "form": "10-K", "start": "2020-09-27"},
                            {"end": "2022-09-24", "val": 16325819000, "form": "10-K", "start": "2021-09-26"},
                            {"end": "2023-09-30", "val": 15812547000, "form": "10-K", "start": "2022-09-25"},
                            {"end": "2024-09-28", "val": 15408095000, "form": "10-K", "start": "2023-10-01"},
                        ]
                    }
                },
                "EarningsPerShareDiluted": {
                    "label": "Diluted EPS",
                    "units": {
                        "USD/shares": [
                            {"end": "2020-09-26", "val": 3.28, "form": "10-K", "start": "2019-09-29"},
                            {"end": "2021-09-25", "val": 5.61, "form": "10-K", "start": "2020-09-27"},
                            {"end": "2022-09-24", "val": 6.11, "form": "10-K", "start": "2021-09-26"},
                            {"end": "2023-09-30", "val": 6.13, "form": "10-K", "start": "2022-09-25"},
                            {"end": "2024-09-28", "val": 6.08, "form": "10-K", "start": "2023-10-01"},
                        ]
                    }
                },
            }
        }
    }


@pytest.fixture
def sample_period_dates():
    return ["2020-09-26", "2021-09-25", "2022-09-24", "2023-09-30", "2024-09-28"]
