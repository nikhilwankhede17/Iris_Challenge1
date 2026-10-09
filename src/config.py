"""
Configuration constants for the Customer Churn Prediction project.

This module defines all temporal boundaries, file paths, and parameters
used throughout the pipeline to ensure reproducibility.
"""
from datetime import datetime
from pathlib import Path

# ============================================================================
# PROJECT PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
MODEL_DIR = PROJECT_ROOT / "models"

# Raw data file
RAW_DATA_FILE = DATA_DIR / "Challenge 1 - Churn Data (AIML).csv"

# ============================================================================
# TEMPORAL BOUNDARIES
# ============================================================================
# Historical period: used for feature engineering
HISTORICAL_START_DATE = datetime(2025, 1, 1)
HISTORICAL_END_DATE = datetime(2025, 9, 30)

# Future outcome period: used ONLY for target labeling
FUTURE_START_DATE = datetime(2025, 10, 1)
FUTURE_END_DATE = datetime(2025, 12, 31)

# ============================================================================
# TARGET DEFINITION
# ============================================================================
# Customers with NO orders in the future period are labeled as churned
# This is a 90-day inactivity proxy, NOT confirmed churn
TARGET_NAME = "churn_proxy"
TARGET_DESCRIPTION = (
    "churn_proxy = 1 if customer has NO orders (any status) "
    f"between {FUTURE_START_DATE.date()} and {FUTURE_END_DATE.date()}; "
    "churn_proxy = 0 if customer has at least one order in that period."
)

# ============================================================================
# DATA QUALITY THRESHOLDS
# ============================================================================
# Thresholds for flagging suspicious values
MAX_REASONABLE_QUANTITY = 100  # Orders with quantity > 100 flagged for review
MAX_REASONABLE_PRICE = 100000  # Unit prices > 100k flagged for review
MIN_VALID_DISCOUNT = 0.0
MAX_VALID_DISCOUNT = 100.0

# ============================================================================
# MODELING PARAMETERS
# ============================================================================
RANDOM_STATE = 42  # For reproducibility
TEST_SIZE = 0.2  # 80/20 train-test split
STRATIFY_TARGET = True  # Stratified split on target variable

# ============================================================================
# FEATURE ENGINEERING
# ============================================================================
# Columns that should NEVER be used as features
EXCLUDE_FROM_FEATURES = [
    'customer_id',
    'customer_name',
    'order_id',
    'order_date'
]

# ============================================================================
# OUTPUT FILES
# ============================================================================
AUDIT_REPORT_FILE = OUTPUT_DIR / "data_audit_report.txt"
CLEANING_REPORT_FILE = OUTPUT_DIR / "data_cleaning_report.txt"
TARGET_REPORT_FILE = OUTPUT_DIR / "target_validation_report.txt"
