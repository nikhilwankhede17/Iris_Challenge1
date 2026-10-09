"""
Main pipeline: Complete end-to-end churn prediction workflow.

This script:
1. Loads and cleans data
2. Creates temporal split and target variable
3. Engineers features (historical period only)
4. Trains Logistic Regression (mandatory) and Random Forest (optional)
5. Evaluates models
6. Saves models and reports
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import (
    HISTORICAL_END_DATE, FUTURE_START_DATE,
    RANDOM_STATE, TEST_SIZE, OUTPUT_DIR, MODEL_DIR
)
from src.data_loader import load_and_parse_dates
from src.data_cleaning import clean_data, create_temporal_split, create_target_variable
from src.feature_engineering import engineer_features
from src.modeling import (
    prepare_data_for_modeling, create_preprocessing_pipeline,
    train_logistic_regression, train_random_forest,
    evaluate_model, get_feature_importance, save_model_and_artifacts
)

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("CUSTOMER CHURN PREDICTION - END-TO-END PIPELINE")
print("=" * 80)
print()

# ===========================================================================
# STEP 1: LOAD AND PARSE DATES
# ===========================================================================
print("STEP 1: Loading and parsing dates...")
df_raw, date_report = load_and_parse_dates()
print(f"  Loaded {len(df_raw):,} records")
print(f"  Parsed {date_report['ok_count']:,} dates successfully")
print()

# ===========================================================================
# STEP 2: CLEAN DATA
# ===========================================================================
print("STEP 2: Cleaning data...")
df_clean, clean_report = clean_data(df_raw)
print(f"  Initial records: {clean_report['initial_records']:,}")
print(f"  Final records: {clean_report['final_records']:,}")
print(f"  Removed {clean_report['total_removed']:,} records:")
print(f"    - Duplicates: {clean_report['removal_breakdown']['duplicates']}")
print(f"    - Negative qty: {clean_report['removal_breakdown']['negative_quantity']}")
print(f"    - Zero qty: {clean_report['removal_breakdown']['zero_quantity']}")
print(f"    - Zero price: {clean_report['removal_breakdown']['zero_price']}")
print(f"    - Invalid discount: {clean_report['removal_breakdown']['invalid_discount']}")
print(f"  Unique customers: {clean_report['unique_customers_after']:,}")
print()

# ===========================================================================
# STEP 3: CREATE TEMPORAL SPLIT
# ===========================================================================
print("STEP 3: Creating temporal split...")
print(f"  Historical period: Jan 1, 2025 - Sep 30, 2025")
print(f"  Future period: Oct 1, 2025 - Dec 31, 2025")
df_historical, df_future, split_report = create_temporal_split(
    df_clean, HISTORICAL_END_DATE, FUTURE_START_DATE
)
print(f"  Historical orders: {split_report['historical_orders']:,}")
print(f"  Future orders: {split_report['future_orders']:,}")
print(f"  Historical customers: {split_report['historical_customers']:,}")
print(f"  Future customers: {split_report['future_customers']:,}")
print()

# ===========================================================================
# STEP 4: CREATE TARGET VARIABLE
# ===========================================================================
print("STEP 4: Creating target variable (90-day inactivity proxy)...")
target_df, target_report = create_target_variable(df_historical, df_future)
print(f"  Eligible customers: {target_report['eligible_customers']:,}")
print(f"  Churned (churn_proxy=1): {target_report['churned_customers']:,} ({target_report['churn_rate']:.2%})")
print(f"  Active (churn_proxy=0): {target_report['active_customers']:,} ({1-target_report['churn_rate']:.2%})")
print()
print("  NOTE: churn_proxy=1 means NO orders in Oct-Dec 2025 (90-day inactivity)")
print("  This is a proxy, NOT confirmed customer churn.")
print()

# ===========================================================================
# STEP 5: ENGINEER FEATURES
# ===========================================================================
print("STEP 5: Engineering features from historical data only...")
features_df = engineer_features(df_historical)
print(f"  Created features for {len(features_df):,} customers")
print(f"  Total features: {len(features_df.columns) - 1}")  # Exclude customer_id
print()

# Sample features
print("  Sample features created:")
print("    - recency_days, frequency, monetary_total, monetary_avg")
print("    - avg_quantity, avg_unit_price, avg_discount")
print("    - cancellation_rate, return_rate")
print("    - unique_categories, unique_products")
print("    - most_frequent_category, most_frequent_payment, most_frequent_city")
print()

# ===========================================================================
# STEP 6: PREPARE DATA FOR MODELING
# ===========================================================================
print("STEP 6: Preparing data for modeling...")
X, y, numerical_features, categorical_features = prepare_data_for_modeling(
    features_df, target_df
)
print(f"  Total samples: {len(X):,}")
print(f"  Numerical features: {len(numerical_features)}")
print(f"  Categorical features: {len(categorical_features)}")
print()

# Check class distribution
print("  Target distribution:")
print(f"    Class 0 (Active): {(y == 0).sum():,} ({(y == 0).sum() / len(y):.2%})")
print(f"    Class 1 (Churned): {(y == 1).sum():,} ({(y == 1).sum() / len(y):.2%})")
print()

# ===========================================================================
# STEP 7: TRAIN/TEST SPLIT
# ===========================================================================
print("STEP 7: Creating train/test split...")
print(f"  Test size: {TEST_SIZE * 100}%")
print(f"  Stratified: Yes")
print(f"  Random state: {RANDOM_STATE}")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)
print(f"  Train samples: {len(X_train):,}")
print(f"  Test samples: {len(X_test):,}")
print()

# ===========================================================================
# STEP 8: CREATE PREPROCESSING PIPELINE
# ===========================================================================
print("STEP 8: Creating preprocessing pipeline...")
preprocessor = create_preprocessing_pipeline(numerical_features, categorical_features)
print("  Numerical: StandardScaler")
print("  Categorical: OneHotEncoder (handle_unknown='ignore')")
print()

# ===========================================================================
# STEP 9: TRAIN LOGISTIC REGRESSION (MANDATORY PRIMARY MODEL)
# ===========================================================================
print("STEP 9: Training Logistic Regression (PRIMARY MODEL)...")
lr_pipeline = train_logistic_regression(X_train, y_train, preprocessor, use_class_weight=False)
print("  [OK] Logistic Regression trained")
print()

# Evaluate Logistic Regression
print("  Evaluating on test set...")
lr_metrics = evaluate_model(lr_pipeline, X_test, y_test, "Logistic Regression")
print(f"    Accuracy:  {lr_metrics['accuracy']:.4f}")
print(f"    Precision: {lr_metrics['precision']:.4f}")
print(f"    Recall:    {lr_metrics['recall']:.4f}")
print(f"    F1-Score:  {lr_metrics['f1_score']:.4f}")
if lr_metrics['roc_auc'] is not None:
    print(f"    ROC-AUC:   {lr_metrics['roc_auc']:.4f}")
print()
print("  Confusion Matrix:")
print(lr_metrics['confusion_matrix'])
print()

# Save Logistic Regression
save_model_and_artifacts(lr_pipeline, X.columns.tolist(), lr_metrics, "logistic_regression")
print()

# ===========================================================================
# STEP 10: TRAIN LOGISTIC REGRESSION WITH CLASS WEIGHT (BONUS EXPERIMENT)
# ===========================================================================
print("STEP 10: Training Logistic Regression with class_weight='balanced'...")
lr_balanced_pipeline = train_logistic_regression(X_train, y_train, preprocessor, use_class_weight=True)
print("  [OK] Balanced Logistic Regression trained")
print()

# Evaluate Balanced Logistic Regression
print("  Evaluating on test set...")
lr_balanced_metrics = evaluate_model(lr_balanced_pipeline, X_test, y_test, "Logistic Regression (Balanced)")
print(f"    Accuracy:  {lr_balanced_metrics['accuracy']:.4f}")
print(f"    Precision: {lr_balanced_metrics['precision']:.4f}")
print(f"    Recall:    {lr_balanced_metrics['recall']:.4f}")
print(f"    F1-Score:  {lr_balanced_metrics['f1_score']:.4f}")
if lr_balanced_metrics['roc_auc'] is not None:
    print(f"    ROC-AUC:   {lr_balanced_metrics['roc_auc']:.4f}")
print()

# Save Balanced Logistic Regression
save_model_and_artifacts(lr_balanced_pipeline, X.columns.tolist(), lr_balanced_metrics, "logistic_regression_balanced")
print()

# ===========================================================================
# STEP 11: TRAIN RANDOM FOREST (OPTIONAL COMPARISON)
# ===========================================================================
print("STEP 11: Training Random Forest (OPTIONAL for comparison)...")
rf_pipeline = train_random_forest(X_train, y_train, preprocessor, use_class_weight=False)
print("  [OK] Random Forest trained")
print()

# Evaluate Random Forest
print("  Evaluating on test set...")
rf_metrics = evaluate_model(rf_pipeline, X_test, y_test, "Random Forest")
print(f"    Accuracy:  {rf_metrics['accuracy']:.4f}")
print(f"    Precision: {rf_metrics['precision']:.4f}")
print(f"    Recall:    {rf_metrics['recall']:.4f}")
print(f"    F1-Score:  {rf_metrics['f1_score']:.4f}")
if rf_metrics['roc_auc'] is not None:
    print(f"    ROC-AUC:   {rf_metrics['roc_auc']:.4f}")
print()

# Save Random Forest
save_model_and_artifacts(rf_pipeline, X.columns.tolist(), rf_metrics, "random_forest")
print()

# ===========================================================================
# STEP 12: FEATURE IMPORTANCE
# ===========================================================================
print("STEP 12: Extracting feature importance...")
lr_importance = get_feature_importance(lr_pipeline, X.columns.tolist(), 'logistic')
print("  Top 10 features (Logistic Regression coefficients):")
for idx, row in lr_importance.head(10).iterrows():
    print(f"    {row['feature']}: {row['importance']:.4f}")
print()

# Save feature importance
importance_path = OUTPUT_DIR / "feature_importance_logistic.csv"
lr_importance.to_csv(importance_path, index=False)
print(f"  Saved full feature importance to: {importance_path}")
print()

# ===========================================================================
# STEP 13: VISUALIZATIONS
# ===========================================================================
print("STEP 13: Creating visualizations...")

# Confusion matrix heatmap
fig, ax = plt.subplots(1, 1, figsize=(8, 6))
sns.heatmap(lr_metrics['confusion_matrix'], annot=True, fmt='d', cmap='Blues', ax=ax)
ax.set_xlabel('Predicted')
ax.set_ylabel('Actual')
ax.set_title('Confusion Matrix - Logistic Regression')
cm_path = OUTPUT_DIR / "confusion_matrix_logistic.png"
plt.savefig(cm_path, dpi=100, bbox_inches='tight')
plt.close()
print(f"  Saved confusion matrix to: {cm_path}")

# ROC curve
if lr_metrics['roc_auc'] is not None:
    fpr, tpr, _ = lr_metrics['roc_curve']
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    ax.plot(fpr, tpr, label=f"Logistic Regression (AUC = {lr_metrics['roc_auc']:.4f})")
    ax.plot([0, 1], [0, 1], 'k--', label='Random')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC Curve')
    ax.legend()
    ax.grid(True, alpha=0.3)
    roc_path = OUTPUT_DIR / "roc_curve_logistic.png"
    plt.savefig(roc_path, dpi=100, bbox_inches='tight')
    plt.close()
    print(f"  Saved ROC curve to: {roc_path}")
print()

# ===========================================================================
# STEP 14: PREDICT ON SAMPLE TEST CUSTOMERS
# ===========================================================================
print("STEP 14: Predicting churn probability for 2 sample test customers...")
sample_indices = X_test.head(2).index
sample_X = X_test.head(2)
sample_y_true = y_test.iloc[:2]
sample_y_pred_proba = lr_pipeline.predict_proba(sample_X)[:, 1]
sample_y_pred = lr_pipeline.predict(sample_X)

print()
print("  Sample Predictions:")
for i, (idx, prob, pred, true) in enumerate(zip(sample_indices, sample_y_pred_proba, sample_y_pred, sample_y_true), 1):
    print(f"    Customer {i}:")
    print(f"      Churn Probability: {prob:.4f} ({prob*100:.2f}%)")
    print(f"      Predicted: {'Churned' if pred == 1 else 'Active'}")
    print(f"      Actual: {'Churned' if true == 1 else 'Active'}")
    print()

# ===========================================================================
# STEP 15: FINAL SUMMARY
# ===========================================================================
print("=" * 80)
print("PIPELINE COMPLETE")
print("=" * 80)
print()
print("Models trained:")
print("  1. Logistic Regression (primary)")
print("  2. Logistic Regression with class_weight='balanced'")
print("  3. Random Forest (for comparison)")
print()
print("Models saved to:")
print(f"  {MODEL_DIR / 'logistic_regression.joblib'}")
print(f"  {MODEL_DIR / 'logistic_regression_balanced.joblib'}")
print(f"  {MODEL_DIR / 'random_forest.joblib'}")
print()
print("Reports saved to:")
print(f"  {OUTPUT_DIR}")
print()
print("To make predictions on new customers:")
print("  python src/predict.py")
print()
print("=" * 80)
