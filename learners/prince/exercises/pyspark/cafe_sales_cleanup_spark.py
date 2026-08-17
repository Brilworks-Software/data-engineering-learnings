"""Cafe sales cleanup -- PySpark DataFrame API.

The third implementation of the same pipeline. The function names match
../python/data_processing/cafe_sales_data_cleanup.py one for one, so you can
open the two files side by side and see exactly how each pandas idiom
translates:

    pandas                              PySpark
    ------------------------------      ------------------------------------
    df.replace([...], None)             F.when(col.isin(...), None)
    pd.to_numeric(errors="coerce")      col.try_cast("double")
    df["a"].map(lookup_series)          df.join(lookup_df, "a", "left")
    df["a"].fillna(df["b"])             F.coalesce("a", "b")
    df.groupby("a")["b"].median()       df.groupBy("a").agg(F.median("b"))
    len(df)                             df.count()

Run locally:      python learners/prince/exercises/pyspark/cafe_sales_cleanup_spark.py
Run on Databricks: import as a notebook and call main() -- it reuses the
                   `spark` session the workspace already gave you.
"""

import tempfile
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def find_repo_root() -> Path:
    """Walk up from this file until the folder containing .git turns up.

    Preferred over a fixed Path(__file__).parents[N] because N silently becomes
    wrong the moment the file moves to a different depth. Searching for a
    landmark keeps the path correct wherever the exercise ends up.
    """
    for candidate in Path(__file__).resolve().parents:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError("repo root not found -- is this still inside the git repo?")


REPO_ROOT = find_repo_root()
RAW_CSV = REPO_ROOT / "resources" / "datasets" / "dirty_cafe_sales.csv"
OUTPUT_DIR = REPO_ROOT / "output" / "spark"

SENTINELS = ["ERROR", "UNKNOWN"]
NUMERIC_COLUMNS = ["quantity", "price_per_unit", "total_spent"]
CATEGORICAL_COLUMNS = ["item", "payment_method", "location"]
MONEY_TOLERANCE = 0.01


