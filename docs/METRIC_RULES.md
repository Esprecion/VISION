# Metric colour rules

These rules are the approved red/amber/green (RAG) definitions for the MVP. Thresholds are inclusive. When a metric aggregates child rows (stages, clients, categories), the worst child colour wins.

- **Green** means the metric is inside its target band and its source loaded successfully.
- **Amber** means the metric is inside the warning band, or the source returned no rows.
- **Red** means the metric is outside the acceptable band, or its source failed to load.

## Dashboard KPIs

| Metric | Direction | Green | Amber | Red |
| --- | --- | --- | --- | --- |
| Product Type Performance (top type value) | Higher | ≥ ₱100,000 | ₱25,000–₱99,999.99 | < ₱25,000 |
| Geographic Distribution (top territory value) | Higher | ≥ ₱100,000 | ₱25,000–₱99,999.99 | < ₱25,000 |
| Deals per Stage (per stage) | Higher | ≥ 5 | 1–4 | 0 |
| Open Deal Value | Higher | ≥ ₱500,000 | ₱100,000–₱499,999.99 | < ₱100,000 |
| Draft Contracts | Higher | ≥ 3 | 1–2 | 0 |
| Finalized Contracts | Higher | ≥ 5 | 1–4 | 0 |
| On-time Delivery Rate | Higher | ≥ 90% | 70–89.99% | < 70% |
| Average Project Cycle Time | Lower | ≤ 30 days | 31–60 days | > 60 days |
| Active Client Count | Higher | ≥ 10 | 5–9 | < 5 |
| Tool and API Cost Trend (latest month) | Lower | ≤ ₱50,000 | ₱50,000.01–₱100,000 | > ₱100,000 |
| Revenue per Client (top client total) | Higher | ≥ ₱100,000 | ₱50,000–₱99,999.99 | < ₱50,000 |
| Total Revenue by Period (latest month) | Higher | ≥ ₱250,000 | ₱100,000–₱249,999.99 | < ₱100,000 |
| Accounts Receivable Aging (worst days overdue) | Lower | ≤ 0 days | 1–30 days | > 30 days |
| Net Burn Rate (latest month) | Lower | ≤ 0 | ₱0.01–₱50,000 | > ₱50,000 |
| Project Profitability (margin) | Higher | ≥ 20% | 0–19.99% | < 0% |
| Expense by Category (top category total) | Lower | ≤ ₱50,000 | ₱50,000.01–₱100,000 | > ₱100,000 |

The four metrics hidden from the MVP (Conversion Rate, Average Time per Pipeline Stage, Client Pipeline Velocity and Client Tenure) keep their data and code but do not render indicators while hidden.

## Import accuracy

Field accuracy is `correct fields / total expected fields`.

- **Green:** accuracy ≥ 95%.
- **Amber:** accuracy ≥ 80% and < 95%.
- **Red:** accuracy < 80%.

Comparison rules are in [benchmarks/imports/README.md](../benchmarks/imports/README.md).
