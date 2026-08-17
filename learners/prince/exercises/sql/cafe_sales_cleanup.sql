-- ============================================================================
-- Cafe sales cleanup -- Spark SQL / Databricks SQL
--
-- The same pipeline as ../python/data_processing/cafe_sales_data_cleanup.py,
-- so you can read the two side by side. Each CTE below is one Python function:
--
--   renamed          -> load_raw()               snake_case the columns
--   nulled           -> sentinels_to_missing()   'ERROR'/'UNKNOWN' -> NULL
--   typed            -> coerce_types()           text -> DOUBLE / DATE
--   price_lookup     -> build_price_lookup()     learn each item's price
--   unique_prices    -> impute_item_from_price() prices owned by one item
--   priced           -> impute_price_from_item() fill price from the item
--   imputed          -> impute_numeric_identity() qty * price = total
--   final SELECT     -> fill_categoricals()      NULL -> 'Unknown'
--
-- Run in Databricks: attach to any cluster / SQL warehouse and run top to
-- bottom. Run locally, FROM THE REPO ROOT:
--   spark-sql -f learners/prince/exercises/sql/cafe_sales_cleanup.sql
-- ============================================================================


-- ---------------------------------------------------------------------------
-- STEP 0: point a view at the raw CSV.
--
-- Local Spark. Unlike the Python scripts, which locate the repo root from
-- __file__, a SQL path is resolved against the directory you launched
-- spark-sql from -- so run this from the repo root or the path will not
-- resolve.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TEMPORARY VIEW dirty_cafe_sales
USING csv
OPTIONS (path 'resources/datasets/dirty_cafe_sales.csv', header 'true');

-- On Databricks, swap the block above for read_files() against your Volume or
-- DBFS path -- everything downstream is identical:
--
-- CREATE OR REPLACE TEMPORARY VIEW dirty_cafe_sales AS
-- SELECT * FROM read_files(
--   '/Volumes/<catalog>/<schema>/<volume>/dirty_cafe_sales.csv',
--   format => 'csv',
--   header => true
-- );


-- ---------------------------------------------------------------------------
-- STEP 1: the cleanup itself.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TEMPORARY VIEW cafe_sales_cleaned AS
WITH renamed AS (
  -- The raw header is "Price Per Unit", which needs backticks every single
  -- time it is referenced. Renaming once here keeps the rest of the file
  -- readable -- the SQL equivalent of df.columns.str.lower().str.replace().
  SELECT
    `Transaction ID`   AS transaction_id,
    `Item`             AS item,
    `Quantity`         AS quantity,
    `Price Per Unit`   AS price_per_unit,
    `Total Spent`      AS total_spent,
    `Payment Method`   AS payment_method,
    `Location`         AS location,
    `Transaction Date` AS transaction_date
  FROM dirty_cafe_sales
),

nulled AS (
  -- NULLIF(x, 'ERROR') returns NULL when x = 'ERROR', otherwise x. Nesting two
  -- of them knocks out both sentinels in one expression -- this is the SQL
  -- version of df.replace(['ERROR', 'UNKNOWN'], None).
  SELECT
    transaction_id,
    NULLIF(NULLIF(item,             'ERROR'), 'UNKNOWN') AS item,
    NULLIF(NULLIF(quantity,         'ERROR'), 'UNKNOWN') AS quantity,
    NULLIF(NULLIF(price_per_unit,   'ERROR'), 'UNKNOWN') AS price_per_unit,
    NULLIF(NULLIF(total_spent,      'ERROR'), 'UNKNOWN') AS total_spent,
    NULLIF(NULLIF(payment_method,   'ERROR'), 'UNKNOWN') AS payment_method,
    NULLIF(NULLIF(location,         'ERROR'), 'UNKNOWN') AS location,
    NULLIF(NULLIF(transaction_date, 'ERROR'), 'UNKNOWN') AS transaction_date
  FROM renamed
),

typed AS (
  -- TRY_CAST is the SQL twin of pandas' errors="coerce": unparseable input
  -- becomes NULL instead of failing the query. Plain CAST would error out (or
  -- silently poison the column) on the first bad row.
  SELECT
    transaction_id,
    item,
    TRY_CAST(quantity       AS DOUBLE) AS quantity,
    TRY_CAST(price_per_unit AS DOUBLE) AS price_per_unit,
    TRY_CAST(total_spent    AS DOUBLE) AS total_spent,
    payment_method,
    location,
    TRY_CAST(transaction_date AS DATE) AS transaction_date
  FROM nulled
),

price_lookup AS (
  -- Learn the menu price from the rows that are already complete, rather than
  -- hardcoding it -- if the cafe reprices, this follows automatically.
  -- median() shrugs off a stray typo far better than avg() would.
  SELECT item, median(price_per_unit) AS item_price
  FROM typed
  WHERE item IS NOT NULL AND price_per_unit IS NOT NULL
  GROUP BY item
),

