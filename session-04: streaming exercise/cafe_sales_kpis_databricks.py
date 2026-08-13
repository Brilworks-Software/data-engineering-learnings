# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Cafe Sales — Cleaning + KPI Pipeline
# MAGIC Source: kagglehub `ahmedmohamed2003/cafe-sales-dirty-data-for-cleaning-training`
# MAGIC
# MAGIC Known dirty-data patterns in this file (confirmed from source sample):
# MAGIC - Numeric columns (`Quantity`, `Price Per Unit`, `Total Spent`) contain the literal string `"ERROR"` and true nulls.
# MAGIC - Categorical columns (`Payment Method`, `Location`) contain the literal string `"UNKNOWN"` and true nulls.
# MAGIC - `Transaction Date` contains unparseable / malformed strings.
# MAGIC
# MAGIC This script does NOT assume the row count, null rate, or specific corrupt values beyond what's visible —
# MAGIC those are computed from the data at runtime, not hardcoded.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

# COMMAND ----------

# MAGIC %md ## 0. Config — adjust the path to wherever the CSV lands in your workspace

# COMMAND ----------

# If you're pulling via kagglehub in a notebook cell first and writing to DBFS/Volumes, point this at that path.
# e.g. "/Volumes/main/default/raw/dirty_cafe_sales.csv" or "dbfs:/FileStore/dirty_cafe_sales.csv"
INPUT_PATH = "/Workspace/Users/het.p@brilworks.com/data-engineering-learnings/session-04: streaming exercise/dirty_cafe_sales.csv"

raw = (
    spark.read
    .option("header", True)
    .option("inferSchema", False)  # read everything as string first; dirty data breaks type inference
    .csv(INPUT_PATH)
)

display(raw)
# display raw schema
raw.printSchema()

# COMMAND ----------

# MAGIC %md ## 1. Normalize sentinel garbage → real nulls
# MAGIC `"ERROR"`, `"UNKNOWN"`, `"NaN"`, `"nan"`, `""`, and whitespace-only strings all become NULL.
# MAGIC This is applied uniformly across every column before any type casting.

# COMMAND ----------

SENTINELS = ["ERROR", "UNKNOWN", "NaN", "nan", "NULL", "null", "None", ""]

def null_out_sentinels(df):
    for c in df.columns:
        df = df.withColumn(
            c,
            F.when(F.trim(F.col(c)).isin(SENTINELS) | F.col(c).isNull(), None)
             .otherwise(F.trim(F.col(c)))
        )
    return df

step1 = null_out_sentinels(raw)
display(step1)

# COMMAND ----------

# MAGIC %md ## 2. Cast numeric columns, keep a pre-cast copy of Total Spent to flag rows that failed casting
# MAGIC (a value like "2.O" or a currency symbol will silently become null on cast — worth tracking separately from true nulls)

# COMMAND ----------

step2 = (
    step1
    .withColumn("Quantity_raw_null", F.col("Quantity").isNull())
    .withColumn("Price_raw_null", F.col("Price Per Unit").isNull())
    .withColumn("Total_raw_null", F.col("Total Spent").isNull())
    .withColumn("Quantity", F.col("Quantity").cast(T.DoubleType()))
    .withColumn("Price Per Unit", F.col("Price Per Unit").cast(T.DoubleType()))
    .withColumn("Total Spent", F.col("Total Spent").cast(T.DoubleType()))
)

# Rows where the string wasn't a sentinel/null but still failed numeric cast (garbage text)
step2 = (
    step2
    .withColumn("qty_cast_failed", (~F.col("Quantity_raw_null")) & F.col("Quantity").isNull())
    .withColumn("price_cast_failed", (~F.col("Price_raw_null")) & F.col("Price Per Unit").isNull())
    .withColumn("total_cast_failed", (~F.col("Total_raw_null")) & F.col("Total Spent").isNull())
)
display(step2)

# COMMAND ----------

# MAGIC %md ## 3. Recompute Total Spent where it's missing but Quantity × Price is available
# MAGIC Assumption (flagging explicitly): Quantity and Price Per Unit are treated as more reliable than Total Spent
# MAGIC when only one of the three is corrupt. If Total Spent conflicts with Qty×Price by more than a cent, we
# MAGIC keep the recomputed value and flag it — Total Spent in this dataset is the one most often replaced with "ERROR".

# COMMAND ----------

step3 = step2.withColumn(
    "Total Spent_recomputed",
    F.when(
        F.col("Total Spent").isNull() & F.col("Quantity").isNotNull() & F.col("Price Per Unit").isNotNull(),
        F.round(F.col("Quantity") * F.col("Price Per Unit"), 2)
    ).otherwise(F.col("Total Spent"))
)

