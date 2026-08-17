"""Compute the cafe sales KPIs from the cleaned table.

    python learners/prince/exercises/python/data_processing/cafe_sales_kpis.py

Reads nothing from disk itself -- it imports clean() from the cleanup module so
the two scripts can never drift apart. Each KPI table is printed and also
written to output/kpis/ as CSV.

Read the caveats in KNOWN_GAPS before quoting the channel numbers.
"""

import pandas as pd

from pathlib import Path

# Because both files sit in the same folder, Python finds this import whichever
# directory you launch from -- the script's own folder is always first on the
# import path.
from cafe_sales_data_cleanup import OUTPUT_DIR, REPO_ROOT, clean

KPI_DIR = OUTPUT_DIR / "kpis"

# Weekday names sort alphabetically by default, which puts Friday first and
# reads as nonsense. An ordered Categorical restores calendar order.
WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

KNOWN_GAPS = """\
location is 60% complete and payment_method 68%, so their splits are reported
twice: once including "Unknown" (true revenue totals) and once across known
rows only (the share you would actually quote). transaction_date is missing on
460 rows, which the time-series KPIs drop.\
"""


def add_date_parts(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the calendar columns the time KPIs group by.

    .dt is the datetime equivalent of .str -- it only works because the cleanup
    step already converted this column with pd.to_datetime(). On a text column
    every one of these would raise.
    """
    df = df.copy()
    # to_period("M") collapses a date to its month ("2023-09"), which is a far
    # better groupby key than the raw date and still sorts chronologically.
    df["month"] = df["transaction_date"].dt.to_period("M")
    df["weekday"] = pd.Categorical(
        df["transaction_date"].dt.day_name(), categories=WEEKDAYS, ordered=True
    )
    return df


def overview_kpis(df: pd.DataFrame) -> pd.Series:
    """The headline numbers -- one scalar each.

    Every row is one transaction (all 10,000 transaction_ids are unique), so
    len(df) is the transaction count and no de-duplication is needed.
    """
    revenue = df["total_spent"].sum()
    transactions = len(df)
    dated = df["transaction_date"].notna()

    return pd.Series(
        {
            "total_revenue": round(revenue, 2),
            "transactions": transactions,
            "units_sold": df["quantity"].sum(),
            # AOV = revenue per transaction, the single most quoted retail KPI.
            "avg_order_value": round(revenue / transactions, 2),
            "avg_units_per_order": round(df["quantity"].mean(), 2),
            "distinct_days": df.loc[dated, "transaction_date"].dt.date.nunique(),
            "avg_revenue_per_day": round(
                df.loc[dated, "total_spent"].sum()
                / df.loc[dated, "transaction_date"].dt.date.nunique(),
                2,
            ),
        }
    )


def revenue_by(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Group revenue by any one column -- item, location, payment_method, ...

    .agg() with a dict applies a different function per column in one pass,
    which is both faster and clearer than three separate groupby calls.
    observed=True stops pandas from emitting empty rows for unused Categorical
    levels.
    """
    grouped = df.groupby(dimension, observed=True).agg(
        revenue=("total_spent", "sum"),
        transactions=("total_spent", "size"),
        units=("quantity", "sum"),
    )

    # Share of total, the number that turns a raw sum into a finding.
    grouped["revenue_share_pct"] = grouped["revenue"] / grouped["revenue"].sum() * 100
    grouped["avg_order_value"] = grouped["revenue"] / grouped["transactions"]

    return grouped.sort_values("revenue", ascending=False).round(2)


def revenue_by_known_only(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Same split, with the "Unknown" bucket excluded before computing shares.

    Leaving Unknown in makes every share look small; dropping it silently
    overstates the winners. Reporting both is the honest option -- and the
    shares here only hold if the missing rows are missing at random, which is
    an assumption, not a fact.
    """
    known = df[df[dimension] != "Unknown"]
    return revenue_by(known, dimension)


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue per calendar month plus month-over-month growth."""
    monthly = df.dropna(subset=["transaction_date"]).groupby("month").agg(
        revenue=("total_spent", "sum"),
        transactions=("total_spent", "size"),
    )
    monthly["avg_order_value"] = monthly["revenue"] / monthly["transactions"]
    # pct_change() compares each row with the previous one; the first month has
    # nothing to compare against, so it is legitimately NaN.
    monthly["mom_growth_pct"] = monthly["revenue"].pct_change() * 100
    return monthly.round(2)


def weekday_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """Which days of the week actually earn the money.

    Revenue alone would just track how many of each weekday fall in the year,
    so avg_revenue_per_day divides by the number of distinct dates -- that is
    the comparable figure.
    """
    dated = df.dropna(subset=["transaction_date"])
    pattern = dated.groupby("weekday", observed=True).agg(
        revenue=("total_spent", "sum"),
        transactions=("total_spent", "size"),
        days=("transaction_date", lambda dates: dates.dt.date.nunique()),
    )
    pattern["avg_revenue_per_day"] = pattern["revenue"] / pattern["days"]
    return pattern.round(2)


def item_by_location(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-tab answering "does Takeaway sell a different menu than In-store?"

    pivot_table() is groupby on two dimensions at once. Percentages run down
    each column, so the two channels are comparable even though their row
    counts differ.
    """
    known = df[df["location"] != "Unknown"]
    revenue = known.pivot_table(
        index="item", columns="location", values="total_spent", aggfunc="sum"
    )
    # .sum() defaults to axis=0 (down the column), which is what we want here.
    return (revenue / revenue.sum() * 100).round(2)


def best_and_worst_days(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """The n strongest and n weakest trading days, for spotting outliers."""
    daily = (
        df.dropna(subset=["transaction_date"])
        .groupby(df["transaction_date"].dt.date)
        .agg(revenue=("total_spent", "sum"), transactions=("total_spent", "size"))
        .round(2)
    )
    ranked = daily.sort_values("revenue", ascending=False)
    # pd.concat glues the head and tail into one table; the label column marks
    # which end each row came from.
    return pd.concat(
        [ranked.head(n).assign(rank="best"), ranked.tail(n).assign(rank="worst")]
    )


def main() -> None:
    df = add_date_parts(clean())

    tables = {
        "by_item": revenue_by(df, "item"),
        "by_location": revenue_by(df, "location"),
        "by_location_known_only": revenue_by_known_only(df, "location"),
        "by_payment_method": revenue_by(df, "payment_method"),
        "by_payment_method_known_only": revenue_by_known_only(df, "payment_method"),
        "monthly_trend": monthly_trend(df),
        "weekday_pattern": weekday_pattern(df),
        "item_mix_by_location_pct": item_by_location(df),
        "best_and_worst_days": best_and_worst_days(df),
    }

    print("=== Overview ===")
    print(overview_kpis(df).to_string())

    for name, table in tables.items():
        print(f"\n=== {name.replace('_', ' ')} ===")
        print(table.to_string())

    print(f"\n=== Caveats ===\n{KNOWN_GAPS}")

    KPI_DIR.mkdir(parents=True, exist_ok=True)
    overview_kpis(df).to_csv(KPI_DIR / "overview.csv", header=["value"])
    for name, table in tables.items():
        table.to_csv(KPI_DIR / f"{name}.csv")
    print(f"\nWrote {len(tables) + 1} KPI tables to {KPI_DIR.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
