"""Internal data assets: code dictionaries and file_metadata.

Ported from the R package's data-raw/codes.R and data-raw/file_metadata.R.
Strings with '?' are verbatim from the R source (mojibake for ≥/≤/curly quotes).
"""

from __future__ import annotations

import polars as pl

# ---------------------------------------------------------------------------
# Code dictionaries  (root__varname → DataFrame[code: Int64, value: Utf8])
# ---------------------------------------------------------------------------

_RCB__INV_CODE: list[tuple[int, str]] = [
    (10, "U.S. Treasury securities"),
    (15, "SBA securities"),
    (17, "Other U.S. Gov't securities and Agency(excluding MBS)"),
    (
        25,
        "Securities fully and unconditionally guaranteed by a GSE (excluding MBS and Farmer Mac securities)",
    ),
    (29, "Municipal securities"),
    (35, "International and multilateral development bank obligations"),
    (40, "Money market instruments:Federal funds sold"),
    (41, "Money market instruments:Negotiable certificates of Deposit"),
    (60, "Money market instruments:Banker acceptances"),
    (52, "Money market instruments:Commercial paper"),
    (50, "Money market instruments:Reverse repurchase agreements"),
    (51, "Money market instruments:Other"),
    (
        62,
        "RMBS fully and unconditionally guaranteed by U.S. government or its agencies",
    ),
    (68, "RMBS fully and unconditionally guaranteed by GSE"),
    (64, "Non-Agency RMBS"),
    (69, "Other RMBS"),
    (
        71,
        "CMBS(excl. Farmer Mac sec.):CMBS fully and unconditionally guaranteed by U.S. government",
    ),
    (
        72,
        "CMBS(excl. Farmer Mac sec.):CMBS fully and unconditionally guaranteed by GSE",
    ),
    (73, "CMBS(excl. Farmer Mac sec.):Non-Agency CMBS"),
    (65, "CMBS(excl. Farmer Mac sec.):Other CMBS"),
    (86, "Farmer Mac guaranteed sec.:Farm and ranch securities (i.e., AMBS)"),
    (87, "Farmer Mac guaranteed sec.:Rural utility securities"),
    (88, "Farmer Mac guaranteed sec.:USDA securities"),
    (66, "Farmer Mac guaranteed sec.:Other Farmer Mac debt securities"),
    (141, "ABS(excl. Farmer Mac securities):Credit card receivables"),
    (142, "ABS(excl. Farmer Mac securities):Home equity loans"),
    (143, "ABS(excl. Farmer Mac securities):Auto Loans"),
    (144, "ABS(excl. Farmer Mac securities):Student Loans"),
    (145, "ABS(excl. Farmer Mac securities):Equipment loans"),
    (146, "ABS(excl. Farmer Mac securities):Manufactured housing loans"),
    (95, "ABS(excl. Farmer Mac securities):Other ABS"),
    (81, "Other types of debt securities:Domestic debt securities"),
    (82, "Other types of debt securities:Foreign debt securities"),
    (
        180,
        "Allowance for Credit Losses on Debt Securities(start collecting on March 2023)",
    ),
    (99, "Total Debt Securities"),
]

_RCB2__AssetCodeRCB2: list[tuple[int, str]] = [
    (110, "Level 1: Cash"),
    (120, "Level 1: Overnight money market instruments"),
    (130, "Level 1: U.S. Government obligations ? 3 years remaining maturity"),
    (140, "Level 1: GSE senior debt ? 60 days remaining maturity"),
    (150, "Level 1: Diversified investments funds comprised of Level 1 securities"),
    (160, "Level 1: Subtotal"),
    (210, "Level 2: U.S. Government obligations > 3 years remaining maturity"),
    (220, "Level 2: MBS fully and explicitly guaranteed (both P&I) by U.S. Government"),
    (
        230,
        "Level 2: Diversified investment funds comprised of Levels 1 and 2 securities",
    ),
    (240, "Level 2: Subtotal"),
    (310, "Level 3: GSE senior debt > 60 days remaining maturity"),
    (320, "Level 3: MBS fully guaranteed (both P&I) by a GSE"),
    (330, "Level 3: Money market instruments ? 90 day remaining maturity"),
    (
        340,
        "Level 3: Diversified investments funds comprised of Levels 1, 2, and 3 securities",
    ),
    (350, "Level 3: Subtotal"),
    (410, "Supplemental liquidity buffer"),
    (510, "Total"),
]

