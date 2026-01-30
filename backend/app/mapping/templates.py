"""Standardized financial statement templates with XBRL tag mappings.

Each line item maps to a list of US-GAAP XBRL tags in priority order.
The mapper tries each tag and uses the first one that has data.
"""

INCOME_STATEMENT = {
    "Revenue": {
        "tags": [
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
            "SalesRevenueNet",
            "SalesRevenueGoodsNet",
            "SalesRevenueServicesNet",
            "NetRevenues",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Cost of Revenue": {
        "tags": [
            "CostOfRevenue",
            "CostOfGoodsAndServicesSold",
            "CostOfGoodsSold",
            "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",
        ],
        "units": "USD",
        "sign": -1,
    },
    "Gross Profit": {
        "tags": [
            "GrossProfit",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Research & Development": {
        "tags": [
            "ResearchAndDevelopmentExpense",
            "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        ],
        "units": "USD",
        "sign": -1,
    },
    "Selling, General & Administrative": {
        "tags": [
            "SellingGeneralAndAdministrativeExpense",
            "SellingAndMarketingExpense",
            "GeneralAndAdministrativeExpense",
        ],
        "units": "USD",
        "sign": -1,
    },
    "Operating Income": {
        "tags": [
            "OperatingIncomeLoss",
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Interest Expense": {
        "tags": [
            "InterestExpense",
            "InterestExpenseDebt",
            "InterestIncomeExpenseNet",
        ],
        "units": "USD",
        "sign": -1,
    },
    "Pretax Income": {
        "tags": [
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic",
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Net Income": {
        "tags": [
            "NetIncomeLoss",
            "NetIncomeLossAvailableToCommonStockholdersBasic",
            "ProfitLoss",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Diluted Shares Outstanding": {
        "tags": [
            "WeightedAverageNumberOfDilutedSharesOutstanding",
            "CommonStockSharesOutstanding",
            "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
        ],
        "units": "shares",
        "sign": 1,
    },
    "Diluted EPS": {
        "tags": [
            "EarningsPerShareDiluted",
            "EarningsPerShareBasicAndDiluted",
        ],
        "units": "USD/shares",
        "sign": 1,
    },
}

BALANCE_SHEET = {
    "Cash & Equivalents": {
        "tags": [
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsAndShortTermInvestments",
            "Cash",
            "CashEquivalentsAtCarryingValue",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Total Current Assets": {
        "tags": [
            "AssetsCurrent",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Total Assets": {
        "tags": [
            "Assets",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Total Current Liabilities": {
        "tags": [
            "LiabilitiesCurrent",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Total Liabilities": {
        "tags": [
            "Liabilities",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Long-term Debt": {
        "tags": [
            "LongTermDebt",
            "LongTermDebtNoncurrent",
            "LongTermDebtAndCapitalLeaseObligations",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Total Equity": {
        "tags": [
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ],
        "units": "USD",
        "sign": 1,
    },
}

CASH_FLOW = {
    "Net Cash from Operations": {
        "tags": [
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Capital Expenditures": {
        "tags": [
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "PaymentsToAcquireProductiveAssets",
            "PaymentsForCapitalImprovements",
        ],
        "units": "USD",
        "sign": -1,
    },
    "Free Cash Flow": {
        "tags": [],  # Computed: CFO - Capex
        "units": "USD",
        "sign": 1,
        "computed": True,
    },
    "Net Cash from Investing": {
        "tags": [
            "NetCashProvidedByUsedInInvestingActivities",
            "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations",
        ],
        "units": "USD",
        "sign": 1,
    },
    "Net Cash from Financing": {
        "tags": [
            "NetCashProvidedByUsedInFinancingActivities",
            "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations",
        ],
        "units": "USD",
        "sign": 1,
    },
}

ALL_TEMPLATES = {
    "Income_Statement": INCOME_STATEMENT,
    "Balance_Sheet": BALANCE_SHEET,
    "Cash_Flow": CASH_FLOW,
}
