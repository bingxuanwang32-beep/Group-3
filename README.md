# HDB Atlas

HDB Atlas is an interactive dashboard for exploring Singapore HDB resale transactions. Built for the BA6003 group project, it combines a Streamlit interface with a SQLite data pipeline to help users explore housing market trends and transaction data.

**Live app:** [Open HDB Atlas](https://group-3-djlqszijzhac29etmwie9y.streamlit.app/)

## Features

- Explore HDB resale transaction data through interactive dashboard pages.
- Filter data and view summary statistics and visualisations.
- Use the optional AI chat box to ask questions about the figures shown in the dashboard. The app uses calculated summaries and the selected filters to provide context for its responses.
- Process source data into a SQLite database for dashboard use.

## Project structure

```text
BA6003_group 3/
├── data/
│   └── raw/                 # Source data used by the pipeline
├── output/
│   ├── hdb_full.sqlite      # Processed database used by the dashboard
│   └── quality_report.json  # Data quality summary
├── src/
│   └── dashboard.py         # Streamlit dashboard
├── PIPELINE.md              # Pipeline instructions
├── README.md
└── requirements.txt