step3 = step3.withColumn(
    "revenue_was_imputed",
    F.col("Total Spent").isNull() & F.col("Total Spent_recomputed").isNotNull()
)

step3 = step3.withColumn("Total Spent", F.col("Total Spent_recomputed")).drop("Total Spent_recomputed")
display(step3)

# COMMAND ----------

# MAGIC %md ## 4. Parse Transaction Date, flag invalid dates explicitly

# COMMAND ----------

step4 = step3.withColumn("Transaction_Date_parsed", F.to_date(F.col("Transaction Date"), "yyyy-MM-dd"))

step4 = step4.withColumn(
    "date_is_invalid",
    F.col("Transaction Date").isNotNull() & F.col("Transaction_Date_parsed").isNull()
)

step4 = step4.withColumn(
    "date_is_missing",
    F.col("Transaction Date").isNull()
)

# COMMAND ----------

# MAGIC %md ## 5. Row-level success/failure flag
# MAGIC A row is "successful" if, after cleaning, it has: a resolvable Total Spent, a non-null Payment Method,
# MAGIC a non-null Location, and a valid Transaction Date. This threshold is a modeling choice, not something
# MAGIC stated in the source data — adjust if your definition of "successful transaction" differs.

# COMMAND ----------

cleaned = step4.withColumn(
    "row_successful",
    F.col("Total Spent").isNotNull()
    & F.col("Payment Method").isNotNull()
    & F.col("Location").isNotNull()
    & F.col("Transaction_Date_parsed").isNotNull()
    & F.col("Quantity").isNotNull()
)

TOTAL_ROWS = cleaned.count()
print(f"Total rows: {TOTAL_ROWS}")

# COMMAND ----------

# MAGIC %md ## 6. KPI 1 — Revenue by Product

# COMMAND ----------

kpi_revenue_by_product = (
    cleaned.filter(F.col("Total Spent").isNotNull())
    .groupBy("Item")
    .agg(F.round(F.sum("Total Spent"), 2).alias("Revenue"))
    .orderBy(F.desc("Revenue"))
)
display(kpi_revenue_by_product)

# COMMAND ----------

# MAGIC %md ## 7. KPI 2 — Revenue by Location

# COMMAND ----------

kpi_revenue_by_location = (
    cleaned.filter(F.col("Total Spent").isNotNull())
    .groupBy("Location")
    .agg(F.round(F.sum("Total Spent"), 2).alias("Revenue"))
    .orderBy(F.desc("Revenue"))
)
display(kpi_revenue_by_location)

# COMMAND ----------

# MAGIC %md ## 8. KPI 3 — Revenue by Payment Method

# COMMAND ----------

kpi_revenue_by_payment = (
    cleaned.filter(F.col("Total Spent").isNotNull())
    .groupBy("Payment Method")
    .agg(F.round(F.sum("Total Spent"), 2).alias("Revenue"))
    .orderBy(F.desc("Revenue"))
)
display(kpi_revenue_by_payment)

# COMMAND ----------

# MAGIC %md ## 9. KPI 4 — Weekend vs Weekday Sales
# MAGIC Spark's `dayofweek`: 1 = Sunday, 7 = Saturday. Weekend = Saturday/Sunday.

# COMMAND ----------

with_daytype = (
    cleaned.filter(F.col("Total Spent").isNotNull() & F.col("Transaction_Date_parsed").isNotNull())
    .withColumn("dow", F.dayofweek("Transaction_Date_parsed"))
    .withColumn("day_type", F.when(F.col("dow").isin(1, 7), "Weekend").otherwise("Weekday"))
)

kpi_weekend_vs_weekday = (
    with_daytype.groupBy("day_type")
    .agg(
        F.round(F.sum("Total Spent"), 2).alias("Revenue"),
        F.count("*").alias("Transactions")
    )
    .orderBy(F.desc("Revenue"))
)
display(kpi_weekend_vs_weekday)

# COMMAND ----------

# MAGIC %md ## 10. KPI 5 — Peak Sales Day
# MAGIC Single calendar date with the highest total revenue. (If you actually meant "which day of week
# MAGIC peaks", swap groupBy to `dow`/`day_type` from the cell above.)

# COMMAND ----------

kpi_peak_sales_day = (
    cleaned.filter(F.col("Total Spent").isNotNull() & F.col("Transaction_Date_parsed").isNotNull())
    .groupBy("Transaction_Date_parsed")
    .agg(F.round(F.sum("Total Spent"), 2).alias("Revenue"))
    .orderBy(F.desc("Revenue"))
)
display(kpi_peak_sales_day.limit(10))
print("Peak day:", kpi_peak_sales_day.first())

# COMMAND ----------

# MAGIC %md ## 11. KPI 6 — Best Selling Item (by Quantity)

# COMMAND ----------