unique_prices AS (
  -- Reversing the lookup is only safe for a price belonging to exactly one
  -- item: 1.0 -> Cookie, 1.5 -> Tea, 2.0 -> Coffee, 5.0 -> Salad. Prices 3.0
  -- (Cake or Juice) and 4.0 (Sandwich or Smoothie) are ambiguous, and the
  -- HAVING clause is what refuses to guess on them.
  SELECT item_price, MAX(item) AS only_item
  FROM price_lookup
  GROUP BY item_price
  HAVING COUNT(DISTINCT item) = 1
),

priced AS (
  -- Fill a missing price from the item name. This runs BEFORE the arithmetic
  -- below because it unlocks rows that were missing two of the three numbers.
  SELECT
    t.transaction_id,
    t.item,
    t.quantity,
    COALESCE(t.price_per_unit, l.item_price) AS price_per_unit,
    t.total_spent,
    t.payment_method,
    t.location,
    t.transaction_date
  FROM typed AS t
  LEFT JOIN price_lookup AS l ON t.item = l.item
),

imputed AS (
  -- quantity * price_per_unit = total_spent holds on every complete row in
  -- this file, so the identity is a trusted rule we can impute WITH, not
  -- merely validate against. Given any two, the third is arithmetic.
  --
  -- NULLIF(x, 0) guards the divisions: a zero quantity or price would
  -- otherwise produce Infinity. Neither is 0 here, but the next export might
  -- be. ROUND(..., 2) pins recomputed money back to cents.
  SELECT
    transaction_id,
    item,
    ROUND(COALESCE(quantity,       total_spent / NULLIF(price_per_unit, 0)), 2) AS quantity,
    ROUND(COALESCE(price_per_unit, total_spent / NULLIF(quantity, 0)),       2) AS price_per_unit,
    ROUND(COALESCE(total_spent,    quantity * price_per_unit),               2) AS total_spent,
    payment_method,
    location,
    transaction_date
  FROM priced
)

-- COALESCE(..., 'Unknown') is deliberate, not lazy: 'Unknown' is a real value
-- that survives a GROUP BY, so unrecoverable rows stay visible in the KPI
-- totals instead of being silently dropped the way a NULL key would be.
SELECT
  i.transaction_id,
  COALESCE(i.item, u.only_item, 'Unknown')  AS item,
  i.quantity,
  i.price_per_unit,
  i.total_spent,
  COALESCE(i.payment_method, 'Unknown')     AS payment_method,
  COALESCE(i.location, 'Unknown')           AS location,
  i.transaction_date
FROM imputed AS i
-- Recover the item from its price, using prices the arithmetic step above may
-- itself have just rebuilt.
LEFT JOIN unique_prices AS u ON i.price_per_unit = u.item_price;


-- ---------------------------------------------------------------------------
-- STEP 2: validate. Never trust a cleanup you have not counted.
-- ---------------------------------------------------------------------------

-- 2a. What is still missing? Expect quantity 23, price_per_unit 6,
--     total_spent 23, transaction_date 460 -- and 0 for the sentinels, which
--     is the whole point of the exercise.
SELECT
  COUNT(*)                                                      AS rows_total,
  COUNT(*) - COUNT(quantity)                                    AS quantity_null,
  COUNT(*) - COUNT(price_per_unit)                              AS price_null,
  COUNT(*) - COUNT(total_spent)                                 AS total_null,
  COUNT(*) - COUNT(transaction_date)                            AS date_null,
  SUM(CASE WHEN item           = 'Unknown' THEN 1 ELSE 0 END)   AS item_unknown,
  SUM(CASE WHEN payment_method = 'Unknown' THEN 1 ELSE 0 END)   AS payment_unknown,
  SUM(CASE WHEN location       = 'Unknown' THEN 1 ELSE 0 END)   AS location_unknown,
  SUM(CASE WHEN item IN ('ERROR', 'UNKNOWN')
             OR payment_method IN ('ERROR', 'UNKNOWN')
             OR location       IN ('ERROR', 'UNKNOWN')
           THEN 1 ELSE 0 END)                                   AS sentinels_left
FROM cafe_sales_cleaned;

-- 2b. Did the imputation invent bad money? Compare with a tolerance -- never
--     test currency with =, because floating point makes 0.1 + 0.2 != 0.3.
--     Expect 0.
SELECT COUNT(*) AS integrity_violations
FROM cafe_sales_cleaned
WHERE ABS(quantity * price_per_unit - total_spent) > 0.01;

-- 2c. Headline revenue, to cross-check against the pandas and PySpark runs.
--     Expect 89096.00 across 9,977 revenue-bearing rows.
SELECT
  ROUND(SUM(total_spent), 2)                       AS total_revenue,
  COUNT(total_spent)                               AS rows_with_revenue,
  ROUND(SUM(total_spent) / COUNT(*), 2)            AS avg_order_value
FROM cafe_sales_cleaned;


-- ---------------------------------------------------------------------------
-- STEP 3: persist. Commented out because it needs a catalog you can write to.
-- ---------------------------------------------------------------------------
-- CREATE OR REPLACE TABLE <catalog>.<schema>.cafe_sales_cleaned AS
-- SELECT * FROM cafe_sales_cleaned;