_RCB3__DebtMaturityCode: list[tuple[int, str]] = [
    (110, "<8 days"),
    (120, "8-15 days"),
    (130, "16-30 days"),
    (140, "31-45 days"),
    (150, "46-90 days"),
    (160, "91-120 days"),
    (170, "121-150 days"),
    (180, ">150 days"),
    (185, "Unamortized discount or premium and unamortized debt issuance costs"),
    (190, "Total"),
]

_RCF__LOANSTATUS: list[tuple[int, str]] = [
    (10, "Accruing"),
    (20, "Formally restructured accruing"),
    (54, "Nonaccrual: Cash basis"),
    (56, "Nonaccrual: Other"),
    (60, "Total"),
    (80, "Number of Loans"),
]

_RCF1__LOANSTATUS: list[tuple[int, str]] = [
    (100, "Production Agriculture: Real Estate"),
    (105, "Production Agriculture: Production and Intermediate Term"),
    (110, "Agribusiness"),
    (115, "Communication"),
    (120, "Energy"),
    (125, "Water/Waste disposal"),
    (130, "Rural residential real estate"),
    (135, "International"),
    (140, "Lease receivables"),
    (145, "Direct loans to associations"),
    (150, "Discounted loans to OFIs"),
    (152, "Other loans"),
    (155, "Total"),
]

_RCI2B__DerivCode: list[tuple[int, str]] = [
    (10, "Cleared Derivatives (Notional): Swap contracts"),
    (20, "Cleared Derivatives (Notional): Option contracts ? purchased"),
    (30, "Cleared Derivatives (Notional): Option contracts ? written (sold)"),
    (40, "Cleared Derivatives (Notional): Futures contracts"),
    (50, "Cleared Derivatives (Notional): Total cleared derivative contracts"),
    (60, "Non-cleared Derivatives (Notional): Swap contracts"),
    (70, "Non-cleared Derivatives (Notional): Option contracts ? purchased"),
    (80, "Non-cleared Derivatives (Notional): Option contracts ? written (sold)"),
    (90, "Non-cleared Derivatives (Notional): Forward contracts"),
    (100, "Non-cleared Derivatives (Notional): Total non-cleared derivative contracts"),
    (110, "Total Derivative Contracts (Notional) (sum of 3(e) and 4(e))"),
    (120, "Derivatives included in Line 5 that are on behalf of customers (Notional)"),
    (130, "Cleared Derivatives (Fair Value): Swap contracts"),
    (140, "Cleared Derivatives (Fair Value): Option contracts ? purchased"),
    (150, "Cleared Derivatives (Fair Value): Option contracts ? written (sold)"),
    (160, "Cleared Derivatives (Fair Value): Futures contracts"),
    (170, "Cleared Derivatives (Fair Value): Total cleared derivative contracts"),
    (180, "Non-cleared Derivatives (Fair Value): Swap contracts"),
    (190, "Non-cleared Derivatives (Fair Value): Option contracts ? purchased"),
    (200, "Non-cleared Derivatives (Fair Value): Option contracts ? written (sold)"),
    (210, "Non-cleared Derivatives (Fair Value): Forward contracts"),
    (
        220,
        "Non-cleared Derivatives (Fair Value): Total non-cleared derivative contracts",
    ),
    (230, "Total derivative contracts (Fair Value ? sum of 7(e) and 8(e))"),
]

