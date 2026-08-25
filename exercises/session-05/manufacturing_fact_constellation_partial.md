# Manufacturing Industry — Fact Constellation Example

A global industrial manufacturing enterprise specialising in high-end electric components operates four different manufacturing plants across North America and Europe. Each plant was acquired at a different time, resulting in a fragmented operational ecosystem:

- **Plant A** uses a modern ERP system (SAP) and tracks assembly runs manually in Excel.
- **Plant B** uses a legacy MES (Manufacturing Execution System) that logs machine telemetry but dumps it into a text file every midnight.
- **Plant C** tracks quality inspections using a local SQL database, but uses entirely different part numbers (internal codes) than the central billing team.

---

## Business Issue 1: Scrap Untraceability

The Chief Financial Officer (CFO) notices a massive, unexplained spike in **"Unallocated Material Losses"** hitting the corporate balance sheet.

### The Problem

Quality inspection data lives in isolated shop-floor silos. There is no correlated data to identify which specific batch of industrial motors caused the failure, which plant produced them, or what the standard material cost loss was.

### Impact

Untraceability of the root cause of production failure patterns.

---

## Business Issue 2: Faulty Vendor Finger-Pointing

Threats of contract cancellation because of a shipment of defective components in breach of SLA.

### The Problem

Plant managers blame a raw material supplier for delivering substandard copper coils. The procurement team defends the vendor, claiming the breakdown happened because Plant B ran the assembly lines too hot to meet quarterly quotas.

### Impact

Because production speed metrics (`downtime_minutes`, `units_produced`) are not integrated with quality telemetry (`failed_units`), it is impossible to run a point-in-time cross-analysis to prove whether speed or material caused the failure.

---

## Business Issue 3: Erroneous OEE Benchmarking

Corporate leadership wants to award an efficiency bonus to the highest-performing plant based on Overall Equipment Effectiveness (OEE).

### The Problem

Each plant calculates "downtime" differently. One plant counts scheduled maintenance as downtime; another does not.

### Impact

The company cannot fairly benchmark plant performance, leading to low employee morale, misallocated capital investments, and skewed operational targets.

---

# Existing Tables in Silver Layer

```text
┌─────────────────────────────┐
│ silver_erp_products         │
├─────────────────────────────┤
│ product_id                  │
│ sku                         │
│ product_name                │
│ category                    │
│ standard_cost               │
│ unit_of_measure             │
│ created_at                  │
│ updated_at                  │
└─────────────────────────────┘

┌─────────────────────────────┐
│ silver_erp_suppliers        │
├─────────────────────────────┤
│ supplier_id                 │
│ supplier_name               │
│ supplier_tier               │
│ supplier_country            │
│ supplier_city               │
│ supplier_status             │
└─────────────────────────────┘

┌─────────────────────────────┐
│ silver_erp_purchase_orders  │
├─────────────────────────────┤
│ purchase_order_id           │
│ supplier_id                 │
│ order_date                  │
│ expected_delivery           │
│ status                      │
└─────────────────────────────┘

┌─────────────────────────────┐
│ silver_erp_supplier_batches │
├─────────────────────────────┤
│ batch_receipt_id            │
│ purchase_order_id           │
│ supplier_id                 │
│ raw_material_sku            │
│ batch_lot_number            │
│ quantity_received           │
│ received_date               │
│ expiry_date                 │
│ inspection_status           │
└─────────────────────────────┘

┌──────────────────────────────────────┐
│ silver_part_number_xref              │
├──────────────────────────────────────┤
│ internal_sku    (Plant C local code) │
│ canonical_sku   (silver_erp_products │
│                  .sku — ERP code)    │
│ plant_id        (which plant uses    │
│                  this internal code) │
│ source_system   (e.g. 'MES_PLANT_C') │
└──────────────────────────────────────┘

┌─────────────────────────────┐
│ silver_mes_plants           │
├─────────────────────────────┤
│ plant_id                    │
│ plant_name                  │
│ region_name                 │
│ country                     │
└─────────────────────────────┘

┌─────────────────────────────┐
│ silver_mes_work_centers     │
├─────────────────────────────┤
│ work_center_id              │
│ plant_id                    │
│ work_center_name            │
│ machine_type                │
│ hourly_capacity_target      │
│ scheduled_hours_per_shift   │
└─────────────────────────────┘

┌─────────────────────────────┐
│ silver_mes_production_events│
├─────────────────────────────┤
│ production_event_id         │
│ product_id                  │
│ work_center_id              │
│ shift_code                  │
│ local_date                  │
│ event_timestamp             │
│ production_start            │  
│ production_end              │  
│ total_counted_units         │
│ scrap_units                 │
│ planned_downtime_minutes    │
│ unplanned_downtime_minutes  │
│ operator_id                 │
└─────────────────────────────┘

┌─────────────────────────────────┐
│ silver_mes_material_consumption │
├─────────────────────────────────┤
│ consumption_event_id            │
│ production_event_id             │
│ raw_material_sku                │
│ batch_lot_number                │
│ quantity_used                   │
│ scan_timestamp                  |
│ canonical_sku                   |
| supplier_id                     |
└─────────────────────────────────┘

┌────────────────────────────────┐
│ silver_mes_quality_inspections │
├────────────────────────────────┤
│ inspection_id                  │
│ production_event_id            │
│ product_id                     │
│ inspection_timestamp           │
│ units_sampled                  │
│ units_failed                   │
│ defect_reason_code             │
│ defect_category                │
│ inspector_id                   │
└────────────────────────────────┘
```

