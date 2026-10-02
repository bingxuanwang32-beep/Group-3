"""Small validation example for explaining the cleaning rules to a professor."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "output" / "quality_report.json"
ISSUES = ROOT / "output" / "quality_issues.csv"

report = json.loads(REPORT.read_text(encoding="utf-8"))
issues = pd.read_csv(ISSUES)
print("Quality report")
for key, value in report.items():
    print(f"{key}: {value}")
print("\nFlag counts")
print(issues["quality_issue"].value_counts().to_string())
