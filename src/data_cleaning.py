"""
Data cleaning and quality audit module.

This module handles:
1. Duplicate detection and analysis
2. Invalid value detection (quantities, prices, discounts)
3. Missing value analysis
4. Data cleaning with documented decisions
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, List
from pathlib import Path

from src.config import (
    OUTPUT_DIR,
    MAX_REASONABLE_QUANTITY,
    MAX_REASONABLE_PRICE,
    MIN_VALID_DISCOUNT,
    MAX_VALID_DISCOUNT
)


def analyze_duplicates(df: pd.DataFrame) -> Dict:
    """
    Analyze duplicate order_id records.
    
    This function:
    1. Identifies exact duplicates (all fields identical)
    2. Identifies conflicting duplicates (same order_id, different fields)
    3. Returns detailed statistics and samples
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with order data
        
    Returns
    -------
    report : dict
        Dictionary with duplicate statistics and samples
    """
    # Check for duplicate order_ids
    duplicate_order_ids = df[df.duplicated(subset=['order_id'], keep=False)]
    
    # Count unique order_ids that have duplicates
    dup_order_ids_list = duplicate_order_ids['order_id'].unique()
    
    # Check for exact duplicates (all fields identical)
    exact_duplicates = df[df.duplicated(keep=False)]
    
    # Conflicting duplicates: same order_id but different data
    conflicting = duplicate_order_ids[~duplicate_order_ids.index.isin(exact_duplicates.index)]
    
    # Sample some duplicate groups for review
    sample_dup_groups = []
    for order_id in dup_order_ids_list[:5]:  # First 5 duplicate order_ids
        group = df[df['order_id'] == order_id]
        sample_dup_groups.append({
            'order_id': order_id,
            'count': len(group),
            'records': group.to_dict('records')
        })
    
    report = {
        'total_records': len(df),
        'unique_order_ids': df['order_id'].nunique(),
        'duplicate_order_ids_count': len(dup_order_ids_list),
        'total_duplicate_records': len(duplicate_order_ids),
        'exact_duplicate_records': len(exact_duplicates),
        'conflicting_duplicate_records': len(conflicting),
        'sample_duplicate_groups': sample_dup_groups
    }
    
    return report


def analyze_invalid_values(df: pd.DataFrame) -> Dict:
    """
    Analyze invalid numerical values in the dataset.
    
    Checks for:
    1. Negative or zero quantities
    2. Negative or zero unit prices
    3. Discounts outside 0-100%
    4. Suspiciously high values
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed numerical columns
        
    Returns
    -------
    report : dict
        Dictionary with invalid value statistics
    """
    # Convert to numeric, handling any string values
    df_clean = df.copy()
    df_clean['quantity'] = pd.to_numeric(df_clean['quantity'], errors='coerce')
    df_clean['unit_price'] = pd.to_numeric(df_clean['unit_price'], errors='coerce')
    df_clean['discount_pct'] = pd.to_numeric(df_clean['discount_pct'], errors='coerce')
    
    # Quantity issues
    qty_negative = df_clean[df_clean['quantity'] < 0]
    qty_zero = df_clean[df_clean['quantity'] == 0]
    qty_high = df_clean[df_clean['quantity'] > MAX_REASONABLE_QUANTITY]
    
    # Price issues
    price_negative = df_clean[df_clean['unit_price'] < 0]
    price_zero = df_clean[df_clean['unit_price'] == 0]
    price_high = df_clean[df_clean['unit_price'] > MAX_REASONABLE_PRICE]
    
    # Discount issues
    discount_negative = df_clean[df_clean['discount_pct'] < MIN_VALID_DISCOUNT]
    discount_high = df_clean[df_clean['discount_pct'] > MAX_VALID_DISCOUNT]
    
    report = {
        'quantity': {
            'negative_count': len(qty_negative),
            'zero_count': len(qty_zero),
            'high_count': len(qty_high),
            'negative_samples': qty_negative[['order_id', 'quantity', 'unit_price']].head(5).to_dict('records'),
            'zero_samples': qty_zero[['order_id', 'quantity', 'unit_price']].head(5).to_dict('records'),
            'high_samples': qty_high[['order_id', 'quantity', 'product']].head(5).to_dict('records')
        },
        'price': {
            'negative_count': len(price_negative),
            'zero_count': len(price_zero),
            'high_count': len(price_high),
            'negative_samples': price_negative[['order_id', 'unit_price', 'product']].head(5).to_dict('records'),
            'zero_samples': price_zero[['order_id', 'unit_price', 'product']].head(5).to_dict('records'),
            'high_samples': price_high[['order_id', 'unit_price', 'product']].head(5).to_dict('records')
        },
        'discount': {
            'negative_count': len(discount_negative),
            'high_count': len(discount_high),
            'negative_samples': discount_negative[['order_id', 'discount_pct']].head(5).to_dict('records'),
            'high_samples': discount_high[['order_id', 'discount_pct', 'product']].head(5).to_dict('records')
        }
    }
    
    return report


def analyze_missing_values(df: pd.DataFrame) -> Dict:
    """
    Analyze missing values across all columns.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to analyze
        
    Returns
    -------
    report : dict
        Dictionary with missing value statistics per column
    """
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / len(df) * 100).round(2)
    
    # Only report columns with missing values
    missing_cols = missing_counts[missing_counts > 0]
    
    report = {
        'total_records': len(df),
        'columns_with_missing': len(missing_cols),
        'missing_by_column': {}
    }
    
    for col in missing_cols.index:
        report['missing_by_column'][col] = {
            'count': int(missing_counts[col]),
            'percentage': float(missing_pct[col])
        }
    
    return report


def generate_audit_report(
    df: pd.DataFrame,
    dup_report: Dict,
    invalid_report: Dict,
    missing_report: Dict
) -> str:
    """
    Generate comprehensive data quality audit report.
    
    Parameters
    ----------
    df : pd.DataFrame
        Original DataFrame
    dup_report : dict
        Duplicate analysis report
    invalid_report : dict
        Invalid values report
    missing_report : dict
        Missing values report
        
    Returns
    -------
    report_text : str
        Formatted audit report
    """
    lines = []
    lines.append("=" * 80)
    lines.append("DATA QUALITY AUDIT REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    # Dataset overview
    lines.append("DATASET OVERVIEW:")
    lines.append(f"  Total records: {len(df):,}")
    lines.append(f"  Unique order_ids: {df['order_id'].nunique():,}")
    lines.append(f"  Unique customers: {df['customer_id'].nunique():,}")
    lines.append(f"  Date range: {df['order_date_parsed'].min().date()} to {df['order_date_parsed'].max().date()}")
    lines.append("")
    
    # Duplicate analysis
    lines.append("=" * 80)
    lines.append("DUPLICATE ANALYSIS")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total records: {dup_report['total_records']:,}")
    lines.append(f"Unique order_ids: {dup_report['unique_order_ids']:,}")
    lines.append(f"Duplicate order_ids: {dup_report['duplicate_order_ids_count']:,}")
    lines.append(f"Total duplicate records: {dup_report['total_duplicate_records']:,}")
    lines.append(f"  - Exact duplicates: {dup_report['exact_duplicate_records']:,}")
    lines.append(f"  - Conflicting duplicates: {dup_report['conflicting_duplicate_records']:,}")
    lines.append("")
    
    if len(dup_report['sample_duplicate_groups']) > 0:
        lines.append("Sample duplicate groups (first 5):")
        for group in dup_report['sample_duplicate_groups']:
            lines.append(f"\n  Order ID: {group['order_id']} ({group['count']} records)")
            for i, record in enumerate(group['records'], 1):
                lines.append(f"    Record {i}:")
                lines.append(f"      Date: {record.get('order_date', 'N/A')}")
                lines.append(f"      Customer: {record.get('customer_id', 'N/A')}")
                lines.append(f"      Product: {record.get('product', 'N/A')}")
                lines.append(f"      Quantity: {record.get('quantity', 'N/A')}")
                lines.append(f"      Price: {record.get('unit_price', 'N/A')}")
                lines.append(f"      Status: {record.get('order_status', 'N/A')}")
        lines.append("")
    
    # Invalid values
    lines.append("=" * 80)
    lines.append("INVALID VALUES ANALYSIS")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("QUANTITY ISSUES:")
    lines.append(f"  Negative quantities: {invalid_report['quantity']['negative_count']}")
    lines.append(f"  Zero quantities: {invalid_report['quantity']['zero_count']}")
    lines.append(f"  Suspiciously high (>{MAX_REASONABLE_QUANTITY}): {invalid_report['quantity']['high_count']}")
    lines.append("")
    
    lines.append("PRICE ISSUES:")
    lines.append(f"  Negative prices: {invalid_report['price']['negative_count']}")
    lines.append(f"  Zero prices: {invalid_report['price']['zero_count']}")
    lines.append(f"  Suspiciously high (>${MAX_REASONABLE_PRICE:,}): {invalid_report['price']['high_count']}")
    lines.append("")
    
    lines.append("DISCOUNT ISSUES:")
    lines.append(f"  Negative discounts: {invalid_report['discount']['negative_count']}")
    lines.append(f"  Discounts > 100%: {invalid_report['discount']['high_count']}")
    lines.append("")
    
    # Missing values
    lines.append("=" * 80)
    lines.append("MISSING VALUES ANALYSIS")
    lines.append("=" * 80)
    lines.append("")
    
    if missing_report['columns_with_missing'] > 0:
        for col, stats in missing_report['missing_by_column'].items():
            lines.append(f"  {col}: {stats['count']:,} ({stats['percentage']:.2f}%)")
    else:
        lines.append("  No missing values found")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Clean the dataset according to documented rules.
    
    Cleaning steps:
    1. Remove exact duplicate records (keep first)
    2. Exclude records with negative or zero quantities
    3. Exclude records with zero or negative prices
    4. Exclude discounts > 100% as invalid
    5. Keep customers with missing names or cities
    
    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame with parsed dates
        
    Returns
    -------
    df_clean : pd.DataFrame
        Cleaned DataFrame
    report : dict
        Dictionary with cleaning statistics
    """
    initial_count = len(df)
    
    # Convert numerical columns
    df = df.copy()
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
    df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
    df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce')
    
    # Track what we're removing
    removed = {
        'duplicates': 0,
        'negative_quantity': 0,
        'zero_quantity': 0,
        'negative_price': 0,
        'zero_price': 0,
        'invalid_discount': 0
    }
    
    # 1. Remove exact duplicates
    dup_count_before = len(df[df.duplicated(keep=False)])
    df = df.drop_duplicates(keep='first')
    removed['duplicates'] = dup_count_before - len(df[df.duplicated(keep=False)])
    
    # 2. Remove negative or zero quantities
    mask_neg_qty = df['quantity'] < 0
    mask_zero_qty = df['quantity'] == 0
    removed['negative_quantity'] = mask_neg_qty.sum()
    removed['zero_quantity'] = mask_zero_qty.sum()
    df = df[~(mask_neg_qty | mask_zero_qty)]
    
    # 3. Remove negative or zero prices
    mask_neg_price = df['unit_price'] < 0
    mask_zero_price = df['unit_price'] == 0
    removed['negative_price'] = mask_neg_price.sum()
    removed['zero_price'] = mask_zero_price.sum()
    df = df[~(mask_neg_price | mask_zero_price)]
    
    # 4. Exclude discounts > 100% as they are data errors
    mask_invalid_discount = df['discount_pct'] > 100
    removed['invalid_discount'] = mask_invalid_discount.sum()
    df = df[~mask_invalid_discount]
    
    final_count = len(df)
    total_removed = initial_count - final_count
    
    report = {
        'initial_records': initial_count,
        'final_records': final_count,
        'total_removed': total_removed,
        'removal_breakdown': removed,
        'unique_customers_after': df['customer_id'].nunique()
    }
    
    return df, report