---

# Proposed Solution

To fix these gaps, we transition to a **Fact Constellation Schema** (also called a Galaxy Schema). Three fact tables share a set of conformed dimensions.

```text
         ┌──────────────┐    ┌─────────────────┐
         │   dim_date   │    │   dim_supplier   │
         └──────┬───────┘    └────────┬─────────┘
                │                     │
         ┌──────┴──────────────────────┴──────────────────┐
         │              dim_product (SCD Type 2)           │
         └──────┬──────────────────────────────────────────┘
                │
         ┌──────▼──────────────────────────────────────────┐
         │                 fact_production                  │
         │  (plant_key, work_center_key, date_key,         │
         │   product_key, shift_code[DD])                  │
         └──────────┬────────────────┬──────────────────────┘
                    │                │
         ┌──────────▼──┐    ┌────────▼───────────────┐
         │fact_quality_ │    │ fact_component_consumed│
         │inspection    │    │                        │
         └──────────────┘    └────────────────────────┘

         [DD] = Degenerate Dimension (no separate dim table)

         Shared by all three facts:
         ┌───────────────┐   ┌───────────────┐
         │   dim_plant   │   │dim_work_center│
         └───────────────┘   └───────────────┘
```

> **Note on diagram:** `dim_plant` and `dim_work_center` are used by **all three** fact tables — `fact_production` directly, and `fact_quality_inspection` and ``fact_component_consumed` through their `production_key` join to `fact_production` at query time (or by denormalising `plant_key` and `work_center_key` onto those facts for performance).

---
# Exercise: Design Resolution of Business Issues

## Issue 1: Scrap Untraceability

**How it works:** Detects unallocated material loss.
Tie the scrapped units back to the specific vendor batch.
Turn an anonymous balance sheet line item into a traceable, addressable shop-floor problem.

## Issue 2: Faulty Vendor Finger-Pointing

**How it works:** Identify the batch lot number used during a time window
Compare failure rates across Vendor A vs Vendor B copper coil batches on the same machine.
Isolate whether the fault lies with vendor quality or machine overheating.

## Issue 3: Erroneous OEE Benchmarking

**How it works:** Enforce an enterprise-wide standard OEE definition using conformed measures:

```
Planned Production Time  =  scheduled_hours_per_shift × 60 minutes
                            [per shift, per work centre]

Availability  =  (Planned Production Time − unplanned_downtime_minutes)
                 ─────────────────────────────────────────────────────
                          Planned Production Time

Performance   =  units_produced
                 ─────────────────────────────────────────────────────
                 (Planned Production Time − unplanned_downtime_minutes)
                 × standard_hourly_capacity

Quality       =  (units_produced − failed_units from fact_quality_inspection)
                 ─────────────────────────────────────────────────────
                          units_produced

OEE = Availability × Performance × Quality
```
---