_RCI2C__ExposureCode: list[tuple[int, str]] = [
    (
        10,
        "Institution?s Exposure to Counterparties after netting: Derivative contracts in a gain position",
    ),
    (
        20,
        "Institution?s Exposure to Counterparties after netting: Initial margin posted by counterparties - Cash",
    ),
    (
        30,
        "Institution?s Exposure to Counterparties after netting: Initial margin posted by counterparties - Securities",
    ),
    (
        40,
        "Institution?s Exposure to Counterparties after netting: Variation margin or settlement payments posted by counterparties - Cash",
    ),
    (
        50,
        "Institution?s Exposure to Counterparties after netting: Variation margin or settlement payments posted by counterparties - Securities",
    ),
    (
        70,
        "Institution?s Exposure to Counterparties after netting: Institution?s exposure to counterparties (item 10(a) minus (items 10(b) through 10(e)))",
    ),
    (
        80,
        "Counterparties? Exposure to Institution after netting: Derivative contracts in a loss position",
    ),
    (
        90,
        "Counterparties? Exposure to Institution after netting: Initial margin posted by counterparties - Cash",
    ),
    (
        100,
        "Counterparties? Exposure to Institution after netting: Initial margin posted by counterparties - Securities",
    ),
    (
        110,
        "Counterparties? Exposure to Institution after netting: Variation margin or settlement payments posted by counterparties - Cash",
    ),
    (
        120,
        "Counterparties? Exposure to Institution after netting: Variation margin or settlement payments posted by counterparties - Securities",
    ),
    (
        140,
        "Counterparties? Exposure to Institution after netting: Counterparty exposure to institution (item 11(a) minus (items 11(b) through 11(e)))",
    ),
]

_RCI2D__DerivRMCode: list[tuple[int, str]] = [
    (10, "Cleared derivatives: Interest rate risk"),
    (20, "Cleared derivatives: Foreign exchange"),
    (30, "Cleared derivatives: Credit"),
    (40, "Cleared derivatives: Others"),
    (50, "Cleared derivatives: Total cleared"),
    (60, "Non-cleared derivatives: Interest rate risk"),
    (70, "Non-cleared derivatives: Foreign exchange"),
    (80, "Non-cleared derivatives: Credit"),
    (90, "Non-cleared derivatives: Others"),
    (100, "Non-cleared derivatives: Total non-cleared"),
    (110, "Total derivative contracts (sum 12(e) + 13(e))"),
]

_RCO__ASSET_CODE: list[tuple[int, str]] = [
    (10, "Loan participations: Purchased"),
    (20, "Loan participations: Sold"),
    (30, "Similar entity transactions: Acquired On Interest Held"),
    (40, "Similar entity transactions: Sold"),
    (50, "Lease interest purchases and sales: Purchased"),
    (60, "Lease interest purchases and sales: Sold"),
    (70, "Other asset purchases and sales: Purchased"),
    (80, "Other asset purchases and sales: Sold"),
    (90, "Participations in Notes Receivables: Purchased"),
    (100, "Participations in Notes Receivables: Sold"),
    (110, "Asset Purchases and Sales - Certain Pool Items: Purchased"),
    (120, "Asset Purchases and Sales - Certain Pool Items: Sold"),
]

_RCR3__RegCapCode: list[tuple[int, str]] = [
    (100, "Purchased Statutory Required Stock"),
    (210, "Purchased Other Required Stock < 5 years"),
    (220, "Purchased Other Required Stock >= 5 years but < 7 years"),
    (230, "Purchased Other Required Stock >= 7 years"),
    (310, "Allocated Stock < 5 years"),
    (320, "Allocated Stock >= 5 years but < 7 years"),
    (330, "Allocated Stock >= 7 years"),
    (410, "Qualified Allocated Surplus < 5 years"),
    (420, "Qualified Allocated Surplus >= 5 years but < 7 years"),
    (430, "Qualified Allocated Surplus >= 7 years"),
    (510, "Nonqualified Allocated Surplus < 5 years"),
    (520, "Nonqualified Allocated Surplus >= 5 years but < 7 years"),
    (530, "Nonqualified Allocated Surplus >= 7 years"),
    (540, "Not subject to redemption or revolvement"),
    (600, "Total Common Cooperative Equities"),
]

