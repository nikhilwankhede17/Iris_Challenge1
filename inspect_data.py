"""
Initial data inspection script to understand the dataset structure and quality.
"""
import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv('data/Challenge 1 - Churn Data (AIML).csv')

print('='*80)
print('DATE FORMAT ANALYSIS')
print('='*80)
print('Sample date values and their patterns:\n')

# Get unique date patterns
dates = df['order_date'].dropna().unique()
print(f'Total unique dates: {len(dates)}\n')

# Categorize by pattern
patterns = {}
for date in dates[:50]:  # Sample first 50
    if '-' in date:
        parts = date.split('-')
        if len(parts) == 3:
            pattern = f'{len(parts[0])}d-{len(parts[1])}d-{len(parts[2])}d'
            if pattern not in patterns:
                patterns[pattern] = []
            patterns[pattern].append(date)

print('Detected patterns:')
for pattern, examples in patterns.items():
    print(f'  {pattern}: {examples[:5]}')
print()

print('='*80)
print('DATA QUALITY CHECKS')
print('='*80)
print()

print('1. Quantity distribution:')
print(df['quantity'].describe())
neg_qty = (df['quantity'] <= 0).sum()
print(f'   Negative or zero quantities: {neg_qty}\n')

print('2. Unit price distribution:')
print(df['unit_price'].describe())
neg_price = (df['unit_price'] < 0).sum()
zero_price = (df['unit_price'] == 0).sum()
print(f'   Negative prices: {neg_price}')
print(f'   Zero prices: {zero_price}\n')

print('3. Discount distribution:')
print(df['discount_pct'].describe())
disc_over = (df['discount_pct'] > 100).sum()
disc_neg = (df['discount_pct'] < 0).sum()
print(f'   Discounts > 100: {disc_over}')
print(f'   Negative discounts: {disc_neg}\n')

print('4. Order status distribution:')
print(df['order_status'].value_counts())
print()

print('5. Duplicate order_id check:')
print(f'   Total orders: {len(df)}')
print(f'   Unique order_ids: {df["order_id"].nunique()}')
print(f'   Duplicate order_ids: {len(df) - df["order_id"].nunique()}\n')

print('6. Customer counts:')
print(f'   Unique customer_ids: {df["customer_id"].nunique()}')
