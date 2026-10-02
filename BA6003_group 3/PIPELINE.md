# HDB Resale Project Pipeline

## 1. End-to-end workflow

```text
HDBResalePrices.csv              HDBPropertyInformation.csv
          │                                  │
          └──────────────┬───────────────────┘
                         ↓
              Schema checks and logging
                         ↓
              Text, date and type cleaning
                         ↓
          Storey, lease, price and age features
                         ↓
       Standardised block-and-street property key
                         ↓
            Validated many-to-one left join
                         ↓
          Quality flags and matched dataset
                         ↓
              SQLite tables and summaries
                         ↓
    Monthly trend / town comparison / price per sqm
                         ↓
             Time-based price prediction model
                         ↓
        Metrics / charts / logs / Streamlit dashboard
```

## 2. Input datasets

`HDBResalePrices.csv` contains transaction-level records, including month, town, flat type, block, street, storey range, floor area, remaining lease and resale price.

`HDBPropertyInformation.csv` contains building-level information, including block, street, completion year, maximum floor level, residential status and dwelling-unit information.

The resale data is the main dataset for price analysis and prediction. The property data is supplementary and is used to add building context.

## 3. Module organisation

### Data loading and schema validation

The pipeline reads the two CSV files and checks that all required fields are available. If a required field is missing, the pipeline stops instead of producing incomplete results.

### Cleaning and feature engineering

The pipeline standardises text, converts dates and numeric variables, parses the storey range and remaining lease and creates analytical features:

- `storey_mid`;
- `remaining_lease_years`;
- `price_per_sqm`;
- `transaction_year`;
- `building_age_at_sale`.

### Data integration

The pipeline creates a normalised property key from block and street. It performs a many-to-one left join and uses `indicator=True` to record whether each transaction matched the property table.

### Database and summaries

The cleaned data is stored in SQLite. The main tables are:

- `resale_transactions`: one row per resale transaction;
- `property_inventory`: one row per building/property record.

Python and SQL summaries are exported as CSV files.

### Model and dashboard

The model uses a chronological train-test split. The dashboard reads the SQLite database, converts `month` to pandas datetime and supports filtering, visualisation and CSV downloads.

The plotting logic is also available as the standalone script `src/generate_figures.py`. It reads pipeline outputs and recreates the four PNG charts, making the visual results reproducible and easy to explain.

## 4. Quality checks and logging

The pipeline checks:

- required columns;
- missing values;
- numeric conversion;
- positive floor area;
- positive resale price;
- valid storey ranges;
- valid remaining lease;
- property matching;
- join cardinality;
- model training and testing sizes.

The join uses:

```python
validate="many_to_one"
```

This reduces the risk of accidental many-to-many joins and duplicated transactions.

Execution messages are printed to the terminal and saved to:

```text
output/pipeline.log
```

The log provides a simple audit trail for row counts, matching rates, quality flags, database creation and model metrics.

## 5. Validation example

The separate file `src/validation_example.py` performs basic post-run checks:

1. confirms that the SQLite database exists;
2. confirms that `resale_transactions` exists;
3. confirms that the table contains records;
4. confirms that required analytical columns exist.

Run it with:

```bash
python src/validation_example.py
```

This test is intentionally simple and demonstrates that the main outputs were created correctly.

## 6. Model evaluation

The model predicts `resale_price` using town, flat type, flat model, floor area, storey midpoint, remaining lease years, lease commencement year and transaction year.

The data is split by time rather than randomly. Older records are used for training and newer records are used for testing. This is intended to reduce future-data leakage.

The metrics are:

- **MAE**: average absolute error in Singapore dollars;
- **RMSE**: error measure that penalises large mistakes more strongly;
- **R²**: explained variation under this test setup, not percentage accuracy.

Current results are approximately:

```text
Training rows: 194,867
Testing rows: 46,952
MAE: S$48,806
RMSE: S$68,866
R²: 0.891
```

## 7. Reliability improvements

The project is more reliable because it:

- validates the input schema;
- makes data types explicit;
- preserves suspicious records with quality flags;
- validates the join relationship;
- reports unmatched properties;
- separates raw data from generated outputs;
- uses time-based model evaluation;
- produces repeatable logs and quality reports;
- checks the generated database with a separate validation script;
- converts database dates to a `DatetimeIndex` before monthly resampling in the dashboard.

## 8. Remaining risks

Some risks remain. The data does not include renovation quality, interior condition, exact MRT distance, view, noise or all neighbourhood characteristics. The property table is a supplementary building snapshot. Without a unique transaction ID, duplicate-looking transactions cannot be classified with certainty. The model may perform differently under future policy, interest-rate or market changes. The output should therefore be treated as an indicative reference rather than an official valuation.

## 9. Presentation summary

> We organised the project into validation, cleaning, feature engineering, data integration, database storage, analysis, modelling and dashboard modules. We added schema checks, join validation, a separate validation example and timestamped logs. These controls reduce errors from invalid fields, incorrect joins, data leakage and silent changes between runs. The remaining risks are mainly missing price drivers, duplicate identification and future market changes.

## Dashboard budget and data quality

The maximum-budget control keeps historical transactions with `resale_price <= budget`; zero disables this control. Empty results show a clear message. Quality cards read `quality_report.json` and describe the complete pipeline run, rather than the filtered subset. Duplicate counts indicate identical input rows and do not establish that those transactions are invalid.