_RCR7__RegCapCode: list[tuple[int, str]] = [
    (100, "Cash and cash balances due from depository institutions or Federal Reserve"),
    (210, "Federal funds sold"),
    (220, "Securities purchased under agreement to resell"),
    (310, "Securities Held-to-Maturity"),
    (320, "Securities Available-for-Sale"),
    (410, "On-balance sheet securitization exposures Held-to-Maturity"),
    (420, "On-balance sheet securitization Available-for-Sale"),
    (430, "On-balance sheet securitization All other"),
    (510, "Loans and leases, net of unearned income Retail exposures"),
    (520, "Loans and leases, net of unearned income Wholesale exposures"),
    (600, "Loans & Leases Held for Sale"),
    (700, "All other assets"),
    (800, "Total On-Balance Sheet Exposures"),
    (900, "Financial standby letters of credit"),
    (
        1000,
        "Performance standby letters of credit and transaction-related contingent items",
    ),
    (
        1110,
        "Commercial and similar letters of credit Original maturity of 14 months or less",
    ),
    (
        1120,
        "Commercial and similar letters of credit Original maturity exceeding 14 months",
    ),
    (1200, "Repo-styled transactions"),
    (1310, "Unused commitments Original maturity of 14 months or less"),
    (1320, "Unused commitments Original maturity exceeding 14 months"),
    (1330, "Unused commitments Original Wholesale exposures"),
    (1400, "Over-the-counter derivatives"),
    (1500, "Centrally cleared derivatives"),
    (1600, "Unsettled Transactions"),
    (1700, "All other off-balance sheet exposures"),
    (1800, "Total Off-Balance Sheet Exposures"),
    (1900, "Total On- and Off-Balance Sheet Exposures"),
    (2000, "Risk Weight Factor"),
    (2100, "Risk Weighted Assets before deductions"),
]

_RID__CAP_CODE: list[tuple[int, str]] = [
    (10, "Beginning balance"),
    (25, "Prior Period & Accounting Adjustments"),
    (35, "Net Income"),
    (45, "Other Comprehensive Income"),
    (80, "Patronage Distributions"),
    (70, "Dividends"),
    (75, "Stock Issued"),
    (85, "Stock Retired"),
    (95, "Paid-in Capital Adjustments"),
    (105, "Allocated Equity Retired"),
    (120, "Other"),
    (130, "Ending balance"),
]

_RIE1__ACLCode: list[tuple[int, str]] = [
    (10, "Allowances for Credit Losses, beginning of period"),
    (
        20,
        "Net increase (or decrease (-)) resulting from provision for credit losses (current period)",
    ),
    (30, "Less: Charge-offs"),
    (40, "Less: Write-downs arising from transfer of financial assets"),
    (50, "Recoveries"),
    (60, "Other"),
    (70, "Allowances for credit losses, end of period"),
]

# Registry: name → raw list of (code, value) tuples
_CODE_DICT_REGISTRY: dict[str, list[tuple[int, str]]] = {
    "RCB__INV_CODE": _RCB__INV_CODE,
    "RCB2__AssetCodeRCB2": _RCB2__AssetCodeRCB2,
    "RCB3__DebtMaturityCode": _RCB3__DebtMaturityCode,
    "RCF__LOANSTATUS": _RCF__LOANSTATUS,
    "RCF1__LOANSTATUS": _RCF1__LOANSTATUS,
    "RCI2B__DerivCode": _RCI2B__DerivCode,
    "RCI2C__ExposureCode": _RCI2C__ExposureCode,
    "RCI2D__DerivRMCode": _RCI2D__DerivRMCode,
    "RCO__ASSET_CODE": _RCO__ASSET_CODE,
    "RCR3__RegCapCode": _RCR3__RegCapCode,
    "RCR7__RegCapCode": _RCR7__RegCapCode,
    "RID__CAP_CODE": _RID__CAP_CODE,
    "RIE1__ACLCode": _RIE1__ACLCode,
}


