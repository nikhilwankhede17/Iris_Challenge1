"""
Run complete data quality audit.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import load_and_parse_dates
from src.data_cleaning import (
    analyze_duplicates,
    analyze_invalid_values,
    analyze_missing_values,
    generate_audit_report
)
from src.config import OUTPUT_DIR

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("RUNNING DATA QUALITY AUDIT")
print("=" * 80)
print()

# Load data with parsed dates
print("1. Loading and parsing dates...")
df, date_report = load_and_parse_dates()
print(f"   [OK] Loaded {len(df):,} records")
print(f"   [OK] All {date_report['ok_count']:,} dates parsed successfully")
print()

# Analyze duplicates
print("2. Analyzing duplicates...")
dup_report = analyze_duplicates(df)
print(f"   Found {dup_report['duplicate_order_ids_count']} duplicate order_ids")
print(f"   - Exact duplicates: {dup_report['exact_duplicate_records']}")
print(f"   - Conflicting duplicates: {dup_report['conflicting_duplicate_records']}")
print()

# Analyze invalid values
print("3. Analyzing invalid values...")
invalid_report = analyze_invalid_values(df)
print(f"   Quantity issues:")
print(f"     - Negative: {invalid_report['quantity']['negative_count']}")
print(f"     - Zero: {invalid_report['quantity']['zero_count']}")
print(f"     - High: {invalid_report['quantity']['high_count']}")
print(f"   Price issues:")
print(f"     - Negative: {invalid_report['price']['negative_count']}")
print(f"     - Zero: {invalid_report['price']['zero_count']}")
print(f"     - High: {invalid_report['price']['high_count']}")
print(f"   Discount issues:")
print(f"     - Negative: {invalid_report['discount']['negative_count']}")
print(f"     - Over 100%: {invalid_report['discount']['high_count']}")
print()

# Analyze missing values
print("4. Analyzing missing values...")
missing_report = analyze_missing_values(df)
print(f"   Columns with missing values: {missing_report['columns_with_missing']}")
for col, stats in missing_report['missing_by_column'].items():
    print(f"     - {col}: {stats['count']} ({stats['percentage']:.2f}%)")
print()

# Generate comprehensive report
print("5. Generating audit report...")
audit_text = generate_audit_report(df, dup_report, invalid_report, missing_report)

# Save to file
audit_file = OUTPUT_DIR / "data_quality_audit.txt"
with open(audit_file, 'w') as f:
    f.write(audit_text)

print(f"   [OK] Audit report saved to: {audit_file}")
print()

print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
print()
print("Next steps:")
print("1. Review the audit report")
print("2. Make decisions on handling duplicates and invalid values")
print("3. Implement cleaning logic")
print("4. Proceed to feature engineering and target construction")
