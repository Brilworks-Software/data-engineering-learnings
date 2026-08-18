# Session 04: Cafe Sales Data Cleaning and 10 KPIs

Exercise from Topic 1 / Programming Fundamentals (Part A).

Dataset: [cafe sales dirty data](https://www.kaggle.com/datasets/ahmedmohamed2003/cafe-sales-dirty-data-for-cleaning-training).
10,000 transactions from 2023, deliberately corrupted. The CSV is in `data/` so the notebook
runs without Kaggle credentials.

Everything is in `cafe_sales_kpis.ipynb`, with outputs saved so it can be read on GitHub
without running it.

## Results

Total revenue 89,096.00 across 9,977 usable transactions.

| KPI | Answer |
|---|---|
| 1. Revenue by product | Salad leads, 19,095 (21.4%) |
| 2. Revenue by location | In-Store 30.5% vs Takeaway 29.8%, 39.7% unknown |
| 3. Revenue by payment method | three methods within 0.1pp, about 23% each |
| 4. Weekend vs weekday | per calendar day 233.06 vs 231.69, no real difference |
| 5. Peak sales day | 2023-07-24 by date, Thursday by weekday |
| 6. Best selling item | Coffee, 3,904 units |
| 7. Product revenue contribution | flat, 5 of 8 items to reach 80% |
| 8. Transaction success rate | 90.6% analytics-ready, 99.8% revenue-usable |
| 9. Missing data rate | 12.6% of cells, 69.1% of rows |
| 10. Invalid date percentage | 4.6%, all blanks or sentinels |

## Approach

69% of rows arrive with at least one broken cell, but 99.8% end up usable. `ERROR` and
`UNKNOWN` are converted to real nulls first, then most missing numbers are recalculated:
each item has a fixed price, and `total_spent = quantity * price_per_unit` holds on all
8,544 complete rows. That rebuilds 1,462 numbers and 489 item names.

No rows are deleted. Each row is flagged for what it can be used for, and each KPI filters
on the flag it needs, so a sale with a broken date still counts towards revenue. Missing
labels become `Unknown` and are shown rather than hidden, since 39.7% of revenue has no
location.

The reasoning behind each decision is in the notebook.

## Run it

```bash
pip install -r requirements.txt
jupyter notebook cafe_sales_kpis.ipynb
```
