# Ad Campaign Analyzer

A runnable Streamlit portfolio dashboard with Overview, Platform / Channel Comparison, Campaign Details, and Time Series views. All views share inclusive date, channel, and campaign filters. Includes CSV upload and filtered exports.

## Local quick start

Use Python 3.10 or newer. From this project folder:

```sh
python -m venv .venv
```

Activate on macOS/Linux with `source .venv/bin/activate`, or Windows PowerShell with `.venv\Scripts\Activate.ps1`.

```sh
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. To run verification: `python -m unittest -v`.

## Replit

Create a Python Replit project, upload/extract all project files into its root (including `data/` and `.replit`), install with `python -m pip install -r requirements.txt`, then press Run. If the run configuration is not imported, run `streamlit run app.py --server.address 0.0.0.0 --server.port 8501` in the shell and open the web preview.

## Source and schema

Bundled CSV downloaded from https://exploremydata.com/datasets/marketing-campaigns-1000.csv. Documentation: https://exploremydata.com/datasets/marketing-campaigns. Synthetic, generated demonstration data; CC0. The downloaded copy is included so startup needs no network connection. Campaigns can span channels. Channels are not named advertising platforms.

Required columns: `date,campaign,channel,impressions,clicks,spend,conversions,revenue`. Currency is USD. Uploaded data must use the same schema; confirm its currency and attribution definitions. Counts may be numeric decimals; no values are rounded during calculations.

## Metric definitions

All ratios use sums of matching eligible rows. CTR = clicks/impressions ×100; CPC = spend/clicks; CPM = spend/impressions ×1000; CVR = conversions/clicks ×100; CPA = spend/conversions; ROAS = revenue/spend; advertising ROI = (revenue−spend)/spend ×100. Revenue less ad cost = revenue−spend; revenue per conversion = revenue/conversions; revenue per click = revenue/clicks. Segment shares divide segment totals by the current filtered totals. Zero denominators return N/A, never infinity or zero.

Advertising ROI excludes non-advertising costs and is not full business ROI or net profitability. Conversions are not guaranteed to be orders or new customers.

## Preparation policy

Raw data is never overwritten. Invalid/missing dates, empty campaign/channel labels, missing/nonfinite numeric measures, and negative numeric values exclude a record from the common analytical population. Missing values are not imputed. Included/excluded counts and previews are visible. Exact duplicates are reported and retained. Clicks above impressions and conversions above clicks are flagged and retained without silent correction. Numeric parsing accepts plain numeric values as specified by the schema, not currency-formatted strings. Invalid uploads receive an actionable error.

Daily/weekly/monthly totals use the same records and recalculate ratios. Weeks start Monday. Partial periods are labeled; absent reporting dates are not filled with assumed zeros. Rankings have a configurable conversion threshold that does not change dashboard totals. No predictive, causal, or automated budget recommendations are made.

## Requirements mapping

| Brief requirement | Implementation |
|---|---|
| Campaign CSV input | Bundled ExploreMyData CSV plus upload |
| Spend, clicks, conversions, ROI | KPI cards, comparisons, details and trends |
| Overview | Overview tab |
| Platform comparison | Platform / Channel Comparison tab; actual data identifies channels |
| Campaign details | Selector, channel breakdown, daily records and comparison |
| Time-series views | Daily, Monday-weekly and monthly charts and export |
| Shared filters | Sidebar date/channel/campaign filters apply to every tab |
| AI coding assistant | Built with Codex; ready for Replit |

The brief's solution-kit link was not supplied, so kit-specific requirements were not assessed. Literal Google Ads-versus-Meta comparison would require a platform column with those values. This project transparently compares the supplied channels.