def get_spark() -> SparkSession:
    """Reuse the active session if there is one, otherwise start a local one.

    getOrCreate() is what makes this file work unchanged in both places: on
    Databricks a session already exists and is handed straight back, so the
    local-only settings below are just ignored.

    Spark hardcodes /tmp for its scratch files, which fails on Windows and
    anywhere /tmp is read-only. Pointing both settings at the OS temp dir fixes
    that: spark.local.dir covers shuffle files, and -Djava.io.tmpdir covers the
    JVM's own scratch space, which is allocated too early for the former to
    reach.
    """
    temp_dir = tempfile.gettempdir()

    return (
        SparkSession.builder.appName("cafe-sales-cleanup")
        .master("local[2]")
        .config("spark.local.dir", temp_dir)
        .config("spark.driver.extraJavaOptions", f"-Djava.io.tmpdir={temp_dir}")
        .config("spark.ui.enabled", "false")
        # 200 shuffle partitions is the cluster-scale default and pure overhead
        # on a 10k-row CSV -- every groupBy would spawn 200 near-empty tasks.
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def load_raw(spark: SparkSession) -> DataFrame:
    """Read the raw CSV as all-strings and snake_case the column names.

    inferSchema is deliberately left off. Letting Spark guess would either
    throw on 'ERROR' or quietly hand back a string column anyway -- and the
    cleanup below is the code that should own typing, not the reader.

    toDF(*names) renames every column positionally in one call, which is the
    closest thing to assigning df.columns in pandas.
    """
    df = spark.read.csv(str(RAW_CSV), header=True, inferSchema=False)
    return df.toDF(*[name.strip().lower().replace(" ", "_") for name in df.columns])


def sentinels_to_missing(df: DataFrame) -> DataFrame:
    """Replace the 'ERROR'/'UNKNOWN' placeholder strings with real NULLs.

    DataFrame.replace() cannot map a value to None, so the substitution is a
    when()/otherwise() per column. With no .otherwise() attached, when() would
    return NULL for every non-matching row too -- which is why .otherwise(...)
    handing back the original column matters here.
    """
    for name in df.columns:
        df = df.withColumn(
            name, F.when(F.col(name).isin(SENTINELS), None).otherwise(F.col(name))
        )
    return df


def coerce_types(df: DataFrame) -> DataFrame:
    """Cast the text columns to the types they should have had.

    try_cast(), not cast(). Spark 4 runs with ANSI mode ON by default, so a
    plain cast() of 'ERROR' to double raises and kills the job; try_cast()
    yields NULL instead. It is the exact counterpart of pandas'
    errors="coerce" -- the argument that turns a conversion into a cleaning
    step.
    """
    for name in NUMERIC_COLUMNS:
        df = df.withColumn(name, F.col(name).try_cast("double"))

    return df.withColumn("transaction_date", F.col("transaction_date").try_cast("date"))


def build_price_lookup(df: DataFrame) -> DataFrame:
    """Learn each item's price from the rows that are already complete.

    Returns a two-column DataFrame rather than a Python dict on purpose: a
    dict would need .collect(), dragging the data back to the driver. Joining
    keeps the work distributed, which is the habit that still holds when this
    file is 10 billion rows instead of 10 thousand.
    """
    return (
        df.filter(F.col("item").isNotNull() & F.col("price_per_unit").isNotNull())
        .groupBy("item")
        .agg(F.median("price_per_unit").alias("item_price"))
    )


def impute_price_from_item(df: DataFrame, price_lookup: DataFrame) -> DataFrame:
    """Fill a missing price_per_unit from the item name.

    F.broadcast() ships this 8-row lookup to every executor so the join needs
    no shuffle at all. Always broadcast a small dimension table -- it is the
    cheapest performance win in Spark.

    coalesce() returns its first non-NULL argument, so a price that is already
    present wins and only the gaps get filled.
    """
    return (
        df.join(F.broadcast(price_lookup), on="item", how="left")
        .withColumn("price_per_unit", F.coalesce("price_per_unit", "item_price"))
        .drop("item_price")
    )


def impute_numeric_identity(df: DataFrame) -> DataFrame:
    """Rebuild a missing number from the other two.

    quantity * price_per_unit = total_spent holds on every complete row in this
    file, so the identity is a trusted rule to impute WITH, not merely validate
    against.

    All three columns are computed from the SAME input row. Spark evaluates the
    select() as one projection, so quantity below still sees the ORIGINAL
    total_spent, not the value the first line just filled -- unlike a chain of
    withColumn() calls, where each step sees the previous one's output.

    nullif(x, 0) keeps a zero quantity or price from producing Infinity.
    """
    quantity, price, total = F.col("quantity"), F.col("price_per_unit"), F.col("total_spent")

    return df.select(
        "transaction_id",
        "item",
        F.round(F.coalesce(quantity, total / F.nullif(price, F.lit(0))), 2).alias("quantity"),
        F.round(F.coalesce(price, total / F.nullif(quantity, F.lit(0))), 2).alias("price_per_unit"),
        F.round(F.coalesce(total, quantity * price), 2).alias("total_spent"),
        "payment_method",
        "location",
        "transaction_date",
    )


def impute_item_from_price(df: DataFrame, price_lookup: DataFrame) -> DataFrame:
    """Recover a missing item name from its price -- where that is unambiguous.

    Only prices owned by a single item qualify: 1.0 -> Cookie, 1.5 -> Tea,
    2.0 -> Coffee, 5.0 -> Salad. 3.0 (Cake or Juice) and 4.0 (Sandwich or
    Smoothie) would be guesses, and the having() clause is what refuses to
    make them.
    """
    unique_prices = (
        price_lookup.groupBy("item_price")
        .agg(F.max("item").alias("only_item"), F.count_distinct("item").alias("n_items"))
        .filter(F.col("n_items") == 1)
        .select("item_price", "only_item")
    )

    return (
        df.join(
            F.broadcast(unique_prices),
            on=df["price_per_unit"] == unique_prices["item_price"],
            how="left",
        )
        .withColumn("item", F.coalesce("item", "only_item"))
        .drop("item_price", "only_item")
    )


def fill_categoricals(df: DataFrame) -> DataFrame:
    """Label the categories we could not recover as an explicit 'Unknown'.

    A real value rather than NULL, because 'Unknown' survives a groupBy and
    keeps unrecoverable rows visible in the KPI totals.
    """
    return df.fillna("Unknown", subset=CATEGORICAL_COLUMNS)


def clean(spark: SparkSession) -> DataFrame:
    """Run the whole pipeline and hand back the cleaned DataFrame.

    Step order is load-bearing, exactly as in the pandas version:
      1. price from item         -- unlocks rows missing two of the three numbers
      2. the arithmetic identity -- now has two knowns on many more rows
      3. item from price         -- uses prices step 2 just recovered

    Nothing has executed yet when this returns. Spark transformations are lazy;
    the plan only runs when an action (count, show, write) asks for a result.
    """
    df = coerce_types(sentinels_to_missing(load_raw(spark)))

    price_lookup = build_price_lookup(df)
    df = impute_price_from_item(df, price_lookup)
    df = impute_numeric_identity(df)
    df = impute_item_from_price(df, price_lookup)

    return fill_categoricals(df)


def quality_report(cleaned: DataFrame) -> DataFrame:
    """One row of counts proving what the cleanup did and did not fix.

    count(col) ignores NULLs while count("*") does not, so subtracting the two
    is the idiomatic SQL way to count missing values.
    """
    unknown = [
        F.sum(F.when(F.col(name) == "Unknown", 1).otherwise(0)).alias(f"{name}_unknown")
        for name in CATEGORICAL_COLUMNS
    ]
    nulls = [
        (F.count("*") - F.count(F.col(name))).alias(f"{name}_null")
        for name in NUMERIC_COLUMNS + ["transaction_date"]
    ]
    sentinels_left = F.sum(
        F.when(
            F.coalesce(*[F.col(name).isin(SENTINELS) for name in CATEGORICAL_COLUMNS]), 1
        ).otherwise(0)
    ).alias("sentinels_left")

    return cleaned.agg(F.count("*").alias("rows_total"), *nulls, *unknown, sentinels_left)


def integrity_violations(df: DataFrame) -> int:
    """Rows where quantity * price no longer equals total_spent. Expect 0.

    Money is compared against a tolerance, never with == -- floating point
    makes 0.1 + 0.2 != 0.3.
    """
    gap = F.abs(F.col("quantity") * F.col("price_per_unit") - F.col("total_spent"))
    return df.filter(gap > MONEY_TOLERANCE).count()


def main() -> None:
    spark = get_spark()
    cleaned = clean(spark)

    # cache() because everything below scans the same result. Without it Spark
    # would recompute the entire pipeline for each action.
    cleaned.cache()

    print("=== Data quality after cleanup ===")
    quality_report(cleaned).show(truncate=False, vertical=True)

    print(f"Arithmetic integrity violations: {integrity_violations(cleaned)}")

    print("\n=== Headline KPIs ===")
    cleaned.agg(
        F.round(F.sum("total_spent"), 2).alias("total_revenue"),
        F.count("total_spent").alias("rows_with_revenue"),
        F.round(F.sum("total_spent") / F.count("*"), 2).alias("avg_order_value"),
    ).show()

    print("=== Revenue by item ===")
    cleaned.groupBy("item").agg(
        F.round(F.sum("total_spent"), 2).alias("revenue"),
        F.count("*").alias("transactions"),
    ).orderBy(F.desc("revenue")).show()

    # coalesce(1) forces a single output file, which is convenient at this size
    # and wrong at scale -- it funnels the whole dataset through one task.
    # Note Spark writes a DIRECTORY of part files, not a single .csv.
    cleaned.coalesce(1).write.mode("overwrite").csv(
        str(OUTPUT_DIR / "cafe_sales_cleaned"), header=True
    )
    print(f"Wrote {(OUTPUT_DIR / 'cafe_sales_cleaned').relative_to(REPO_ROOT)}/")

    cleaned.unpersist()
    spark.stop()


if __name__ == "__main__":
    main()