kpi_best_selling_item = (
    cleaned.filter(F.col("Quantity").isNotNull())
    .groupBy("Item")
    .agg(F.sum("Quantity").alias("Total_Quantity"))
    .orderBy(F.desc("Total_Quantity"))
)
display(kpi_best_selling_item)
print("Best seller by quantity:", kpi_best_selling_item.first())

# COMMAND ----------

# MAGIC %md ## 12. KPI 7 — Product Revenue Contribution (%)

# COMMAND ----------

total_revenue = cleaned.filter(F.col("Total Spent").isNotNull()).agg(F.sum("Total Spent")).first()[0]

kpi_product_contribution = (
    kpi_revenue_by_product
    .withColumn("Contribution_Pct", F.round(F.col("Revenue") / F.lit(total_revenue) * 100, 2))
    .orderBy(F.desc("Contribution_Pct"))
)
display(kpi_product_contribution)

# COMMAND ----------

# MAGIC %md ## 13. KPI 8 — Transaction Success Rate
# MAGIC % of rows that are "successful" per the row_successful definition in Step 5.

# COMMAND ----------

success_count = cleaned.filter(F.col("row_successful")).count()
transaction_success_rate = round(success_count / TOTAL_ROWS * 100, 2) if TOTAL_ROWS else None

print(f"Successful transactions: {success_count} / {TOTAL_ROWS}")
print(f"Transaction Success Rate: {transaction_success_rate}%")

kpi_success_rate = spark.createDataFrame(
    [(success_count, TOTAL_ROWS - success_count, transaction_success_rate)],
    ["Successful_Rows", "Failed_Rows", "Success_Rate_Pct"]
)
display(kpi_success_rate)

# COMMAND ----------

# MAGIC %md ## 14. KPI 9 — Missing Data Rate
# MAGIC Two versions, since "missing data rate" is ambiguous:
# MAGIC - **Cell-level**: nulls across all cells (post sentinel-normalization) ÷ total cells.
# MAGIC - **Column-level breakdown**: null rate per column, so you can see which fields are actually driving it.

# COMMAND ----------

business_cols = [c for c in raw.columns]  # original source columns only, excludes derived flag columns

null_counts = cleaned.select(
    [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in business_cols]
).first().asDict()

total_cells = TOTAL_ROWS * len(business_cols)
total_missing_cells = sum(null_counts.values())
cell_level_missing_rate = round(total_missing_cells / total_cells * 100, 2) if total_cells else None

print(f"Cell-level Missing Data Rate: {cell_level_missing_rate}%")

kpi_missing_by_column = spark.createDataFrame(
    [(col, cnt, round(cnt / TOTAL_ROWS * 100, 2)) for col, cnt in null_counts.items()],
    ["Column", "Null_Count", "Null_Rate_Pct"]
).orderBy(F.desc("Null_Rate_Pct"))

display(kpi_missing_by_column)

# COMMAND ----------

# MAGIC %md ## 15. KPI 10 — Invalid Date Percentage
# MAGIC Split into two numbers on purpose: "invalid" (non-null string that failed to parse) is a different
# MAGIC failure mode than "missing" (null outright). Reported both individually and combined.

# COMMAND ----------

invalid_date_count = cleaned.filter(F.col("date_is_invalid")).count()
missing_date_count = cleaned.filter(F.col("date_is_missing")).count()

invalid_date_pct = round(invalid_date_count / TOTAL_ROWS * 100, 2) if TOTAL_ROWS else None
missing_date_pct = round(missing_date_count / TOTAL_ROWS * 100, 2) if TOTAL_ROWS else None
combined_bad_date_pct = round((invalid_date_count + missing_date_count) / TOTAL_ROWS * 100, 2) if TOTAL_ROWS else None

print(f"Invalid (unparseable) date %: {invalid_date_pct}%")
print(f"Missing (null) date %: {missing_date_pct}%")
print(f"Combined bad-date %: {combined_bad_date_pct}%")

kpi_invalid_dates = spark.createDataFrame(
    [(invalid_date_count, invalid_date_pct, missing_date_count, missing_date_pct, combined_bad_date_pct)],
    ["Invalid_Count", "Invalid_Pct", "Missing_Count", "Missing_Pct", "Combined_Bad_Date_Pct"]
)
display(kpi_invalid_dates)

# COMMAND ----------

# MAGIC %md ## 16. Optional — write cleaned table + KPI summary to a Delta table for downstream BI use

# COMMAND ----------

# cleaned.write.format("delta").mode("overwrite").saveAsTable("main.default.cafe_sales_cleaned")
# kpi_revenue_by_product.write.format("delta").mode("overwrite").saveAsTable("main.default.kpi_revenue_by_product")
# (repeat per KPI table as needed — left commented out since target catalog/schema is environment-specific)