"""Turn the raw cafe sales export into an analysis-ready table.

Session-01 shared template. Copy it into your own
learners/<name>/exercises/ folder before changing anything -- the copy in
exercises/ stays as the starting point for everyone.

Run it directly to write the cleaned CSV and print a data-quality report:

    python exercises/session-01/cafe_sales_data_cleanup.py

Or import the pieces from another script:

    from cafe_sales_data_cleanup import clean, load_raw
"""

import pandas as pd
import numpy as np

from pathlib import Path


def find_repo_root() -> Path:
    """Walk up from this file until the folder containing .git turns up.

    Preferred over a fixed Path(__file__).parents[N] because N silently becomes
    wrong the moment the file is moved to a different depth -- which is exactly
    what happened when this exercise moved into learners/prince/exercises/.
    Searching for a landmark instead means the path survives the next move too.
    """
    for candidate in Path(__file__).resolve().parents:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError("repo root not found -- is this still inside the git repo?")


REPO_ROOT = find_repo_root()
# Shared reference material lives in resources/, per the README layout.
DATASETS = REPO_ROOT / "resources" / "datasets"
OUTPUT_DIR = REPO_ROOT / "output"

RAW_CSV = DATASETS / "dirty_cafe_sales.csv"
CLEAN_CSV = OUTPUT_DIR / "cafe_sales_cleaned.csv"

# Strings the source system writes instead of leaving a cell blank. pandas
# cannot know these mean "missing", so a plain read_csv() keeps them as text --
# which is exactly what drags a whole numeric column down to str dtype.
SENTINELS = ["ERROR", "UNKNOWN"]

NUMERIC_COLUMNS = ["quantity", "price_per_unit", "total_spent"]
CATEGORICAL_COLUMNS = ["item", "payment_method", "location"]

# Tolerance for comparing money. Never test currency with == -- 0.1 + 0.2
# does not equal 0.3 in floating point.
MONEY_TOLERANCE = 0.01


def load_raw() -> pd.DataFrame:
    """Read the raw CSV and normalise the column names to snake_case.

    The source header says "Price Per Unit"; quoting that everywhere is
    painful, so it becomes price_per_unit. The .str calls run on the column
    Index itself -- an Index exposes the same .str accessor a Series does.
    """
    df = pd.read_csv(RAW_CSV)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df


def sentinels_to_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Replace the "ERROR"/"UNKNOWN" placeholder strings with real NaN.

    The most important step in the file: until these become NaN, pandas treats
    them as ordinary text, so isna() under-reports the missing data and
    describe() shows top/freq instead of mean/std.
    """
    return df.replace(SENTINELS, None)


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert the text columns into the dtypes they should have had.

    errors="coerce" is the argument that matters -- anything unparseable
    becomes NaN instead of raising, which makes the conversion a *cleaning*
    step rather than something that explodes on the first bad row.
    """
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    return df


def build_price_lookup(df: pd.DataFrame) -> pd.Series:
    """Learn each item's price from the rows that are already complete.

    Every item on this menu has exactly one price, so the price list can be
    derived from the data instead of hardcoded -- if the cafe reprices, the
    lookup follows automatically. .median() collapses the identical values and
    shrugs off a stray typo far better than .mean() would.
    """
    complete = df.dropna(subset=["item", "price_per_unit"])
    return complete.groupby("item")["price_per_unit"].median()


def impute_price_from_item(df: pd.DataFrame, price_lookup: pd.Series) -> pd.DataFrame:
    """Fill a missing price_per_unit using the item name.

    .map() translates each item into its price, then .fillna() applies those
    values *only* where price_per_unit is currently empty, so real data is
    never overwritten.
    """
    df["price_per_unit"] = df["price_per_unit"].fillna(df["item"].map(price_lookup))
    return df


def impute_numeric_identity(df: pd.DataFrame) -> pd.DataFrame:
    """Rebuild a missing number from the other two.

    quantity * price_per_unit == total_spent holds on every complete row in
    this file (integrity_violations() re-checks it after the fact), so the
    identity is a trusted rule we can impute *with*, not merely validate
    against. Whenever two of the three are known, the third is arithmetic.

    One pass is enough: every rule needs two known values, and no rule's
    output is another rule's missing input.
    """
    quantity, price, total = df["quantity"], df["price_per_unit"], df["total_spent"]

    # Swapping 0 for NaN before dividing keeps a zero quantity or price from
    # producing inf. Neither is 0 in this dataset, but the next export might be.
    safe_quantity = quantity.replace(0, np.nan)
    safe_price = price.replace(0, np.nan)

    df["total_spent"] = total.fillna(quantity * price)
    df["quantity"] = quantity.fillna(total / safe_price)
    df["price_per_unit"] = price.fillna(total / safe_quantity)

    # Recomputed money can carry float noise (4.199999999999999); pin it back
    # to cents.
    for column in NUMERIC_COLUMNS:
        df[column] = df[column].round(2)
    return df


