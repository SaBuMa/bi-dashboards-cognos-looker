-- =====================================================================
--  Swift Auto Traders: every dashboard panel expressed as SQL
-- =====================================================================
--  Each query below reproduces one visual from the Cognos Analytics and
--  Looker Studio dashboards. analysis/validate_kpis.py loads the raw
--  files into an in-memory SQLite database (snake_case column names),
--  runs every block and compares the result with what the dashboards
--  display.
--
--  Block format:   -- name: <panel_id>
--  Dialect:        SQLite (portable to PostgreSQL / BigQuery with
--                  minor date-function changes)
--
--  Tables
--    sales_by_model (year, month, date, model, dealer_id, quantity_sold, profit)
--    car_recalls    (date, car_id, system_affected, units, model)
--    sentiment      (postal_code, date, sentiment, year)
--    dealers        (dealer_id, ..., dealer_name, city, zip_code, ...)
--    car_models     (car_id, model)
--    bad_sentiment  (keyword, count)
-- =====================================================================


-- ---------------------------------------------------------------------
--  SALES DASHBOARD
-- ---------------------------------------------------------------------

-- name: sales_p1_total_profit
-- Panel 1 | KPI card | Profit in millions of USD, 1 decimal place
SELECT
    SUM(profit)                              AS total_profit_usd,
    ROUND(SUM(profit) / 1000000.0, 1)        AS total_profit_musd
FROM sales_by_model;

-- name: sales_p2_quantity_sold
-- Panel 2 | KPI card | Total units sold
SELECT SUM(quantity_sold) AS total_quantity_sold
FROM sales_by_model;

-- name: sales_p3_quantity_by_model
-- Panel 3 | Bar chart | Units sold per model
SELECT model, SUM(quantity_sold) AS quantity_sold
FROM sales_by_model
GROUP BY model
ORDER BY quantity_sold ASC;

-- name: sales_p4_avg_quantity
-- Panel 4 | KPI card | Average units per record
-- Grain of one record = one model x one dealer x one month
SELECT ROUND(AVG(quantity_sold), 2) AS avg_quantity_sold
FROM sales_by_model;

-- name: sales_p5_profit_by_dealer
-- Panel 5 | Column chart | Profit per dealer, ascending
SELECT
    s.dealer_id,
    d.dealer_name,
    d.city,
    ROUND(SUM(s.profit), 2) AS profit
FROM sales_by_model AS s
LEFT JOIN dealers  AS d ON d.dealer_id = s.dealer_id
GROUP BY s.dealer_id, d.dealer_name, d.city
ORDER BY profit ASC;


-- ---------------------------------------------------------------------
--  SERVICE DASHBOARD
-- ---------------------------------------------------------------------

-- name: service_p1_recalls_by_model
-- Panel 1 | Column chart | Recalled units per model
SELECT model, ROUND(SUM(units), 0) AS recalled_units
FROM car_recalls
GROUP BY model
ORDER BY recalled_units DESC;

-- name: service_p2_sentiment
-- Panel 2 | Treemap | Review count per sentiment class
SELECT
    sentiment,
    COUNT(*)                                            AS reviews,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_of_reviews
FROM sentiment
GROUP BY sentiment
ORDER BY reviews DESC;

-- name: service_p3_monthly_qty_profit
-- Panel 3 | Line + column combo | Units and profit per calendar month
-- (all years combined, ordered January -> December)
SELECT
    CAST(strftime('%m', date) AS INTEGER) AS month_num,
    month,
    SUM(quantity_sold)                    AS quantity_sold,
    ROUND(SUM(profit), 2)                 AS profit
FROM sales_by_model
GROUP BY month_num, month
ORDER BY month_num;

-- name: service_p4_recall_heatmap
-- Panel 4 | Heat map / pivot | Recalled units by model x affected system
SELECT
    model,
    system_affected,
    ROUND(SUM(units), 3) AS recalled_units
FROM car_recalls
GROUP BY model, system_affected
ORDER BY recalled_units DESC;


-- ---------------------------------------------------------------------
--  BEYOND THE BRIEF: supporting analysis used in docs/insights.md
-- ---------------------------------------------------------------------

-- name: extra_profit_mix_by_model
-- Share of volume vs share of profit, and profit per unit
SELECT
    model,
    SUM(quantity_sold)                                                     AS quantity_sold,
    ROUND(SUM(profit), 0)                                                  AS profit,
    ROUND(SUM(profit) / SUM(quantity_sold), 0)                             AS profit_per_unit,
    ROUND(100.0 * SUM(quantity_sold) / SUM(SUM(quantity_sold)) OVER (), 1) AS pct_of_units,
    ROUND(100.0 * SUM(profit)        / SUM(SUM(profit))        OVER (), 1) AS pct_of_profit
FROM sales_by_model
GROUP BY model
ORDER BY profit DESC;

-- name: extra_yearly_trend
-- Year-over-year units and profit
SELECT
    year,
    SUM(quantity_sold)    AS quantity_sold,
    ROUND(SUM(profit), 0) AS profit
FROM sales_by_model
GROUP BY year
ORDER BY year;

-- name: extra_negative_sentiment_trend
-- Share of negative reviews per year
SELECT
    year,
    COUNT(*)                                                         AS reviews,
    ROUND(100.0 * SUM(sentiment = 'Negative') / COUNT(*), 1)         AS pct_negative,
    ROUND(100.0 * SUM(sentiment = 'Positive') / COUNT(*), 1)         AS pct_positive
FROM sentiment
GROUP BY year
ORDER BY year;

-- name: extra_recalls_by_system
-- Total recalled units per affected system
SELECT system_affected, ROUND(SUM(units), 0) AS recalled_units
FROM car_recalls
GROUP BY system_affected
ORDER BY recalled_units DESC;

-- name: extra_top_complaints
-- Keywords from negative reviews
SELECT keyword, count
FROM bad_sentiment
ORDER BY count DESC;

-- name: extra_sentiment_by_dealer
-- Review postal codes match dealer zip codes, so sentiment can be
-- attributed to a dealership
SELECT
    d.dealer_id,
    d.dealer_name,
    d.city,
    COUNT(*)                                                  AS reviews,
    ROUND(100.0 * SUM(s.sentiment = 'Negative') / COUNT(*), 1) AS pct_negative
FROM sentiment AS s
JOIN dealers   AS d ON d.zip_code = s.postal_code
GROUP BY d.dealer_id, d.dealer_name, d.city
ORDER BY pct_negative DESC;
