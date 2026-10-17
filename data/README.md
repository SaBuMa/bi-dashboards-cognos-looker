# 📁 Data Dictionary & Lineage

The dataset is a modified subset of the **IBM Accelerator Catalog automotive sample**, provided by the course for a fictional dealership chain (*Swift Auto Traders*, 10 dealerships in Colorado, USA). It is used under the [IBM Developer terms of use](https://developer.ibm.com/terms/ibm-developer-terms-of-use/).

---

## 1. Folders

| Folder | Contents | Used by the dashboards? |
|---|---|---|
| [`raw/`](raw/) | `AU_*` files: the current release of the course data | ✅ Yes, both tools |
| [`legacy/`](legacy/) | Earlier release (lower-case file names, dates shifted 3–4 years earlier) | ❌ No, kept for comparison |

**How do we know which release the dashboards use?** `python analysis/validate_kpis.py --dataset legacy` fails 6 of 15 checks. For example, the legacy files give $78.3M total profit instead of the $78.4M shown on both dashboards. The `AU_*` files pass all 15 checks.

---

## 2. Lineage

```text
                         ┌────────────────────────────────────────────┐
  IBM Accelerator        │  data/raw/  (AU_* files)                   │
  Catalog sample ───────►│  modified subset distributed by the course │
                         └───────┬───────────────┬──────────────┬─────┘
                                 │               │              │
              Cognos: "Auto group data module"   │              │
              (preloaded in Team content/Samples)│              │
                                 │               │              │
                                 ▼               ▼              ▼
                     ┌──────────────────┐ ┌──────────────┐ ┌────────────────┐
                     │ Cognos dashboard │ │ Google Drive │ │ validate_kpis  │
                     │ Sales · Service  │ │ → Sheets     │ │ .py → SQLite   │
                     └──────────────────┘ │ → Looker     │ └────────────────┘
                                          │   Studio     │
                                          └──────────────┘
```

---

## 3. Tables

### `AU_Sales_By_Model.xlsx` (3,000 rows, **main fact table**)

Grain: **one row = one model × one dealer × one month** (5 models × 10 dealers × 60 months, Jan 2021 – Dec 2025).

| Column | Type | Description | Example |
|---|---|---|---|
| `Year` | int | Calendar year | `2025` |
| `Month` | text | Month name | `December` |
| `Date` | datetime | First day of the month, with a stray time component (see §5) | `2025-12-01 23:00` |
| `Model` | text | Car model (5 values) | `Salish` |
| `Dealer ID` | int | FK → `AU_Dealers.Dealer ID` | `1222` |
| `Quantity Sold` | int | Units sold in the month | `9` |
| `Profit` | float | Profit in USD for those units | `27529.0` |

Dashboard use: Sales P1–P5, Service P3.

### `AU_Car_Recalls.xlsx` (163 rows)

Grain: **one row = one recall campaign** for a model and system on a date (Jan 2020 – Dec 2024).

| Column | Type | Description | Example |
|---|---|---|---|
| `Date` | date | Recall date | `2024-12-27` |
| `Car_ID` | int | FK → `AU_Car_Models.Car_ID` | `147160` |
| `System_Affected` | text | Vehicle system (14 values) | `Tires` |
| `Units` | float | Vehicles covered by the recall | `12623.0` |
| `Model` | text | Model name (denormalised; agrees with `Car_ID`) | `Champlain` |

Dashboard use: Service P1 (column chart) and P4 (heat map). Both dashboards label this measure "# of Recalls", but it is the **number of vehicles affected**, not the number of recall campaigns. Counting campaigns gives 32–33 per model.

### `AU_Sentiment.csv` (76,629 rows)

Grain: **one row = one customer review** (Jan 2021 – Dec 2024).

| Column | Type | Description | Example |
|---|---|---|---|
| `Postal Code` | int | Reviewer postal code. All 10 values match a dealer `Zip Code` | `80234` |
| `Date` | date | Review date | `2024-12-31` |
| `Sentiment` | text | `Positive` / `Neutral` / `Negative` | `Negative` |
| `Year` | int | Year of `Date` | `2024` |

Dashboard use: Service P2 (treemap, `COUNT(*)` by `Sentiment`).

### `AU_Bad_Sentiment.xlsx` (10 rows)

| Column | Type | Description | Example |
|---|---|---|---|
| `Keyword` | text | Complaint topic from negative reviews | `Fluid leaks` |
| `Count` | int | Mentions | `981` |

Not on the dashboards; used in [`docs/insights.md`](../docs/insights.md).

### `AU_Dealers.xlsx` (10 rows, dimension)

| Column | Type | Description |
|---|---|---|
| `Dealer ID` | int | Primary key |
| `Country`, `State`, `City`, `Zip Code`, `Address` | text / int | Location (all in Colorado, USA) |
| `Dealer Name` | text | e.g. `Northern Auto Sales` |
| `Contact Name`, `Contact Phone Number` | text | Fictional contact details |
| `Latitude`, `Longitude` | float | Geo-coordinates |

### `AU_Car_Models.xlsx` (5 rows, dimension)

| Column | Type | Description |
|---|---|---|
| `Car_ID` | int | Primary key |
| `Model` | text | `Beaufort`, `Salish`, `Labrador`, `Champlain`, `Hudson` |

### `AU_Daily_Sales.xlsx` (167,934 rows, 16 MB)

Transaction-level sales enriched with weather (Jan 2023 – Dec 2025). Distributed with the course files but **not used by the required visuals**. It is kept here so the full source set is preserved for future analysis (e.g. weather vs. days-to-sale).

| Column group | Columns |
|---|---|
| Keys | `Sales ID`, `Car ID`, `Dealer ID` |
| Time | `Open Date`, `Year`, `Month`, `Month Order` |
| Measures | `Count` (always 1), `Days to Make Sale` |
| Weather | `Temperature (F)`, `Temperature Category`, `Weather Condition`, `Humidity (%)`, `Wind Speed (mph)`, `Wind Gust (mph)`, `Wind Direction`, `Visibility (mi)`, `Wind Chill (F)`, `Precipitation (in)`, `Fog (Y/N)`, `Rain (Y/N)`, `Snow (Y/N)` |

---

## 4. Relationships

```text
  ┌──────────────────┐          ┌──────────────────────┐          ┌──────────────────┐
  │  AU_Car_Models   │          │  AU_Sales_By_Model   │          │   AU_Dealers     │
  │  Car_ID  (PK)    │          │  Model               │◄────────►│  Dealer ID (PK)  │
  │  Model           │◄───┐     │  Dealer ID   (FK)    │  1 : *   │  Zip Code        │
  └──────────────────┘    │     │  Quantity Sold       │          └────────┬─────────┘
                          │     │  Profit              │                   │ 1 : *
                   1 : *  │     └──────────────────────┘                   │ Zip Code =
                          │                                                │ Postal Code
  ┌──────────────────┐    │                                       ┌────────▼─────────┐
  │  AU_Car_Recalls  │    │                                       │   AU_Sentiment   │
  │  Car_ID  (FK) ───┼────┘                                       │  Postal Code     │
  │  System_Affected │                                            │  Sentiment       │
  │  Units           │                                            └──────────────────┘
  └──────────────────┘
```

Models link sales and recalls by **model name**; reviews link to dealers through **postal code** (every review matches exactly one dealer).

---

## 5. Known data-quality issues

Found by [`analysis/validate_kpis.py`](../analysis/validate_kpis.py). None of them change a dashboard KPI, but anyone using the data should know about them.

| # | Table | Issue | Impact | Suggested handling |
|---|---|---|---|---|
| 1 | `AU_Car_Recalls` | **2020 rows are an exact copy of 2021** (same month-day, model, system and units, 33 rows) | Recall totals include ~275K duplicated units (~22%) | Confirm with the data owner, then drop one year |
| 2 | `AU_Car_Recalls` | 30 of 163 rows have **fractional `Units`** (e.g. 2,682.854) | Heat-map maximum shows as 70,422.354 vehicles | Round to whole vehicles in the data layer |
| 3 | `AU_Car_Recalls` | Measure labelled "# of Recalls" is really vehicles affected | Possible misreading by dashboard users | Rename to "Recalled units" or add a campaign-count KPI |
| 4 | `AU_Sales_By_Model` | `Date` has stray hours (`23:00`) and some 2024 dates fall on days 2–15 | None if grouped by `Year` + `Month` (as the dashboards do) | Truncate to month start |
| 5 | All | **Date windows differ**: sales 2021–2025, recalls 2020–2024, sentiment 2021–2024 | Cross-table comparisons by year must use the overlap (2021–2024) | Add a shared date filter |
| 6 | `AU_Dealers` | Dealer 1401 is listed in *Colorado Springs* with zip 80219, which is a Denver zip code | Wrong city on a map visual | Correct the city or zip at the source |
| 7 | `AU_Sentiment` | No review ID, so 45,519 rows are identical to another row | Expected for an event log; not an error | Add a surrogate key if row-level tracking is needed |