def impute_item_from_price(df: pd.DataFrame, price_lookup: pd.Series) -> pd.DataFrame:
    """Recover a missing item name from its price -- where that is unambiguous.

    Reversing the lookup only works for prices belonging to a single item:
    Cookie (1.0), Tea (1.5), Coffee (2.0) and Salad (5.0) qualify, while 3.0
    (Cake or Juice) and 4.0 (Sandwich or Smoothie) would be guesses we refuse
    to make. Filtering to size == 1 keeps the honest half.
    """
    items_per_price = price_lookup.reset_index().groupby("price_per_unit")["item"]
    unique_prices = items_per_price.first()[items_per_price.size() == 1]

    df["item"] = df["item"].fillna(df["price_per_unit"].map(unique_prices))
    return df


def fill_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Label the categories we could not recover as an explicit "Unknown".

    Deliberately a real value rather than NaN: "Unknown" survives a groupby()
    (pandas drops NaN keys by default), so unknown payment methods stay visible
    in the KPI tables instead of quietly disappearing from the totals.
    """
    for column in CATEGORICAL_COLUMNS:
        df[column] = df[column].fillna("Unknown")
    return df


def clean() -> pd.DataFrame:
    """Run the whole pipeline and hand back the cleaned DataFrame.

    The step order is load-bearing:
      1. price from item         -- unlocks rows missing two of the three numbers
      2. the arithmetic identity -- now has two knowns on many more rows
      3. item from price         -- uses prices step 2 just recovered
    """
    df = load_raw()
    df = sentinels_to_missing(df)
    df = coerce_types(df)

    price_lookup = build_price_lookup(df)
    df = impute_price_from_item(df, price_lookup)
    df = impute_numeric_identity(df)
    df = impute_item_from_price(df, price_lookup)

    return fill_categoricals(df)


def quality_report(raw: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    """Per-column before/after table -- the KPIs about the pipeline itself.

    "missing_before" counts blank cells *and* sentinel strings, which is the
    honest baseline; raw.isna() on its own understates the problem.
    """
    raw_missing = raw.isna() | raw.isin(SENTINELS)
    cleaned_missing = cleaned.isna() | cleaned.isin(["Unknown"])

    report = pd.DataFrame(
        {
            "missing_before": raw_missing.sum(),
            "missing_after": cleaned_missing.sum(),
        }
    )
    report["recovered"] = report["missing_before"] - report["missing_after"]
    report["complete_pct_after"] = (1 - report["missing_after"] / len(cleaned)) * 100
    return report.round(1)


def integrity_violations(df: pd.DataFrame) -> int:
    """Count rows where quantity * price no longer equals total_spent.

    Run *after* imputing, to prove the imputation did not invent bad money.
    Expected result: 0.
    """
    expected = df["quantity"] * df["price_per_unit"]
    gap = (expected - df["total_spent"]).abs()
    return int((gap > MONEY_TOLERANCE).sum())


def main() -> None:
    raw = load_raw()
    cleaned = clean()

    print("=== Data quality: before vs. after ===")
    print(quality_report(raw, cleaned).to_string())

    revenue_ready = cleaned["total_spent"].notna().sum()
    print(f"\nRows with usable revenue: {revenue_ready:,} / {len(cleaned):,}")
    print(f"Arithmetic integrity violations: {integrity_violations(cleaned)}")

    # parents=True creates output/ if it is missing; exist_ok=True makes a
    # re-run a no-op instead of an error. index=False keeps pandas' row numbers
    # out of the file -- they are not data.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(CLEAN_CSV, index=False)
    print(f"\nWrote {CLEAN_CSV.relative_to(REPO_ROOT)}")


# Only runs when this file is executed directly, not when another script
# imports it -- which is what lets cafe_sales_kpis.py reuse clean() without
# triggering all the printing above.
if __name__ == "__main__":
    main()
