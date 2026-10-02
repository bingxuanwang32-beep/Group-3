# HDB Resale Price Analytics and Prediction Project

This project builds an end-to-end HDB resale price analytics tool. It combines transaction-level resale data with building-level property information, produces descriptive market analysis, trains an indicative price-prediction model and provides an interactive Streamlit dashboard.

The workflow is:

> Raw data → Validation → Cleaning → Feature engineering → Data integration → SQLite → Analysis → Machine learning → Dashboard → Business insight

## 1. Project structure

```text
HDB_Project_Full_English_Logging_Fixed/
├── data/raw/
│   ├── HDBResalePrices.csv
│   └── HDBPropertyInformation.csv
├── output/
├── src/
│   ├── full_pipeline.py
│   ├── full_pipeline_with_logging.py
│   ├── dashboard.py
│   ├── generate_figures.py
│   └── validation_example.py
├── PIPELINE.md
├── README.md
├── requirements.txt
└── .venv/
```

The raw CSV files are input files. The pipeline does not overwrite them. Generated tables, charts, databases, reports and logs are written to `output/`.

## 2. Environment setup in VS Code

Open this project folder in VS Code. Open **Terminal → New Terminal** and run the commands one at a time:

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt
```

If the terminal begins with `(.venv)`, the environment is active.

Check the installation:

```bash
python -c "import pandas, sklearn, streamlit; print('Environment OK')"
```

If you see `unrecognized subcommand 'venu'`, the command was misspelled. The correct command is `uv venv`.

## 3. Run the full pipeline

Run this command from the project root:

```bash
python src/full_pipeline.py
```

The script performs the following steps:

1. load both CSV files;
2. check the required columns;
3. standardise text, dates and numerical fields;
4. create storey, lease, price-per-square-metre and building-age features;
5. match transactions to building information;
6. save cleaned data and a SQLite database;
7. produce market summaries and charts;
8. train and evaluate a Random Forest model;
9. write timestamped execution logs and quality reports.

The complete run can take several minutes because the model is trained on a large transaction dataset.

To recreate only the four PNG figures after the pipeline has finished, run:

```bash
python src/generate_figures.py
```

The script reads `output/resale_analysis.csv`, `output/monthly_summary.csv` and `output/test_predictions.csv`. It creates the four files in `output/figures/`: a monthly trend, town comparison, actual-versus-predicted scatter plot and price-per-square-metre histogram.

## 4. Run the validation example

After the main pipeline finishes, run:

```bash
python src/validation_example.py
```

This reads `quality_report.json` and `quality_issues.csv` and prints the run summary and quality-issue counts. It is useful when explaining how the cleaning rules were checked.

## 5. Run the dashboard

Start the dashboard in the VS Code terminal:

```bash
python -m streamlit run src/dashboard.py
```

Open the `Local URL` shown in the terminal, normally:

```text
http://localhost:8501
```

The dashboard allows users to:

- filter by town;
- filter by flat type;
- filter by floor area;
- set a maximum budget (0 disables the budget filter);
- view data quality counts, matching rate, date range and duplicates;
- view transaction count;
- view median price;
- view median price per square metre;
- view the monthly median price chart;
- view filtered transaction records;
- download filtered records as a CSV file.

The dashboard explicitly converts the `month` field to a pandas datetime field before monthly resampling. This prevents the `DatetimeIndex` error that occurs when a string column is used with `.resample()`.

Stop the dashboard with:

```text
Control + C
```

## 6. Cleaning and feature engineering

The pipeline standardises text fields by removing unnecessary spaces and converting relevant text to uppercase. It converts `month` to a date, `floor_area_sqm` and `resale_price` to numeric variables, and checks that values are positive.

It transforms:

- `storey_range` into `storey_mid`, the midpoint of the range;
- `remaining_lease` into `remaining_lease_years`;
- `resale_price` and `floor_area_sqm` into `price_per_sqm`;
- `month` into `transaction_year`;
- transaction year and completion year into `building_age_at_sale`.

The formulas are:

```text
price_per_sqm = resale_price / floor_area_sqm
building_age_at_sale = transaction_year - year_completed
```

Missing prices and areas are not replaced with zero because zero would distort the analysis.

## 7. Data integration

The transaction data and property data are joined using a standardised key based on block and street. The join is a many-to-one left join:

- many transactions can belong to one building;
- one building key should not unexpectedly match multiple building records;
- unmatched transactions remain visible and are exported for review.

The code uses `validate="many_to_one"` and `indicator=True`. These controls help detect incorrect joins and unexpected row duplication.

## 8. Outputs

| File | Purpose |
|---|---|
| `output/resale_cleaned_all.csv` | All cleaned transactions with quality flags |
| `output/resale_analysis.csv` | Records passing quality checks and property matching |
| `output/quality_issues.csv` | Records requiring review |
| `output/unmatched_property_records.csv` | Transactions without a matching property record |
| `output/hdb_full.sqlite` | SQLite database with transaction and property tables |
| `output/monthly_summary.csv` | Monthly mean price, median price and transaction count |
| `output/town_flat_summary.csv` | Median price and price-per-square-metre summaries |
| `output/model_metrics.json` | Training size, test size, MAE, RMSE and R² |
| `output/test_predictions.csv` | Actual and predicted prices for the test set |
| `output/quality_report.json` | Data-quality and run summary |
| `output/pipeline.log` | Timestamped pipeline log messages |
| `output/figures/` | Four report-ready visualisations |

## 9. Logging

The full pipeline writes messages to both the terminal and `output/pipeline.log`.

The log records:

- when the pipeline starts and finishes;
- how many rows were loaded from each file;
- whether required columns were verified;
- the property matching rate;
- the number of unmatched records;
- the number of rows passing quality checks;
- the SQLite database creation;
- the model training and testing sizes;
- the MAE, RMSE and R² values.

Example:

```text
INFO | Pipeline started
INFO | Loaded resale data: 241822 rows
INFO | Loaded property data: 13357 rows
INFO | Property matching rate: 99.9988%
INFO | SQLite database created
INFO | Model metrics: MAE=48806.17 RMSE=68865.97 R2=0.891
INFO | Pipeline completed successfully
```

## 10. Model and current results

The target variable is `resale_price`. The model uses town, flat type, flat model, floor area, storey midpoint, remaining lease years, lease commencement year and transaction year.

The data is split chronologically rather than randomly. Older transactions are used for training and newer transactions are used for testing. This reduces future-data leakage.

The current run contains:

- 241,822 raw resale records;
- 241,819 records used for analysis;
- 318 exact duplicate-looking rows;
- 3 records flagged for review;
- a property matching rate of 99.9988%;
- 194,867 training records;
- 46,952 testing records.

The current test metrics are approximately:

- MAE: S$48,806;
- RMSE: S$68,866;
- R²: 0.891.

MAE is the average absolute prediction error. RMSE penalises large errors more heavily. R² describes the proportion of variation explained under this test setup; it is not an accuracy percentage.

## 11. Testing and coding risks

The pipeline reduces the following risks:

- missing or renamed columns;
- incorrect data types;
- invalid prices, areas, dates or lease values;
- accidental many-to-many joins;
- silent deletion of suspicious records;
- future-data leakage;
- overwriting source data;
- inability to identify changes between runs.

## 12. Limitations

The data does not include every factor affecting price, including renovation quality, interior condition, exact MRT distance, view, noise and nearby-school quality. The building data is supplementary and may not represent the exact condition at the time of each transaction. Duplicate-looking records cannot be confidently removed without a unique transaction ID. Market conditions can change, so historical model performance may not continue in the future.

The dashboard supports comparison and decision-making. It is an indicative analytical tool, not an official HDB valuation or a guaranteed market price.

## Budget and quality interpretation

Budget filters historical transactions by observed resale price, not current listings. All market cards, the monthly chart and CSV downloads follow the same budget filter. The data quality summary describes the full input dataset and is independent of sidebar filters. Duplicate-looking rows are counted, not automatically removed, because distinct sales may share identical recorded attributes.