def _make_code_df(pairs: list[tuple[int, str]]) -> pl.DataFrame:
    return pl.DataFrame(pairs, schema={"code": pl.Int64, "value": pl.String}, orient="row")


def get_code_df(registry_key: str) -> pl.DataFrame:
    """Return a DataFrame[code: Int64, value: Utf8] for *registry_key*."""
    return _make_code_df(_CODE_DICT_REGISTRY[registry_key])


# ---------------------------------------------------------------------------
# file_metadata  (36-row lookup: file_prefix → description)
# ---------------------------------------------------------------------------

_FILE_METADATA_ROWS: list[tuple[str, str]] = [
    ("INST", "Institution Information"),
    ("RC", "Balance Sheet"),
    ("RC1", "Memoranda"),
    (
        "RCB",
        "Debt Securities (excluding investments in Farm Credit institutions and diversified investment funds)",
    ),
    ("RCB2", "Assets Held for Liquidity (Applicable to banks only)"),
    (
        "RCB3",
        "Demands on Liquidity (Applicable to banks and block-funded associations only)",
    ),
    ("RCB4", "Equity Securities"),
    ("RCB5", "Investments Memoranda"),
    ("RCF", "Performance of Loans, Notes, Sales Contracts, and Leases"),
    (
        "RCF1",
        "Performance of Loans, Notes, Sales Contracts, and Leases Loan Performance by Loan Type",
    ),
    ("RCG", "Average Daily Amounts for the Quarter"),
    ("RCH", "Reconcilement of Net Worth"),
    (
        "RCI1",
        "Off-Balance Sheet Commitments, Contingencies, and Other Items (Excluding Derivatives)",
    ),
    (
        "RCI2A",
        "Off-Balance Sheet Derivative Contracts: Credit Derivative Contracts Section",
    ),
    (
        "RCI2B",
        "Off-Balance Sheet Derivative Contracts: Derivative Contracts (exclude credit derivatives) Section",
    ),
    (
        "RCI2C",
        "Off-Balance Sheet Derivative Contracts: Fair Value Counterparty Exposures Including Impact of Netting Agreements)",
    ),
    (
        "RCI2D",
        "Off-Balance Sheet Derivative Contracts: Derivatives by Remaining Maturity (Notional) Section",
    ),
    (
        "RCK",
        "Accrual Loan Activity Reconcilement for Loans, Leases, Notes Receivable (excluding Intra-System Loan), and Sales Contracts",
    ),
    ("RCL", "Nonaccrual Loan Activity Reconcilement"),
    ("RCM", "Other-Property-Owned (Net of Depreciation) Activity Reconcilement"),
    ("RCO", "Asset Purchase and Sales"),
    ("RCR1", "Summary - Regulatory Capital"),
    ("RCR2", "Summary - Regulatory Capital Ratios"),
    ("RCR3", "Common Cooperative Equities"),
    ("RCR4", "Tier 1/Tier 2 Numerator"),
    ("RCR5", "Miscellaneous Tier 1/Tier 2 Calculations"),
    ("RCR6", "Permanent Capital Numerator"),
    ("RCR7", "Risk-Weighted Assets (RWAs)"),
    ("RI", "Income and Comprehensive Income Statement"),
    ("RIA", "Operating Income"),
    ("RIB", "Net Gains and Losses"),
    ("RIC", "Operating Expenses"),
    ("RIC1", "Other Noninterest Expenses"),
    ("RID", "Changes in Net Worth"),
    ("RIE1", "Changes in Allowances for Credit Losses"),
    (
        "RIE2",
        "Analysis of Allowance for Credit Losses—Loans, Notes, Sales Contracts, and Leases",
    ),
]

file_metadata: pl.DataFrame = pl.DataFrame(
    {
        "file_prefix": [r[0] for r in _FILE_METADATA_ROWS],
        "description": [r[1] for r in _FILE_METADATA_ROWS],
    }
)
