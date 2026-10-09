"""
Test script to validate date parsing on the actual CSV.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import load_and_parse_dates, check_cutoff_date_reliability, generate_date_parsing_report
from src.config import HISTORICAL_END_DATE, OUTPUT_DIR

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading and parsing dates from CSV...")
df, parse_report = load_and_parse_dates()

print(f"\nLoaded {len(df):,} records")
print(f"Successfully parsed: {parse_report['ok_count']:,}")
print(f"Ambiguous: {parse_report['ambiguous_count']:,}")
print(f"Unparseable: {parse_report['unparseable_count']:,}")
print(f"Missing: {parse_report['missing_count']:,}")

print("\nChecking cutoff date reliability...")
cutoff_report = check_cutoff_date_reliability(df, HISTORICAL_END_DATE)

print(f"Records near cutoff (±14 days): {cutoff_report['total_records_in_window']:,}")
print(f"Ambiguous near cutoff: {cutoff_report['ambiguous_count']:,}")

# Generate full report
report_text = generate_date_parsing_report(df, parse_report, cutoff_report)
print("\n" + report_text)

# Save report to file
report_file = OUTPUT_DIR / "date_parsing_report.txt"
with open(report_file, 'w') as f:
    f.write(report_text)

print(f"\n[OK] Report saved to: {report_file}")

# Save parsed data for next steps
parsed_data_file = OUTPUT_DIR / "data_with_parsed_dates.csv"
df.to_csv(parsed_data_file, index=False)
print(f"[OK] Parsed data saved to: {parsed_data_file}")

# Check if we should proceed or stop
if parse_report['unparseable_count'] > 0:
    print("\nWARNING: Some dates could not be parsed.")
    print("   Review unparseable dates before proceeding.")

if cutoff_report['ambiguous_count'] > 0:
    print("\nCRITICAL: Ambiguous dates found near the September 30 cutoff!")
    print("   These could affect historical vs future classification.")
    print("   STOP and resolve before generating target variable.")
else:
    print("\n[OK] All dates near cutoff are reliable.")
    print("  Safe to proceed to target construction.")
