"""Re-create the four project figures from the pipeline outputs.

Run from the project root:
    python src/generate_figures.py

The script does not download images. Every figure is generated from the
cleaned CSV files produced by ``full_pipeline.py``.
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
FIG = OUT / "figures"


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(OUT / "resale_analysis.csv", parse_dates=["month"])
    monthly = pd.read_csv(OUT / "monthly_summary.csv", parse_dates=["month"])

    plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False,
                         "axes.spines.right": False})

    # Figure 1: time trend from monthly_summary.csv.
    plt.figure(figsize=(10, 5))
    plt.plot(monthly["month"], monthly["median_price"], color="#147d92")
    plt.xticks(monthly["month"][::12], rotation=45)
    plt.ylabel("Median resale price (SGD)")
    plt.title("Monthly median HDB resale price")
    plt.tight_layout()
    plt.savefig(FIG / "01_monthly_price.png")
    plt.close()

    # Figure 2: town comparison from resale_analysis.csv.
    top = d.groupby("town")["resale_price"].median().sort_values().tail(15)
    plt.figure(figsize=(9, 6))
    top.plot.barh(color="#e59b3d")
    plt.xlabel("Median resale price (SGD)")
    plt.title("15 towns with highest median prices")
    plt.tight_layout()
    plt.savefig(FIG / "02_town_prices.png")
    plt.close()

    # Figure 3: actual versus predicted values from test_predictions.csv.
    pred = pd.read_csv(OUT / "test_predictions.csv")
    plt.figure(figsize=(8, 5))
    plt.scatter(pred["actual"], pred["predicted"], s=5, alpha=0.2)
    low = min(pred["actual"].min(), pred["predicted"].min())
    high = max(pred["actual"].max(), pred["predicted"].max())
    plt.plot([low, high], [low, high], "r--")
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.title("Time-based test predictions")
    plt.tight_layout()
    plt.savefig(FIG / "03_actual_predicted.png")
    plt.close()

    # Figure 4: price per square metre distribution.
    plt.figure(figsize=(8, 5))
    plt.hist(d["price_per_sqm"].dropna(), bins=50, color="#147d92")
    plt.xlabel("Price per sqm (SGD)")
    plt.ylabel("Transactions")
    plt.title("Resale price per square metre")
    plt.tight_layout()
    plt.savefig(FIG / "04_price_psqm.png")
    plt.close()
    print(f"Saved four figures to {FIG}")


if __name__ == "__main__":
    main()
