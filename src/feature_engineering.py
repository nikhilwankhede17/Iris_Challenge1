"""
Feature engineering module.

Creates customer-level features from historical order data only.
NO future-period information should be used in features.
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import datetime

from src.config import HISTORICAL_END_DATE


def engineer_features(df_historical: pd.DataFrame) -> pd.DataFrame:
    """
    Create customer-level features from historical orders.
    
    Features created:
    - RFM features: Recency, Frequency, Monetary
    - Order behavior: avg quantity, avg price, avg discount
    - Order outcomes: cancellation rate, return rate
    - Product diversity: unique categories, unique products
    - Payment preferences: most frequent payment method
    - Geographic: most frequent city
    
    All features use ONLY historical period data (Jan-Sep 2025).
    
    Parameters
    ----------
    df_historical : pd.DataFrame
        Historical period orders
        
    Returns
    -------
    features_df : pd.DataFrame
        One row per customer with engineered features
    """
    # Fill missing values before aggregation
    df = df_historical.copy()
    df['discount_pct'] = df['discount_pct'].fillna(0)
    df['city'] = df['city'].fillna('Unknown')
    df['payment_method'] = df['payment_method'].fillna('Unknown')
    
    # Calculate order value: quantity * unit_price * (1 - discount_pct/100)
    df['order_value'] = df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)
    
    # Reference date for recency calculation
    reference_date = HISTORICAL_END_DATE
    
    # Group by customer
    customer_features = []
    
    for customer_id, group in df.groupby('customer_id'):
        features = {'customer_id': customer_id}
        
        # === RFM FEATURES ===
        # Recency: days since last order
        last_order_date = group['order_date_parsed'].max()
        features['recency_days'] = (reference_date - last_order_date).days
        
        # Frequency: total number of orders
        features['frequency'] = len(group)
        
        # Monetary: total order value
        features['monetary_total'] = group['order_value'].sum()
        features['monetary_avg'] = group['order_value'].mean()
        
        # === ORDER BEHAVIOR ===
        features['avg_quantity'] = group['quantity'].mean()
        features['total_quantity'] = group['quantity'].sum()
        features['avg_unit_price'] = group['unit_price'].mean()
        features['avg_discount'] = group['discount_pct'].mean()
        
        # === TEMPORAL FEATURES ===
        first_order_date = group['order_date_parsed'].min()
        features['tenure_days'] = (reference_date - first_order_date).days
        
        # Order velocity (orders per month)
        if features['tenure_days'] > 0:
            features['order_velocity'] = features['frequency'] / (features['tenure_days'] / 30)
        else:
            features['order_velocity'] = 0
        
        # Days between orders (average)
        if features['frequency'] > 1:
            date_diffs = group['order_date_parsed'].sort_values().diff().dt.days
            features['avg_days_between_orders'] = date_diffs.mean()
        else:
            features['avg_days_between_orders'] = 0
        
        # === ORDER OUTCOMES ===
        status_counts = group['order_status'].value_counts()
        total_orders = len(group)
        
        features['delivered_count'] = status_counts.get('Delivered', 0)
        features['cancelled_count'] = status_counts.get('Cancelled', 0)
        features['returned_count'] = status_counts.get('Returned', 0)
        
        features['cancellation_rate'] = features['cancelled_count'] / total_orders
        features['return_rate'] = features['returned_count'] / total_orders
        
        # === PRODUCT DIVERSITY ===
        features['unique_categories'] = group['category'].nunique()
        features['unique_products'] = group['product'].nunique()
        
        # === CATEGORICAL FEATURES ===
        # Most frequent category
        features['most_frequent_category'] = group['category'].mode().iloc[0] if len(group['category'].mode()) > 0 else 'Unknown'
        
        # Most frequent payment method
        features['most_frequent_payment'] = group['payment_method'].mode().iloc[0] if len(group['payment_method'].mode()) > 0 else 'Unknown'
        
        # Most frequent city
        features['most_frequent_city'] = group['city'].mode().iloc[0] if len(group['city'].mode()) > 0 else 'Unknown'
        
        customer_features.append(features)
    
    features_df = pd.DataFrame(customer_features)
    
    return features_df
