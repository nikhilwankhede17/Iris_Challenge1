"""
Analyze ambiguous dates and propose resolution strategy.

The goal is to understand if the ambiguous dates near the cutoff
are actually misclassified or if the ambiguity can be resolved.
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import OUTPUT_DIR

# Load the parsed data
df = pd.read_csv(OUTPUT_DIR / "data_with_parsed_dates.csv")
df['order_date_parsed'] = pd.to_datetime(df['order_date_parsed'])

print("=" * 80)
print("AMBIGUOUS DATE ANALYSIS")
print("=" * 80)
print()

# Get all ambiguous dates
ambiguous_df = df[df['date_parse_status'] == 'ambiguous'].copy()

print(f"Total ambiguous dates: {len(ambiguous_df):,}")
print()

# Analyze the patterns
print("Sample of ambiguous dates with their parsed values:")
print("-" * 80)
sample = ambiguous_df[['order_date', 'order_date_parsed']].head(20)
for _, row in sample.iterrows():
    orig = row['order_date']
    parsed = row['order_date_parsed']
    print(f"  Original: {orig:15} -> Parsed as: {parsed}")
print()

# Check dates near cutoff
cutoff = pd.Timestamp('2025-09-30')
window_days = 14
lower_bound = cutoff - pd.Timedelta(days=window_days)
upper_bound = cutoff + pd.Timedelta(days=window_days)

ambiguous_near_cutoff = ambiguous_df[
    (ambiguous_df['order_date_parsed'] >= lower_bound) &
    (ambiguous_df['order_date_parsed'] <= upper_bound)
].copy()

print(f"Ambiguous dates near cutoff (Sep 16 - Oct 14): {len(ambiguous_near_cutoff)}")
print()

if len(ambiguous_near_cutoff) > 0:
    print("CRITICAL DATES NEAR CUTOFF:")
    print("-" * 80)
    critical = ambiguous_near_cutoff[['order_date', 'order_date_parsed']].drop_duplicates()
    for _, row in critical.iterrows():
        orig = row['order_date']
        parsed = row['order_date_parsed']
        
        # Check if this could be interpreted differently
        parts = orig.split('-')
        if len(parts) == 3:
            # Parsed as mm-dd-yyyy, could also be dd-mm-yyyy
            try:
                # Alternative interpretation: dd-mm-yyyy
                alternative = pd.to_datetime(f"{parts[2]}-{parts[1]}-{parts[0]}")
                before_cutoff = parsed <= cutoff
                alt_before_cutoff = alternative <= cutoff
                
                conflict = before_cutoff != alt_before_cutoff
                
                print(f"  Original: {orig}")
                print(f"    Parsed as (mm-dd-yyyy): {parsed.date()} -> {'HISTORICAL' if parsed <= cutoff else 'FUTURE'}")
                print(f"    Could be (dd-mm-yyyy):  {alternative.date()} -> {'HISTORICAL' if alternative <= cutoff else 'FUTURE'}")
                if conflict:
                    print(f"    *** CONFLICT: Different period classification! ***")
                print()
            except:
                print(f"  Original: {orig} -> Parsed as: {parsed.date()}")
                print()

print()
print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()

# Count how many records would be affected
total_ambiguous = len(ambiguous_df)
ambiguous_near_cutoff_count = len(ambiguous_near_cutoff)

print(f"Out of 5,120 total records:")
print(f"  - {total_ambiguous} ({total_ambiguous/5120*100:.2f}%) have ambiguous dates")
print(f"  - {ambiguous_near_cutoff_count} ({ambiguous_near_cutoff_count/5120*100:.2f}%) are ambiguous AND near cutoff")
print()

print("PROPOSED RESOLUTION:")
print("1. Since ambiguous dates use format mm-dd-yyyy (U.S. convention),")
print("   but the data appears to be from India (cities: Mumbai, Delhi, etc.),")
print("   the dd-mm-yyyy (day-first) interpretation is more likely correct.")
print()
print("2. OPTION A: Re-parse all ambiguous dates assuming dd-mm-yyyy format")
print("   - Safer for Indian e-commerce data")
print("   - More consistent with other dates in dataset")
print()
print("3. OPTION B: Exclude ambiguous dates entirely")
print("   - Most conservative approach")
print("   - Would lose 2.77% of data")
print()
print("4. OPTION C: Manually inspect and correct critical dates near cutoff")
print("   - Only 14 dates need inspection")
print("   - Most accurate but requires manual review")
print()

# Save detailed analysis
analysis_file = OUTPUT_DIR / "ambiguous_dates_analysis.txt"
with open(analysis_file, 'w') as f:
    f.write("Ambiguous Dates Near Cutoff (Sep 16 - Oct 14, 2025)\\n")
    f.write("=" * 80 + "\\n\\n")
    for _, row in ambiguous_near_cutoff.iterrows():
        f.write(f"Order ID: {row['order_id']}\\n")
        f.write(f"  Original date: {row['order_date']}\\n")
        f.write(f"  Parsed as: {row['order_date_parsed']}\\n")
        f.write(f"  Customer: {row['customer_id']}\\n")
        f.write(f"  Status: {row['order_status']}\\n")
        f.write("\\n")

print(f"Detailed analysis saved to: {analysis_file}")