def create_temporal_split(df: pd.DataFrame, historical_end: datetime, future_start: datetime) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Split data into historical and future periods.
    
    Parameters
    ----------
    df : pd.DataFrame
        Cleaned DataFrame with parsed dates
    historical_end : datetime
        End of historical period (2025-09-30)
    future_start : datetime
        Start of future period (2025-10-01)
        
    Returns
    -------
    df_historical : pd.DataFrame
        Orders in historical period
    df_future : pd.DataFrame
        Orders in future period
    report : dict
        Split statistics
    """
    df_historical = df[df['order_date_parsed'] <= historical_end].copy()
    df_future = df[df['order_date_parsed'] >= future_start].copy()
    
    report = {
        'total_orders': len(df),
        'historical_orders': len(df_historical),
        'future_orders': len(df_future),
        'historical_customers': df_historical['customer_id'].nunique(),
        'future_customers': df_future['customer_id'].nunique()
    }
    
    return df_historical, df_future, report


def create_target_variable(df_historical: pd.DataFrame, df_future: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Create churn_proxy target variable.
    
    Target definition:
    - Eligible customers: have at least one order in historical period (Jan-Sep 2025)
    - churn_proxy = 1: customer has NO orders in future period (Oct-Dec 2025)
    - churn_proxy = 0: customer has at least one order in future period
    
    This is a 90-day inactivity proxy, NOT confirmed churn.
    
    Parameters
    ----------
    df_historical : pd.DataFrame
        Historical period orders
    df_future : pd.DataFrame
        Future period orders
        
    Returns
    -------
    target_df : pd.DataFrame
        DataFrame with customer_id and churn_proxy
    report : dict
        Target statistics
    """
    # Get eligible customers (those with historical orders)
    eligible_customers = df_historical['customer_id'].unique()
    
    # Get customers who made future purchases
    future_customers = df_future['customer_id'].unique()
    
    # Create target DataFrame
    target_df = pd.DataFrame({
        'customer_id': eligible_customers
    })
    
    # Label: 1 if customer NOT in future, 0 if customer IS in future
    target_df['churn_proxy'] = target_df['customer_id'].apply(
        lambda x: 0 if x in future_customers else 1
    )
    
    report = {
        'eligible_customers': len(eligible_customers),
        'churned_customers': (target_df['churn_proxy'] == 1).sum(),
        'active_customers': (target_df['churn_proxy'] == 0).sum(),
        'churn_rate': (target_df['churn_proxy'] == 1).sum() / len(target_df),
        'class_distribution': target_df['churn_proxy'].value_counts().to_dict()
    }
    
    return target_df, report
