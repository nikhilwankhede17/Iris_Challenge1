# Customer Churn Prediction - Project Plan

## Dataset Summary

**File:** `data/Challenge 1 - Churn Data (AIML).csv`
- **Rows:** 5,120 order records
- **Unique customers:** 1,356
- **Columns:** 12 (order_id, order_date, customer_id, customer_name, city, category, product, quantity, unit_price, discount_pct, payment_method, order_status)

### Key Data Quality Issues Identified

1. **Date Format Ambiguity (CRITICAL)**
   - Mixed formats detected: `dd-Mmm-yy` (e.g., "03-Oct-25") and `dd-mm-yyyy` (e.g., "17-10-2025")
   - Total unique dates: 780
   - **Resolution needed:** Implement explicit parsing strategy to handle both formats

2. **Duplicate Orders**
   - 5,120 total orders but only 5,000 unique order_ids
   - 120 duplicate order records
   - **Action:** Investigate and document duplicate handling strategy

3. **Data Quality Issues**
   - Negative/zero quantities: 52 orders
   - Zero unit prices: 26 orders
   - Discounts > 100%: 10 orders
   - Missing values: 595 across multiple columns
     - customer_name: 93
     - city: 186
     - unit_price: 153
     - discount_pct: 123
     - payment_method: 40

4. **Order Status Distribution**
   - Delivered: 3,436 (67.1%)
   - Cancelled: 867 (16.9%)
   - Returned: 817 (16.0%)

---

## Target Definition (90-Day Inactivity Proxy)

**Historical Feature Period:** 2025-01-01 through 2025-09-30
**Future Outcome Period:** 2025-10-01 through 2025-12-31

**Eligibility:**
- Customer must have at least one valid historical order dated on or before 2025-09-30

**Target Variable (`churn_proxy`):**
- `1` = Customer has NO orders (any status) during 2025-10-01 to 2025-12-31
- `0` = Customer has at least one order (any status) during 2025-10-01 to 2025-12-31

**Critical Constraints:**
- Never use future-period (Oct-Dec 2025) information as features
- Never use customer_id or customer_name as features
- One row per eligible customer in final dataset

---

## Requirements Checklist

### Core Requirements

- [ ] **1. Data Exploration & Quality Analysis**
  - [ ] Load and inspect raw data
  - [ ] Document date format handling strategy
  - [ ] Analyze and document all data quality issues
  - [ ] Check distribution of all features
  - [ ] Verify eligible customer count after temporal split

- [ ] **2. Data Cleaning**
  - [ ] Implement reproducible date parsing (handle mixed formats)
  - [ ] Handle duplicate order_id records (document decision)
  - [ ] Handle negative/zero quantities (document decision)
  - [ ] Handle zero/invalid prices (document decision)
  - [ ] Handle discount_pct > 100% (document decision)
  - [ ] Handle missing values (document strategy per column)
  - [ ] Validate no future data leakage

- [ ] **3. Feature Engineering**
  - [ ] Create customer-level aggregated features from historical orders
  - [ ] RFM features: Recency, Frequency, Monetary
  - [ ] Behavioral features: avg order value, favorite category, payment method preferences
  - [ ] Order status patterns: cancellation rate, return rate
  - [ ] Temporal features: days since first order, order velocity
  - [ ] Product diversity: number of unique categories/products
  - [ ] Document all feature definitions

- [ ] **4. Target Creation**
  - [ ] Implement temporal split (historical vs future periods)
  - [ ] Create churn_proxy label
  - [ ] Verify no data leakage
  - [ ] Document class distribution

- [ ] **5. Train/Test Split**
  - [ ] Stratified split (maintain churn_proxy distribution)
  - [ ] Document split ratio (suggest 80/20 or 75/25)
  - [ ] Set random_state for reproducibility
  - [ ] Verify both classes present in train and test

- [ ] **6. Feature Preprocessing**
  - [ ] Identify numerical vs categorical features
  - [ ] Fit preprocessing pipeline on training data ONLY
  - [ ] Numerical: StandardScaler or MinMaxScaler
  - [ ] Categorical: OneHotEncoder or OrdinalEncoder
  - [ ] Handle any remaining missing values in features

- [ ] **7. Logistic Regression Model**
  - [ ] Train baseline Logistic Regression
  - [ ] Document hyperparameters
  - [ ] Fit on training data only

- [ ] **8. Model Evaluation**
  - [ ] Predict on held-out test set
  - [ ] Calculate and report:
    - [ ] Accuracy
    - [ ] Precision
    - [ ] Recall
    - [ ] Confusion Matrix (visualize)
  - [ ] Justify metric selection for churn prediction
  - [ ] Show predicted probabilities for 2 test customers

### Bonus Requirements

- [ ] **9. Random Forest Comparison**
  - [ ] Train Random Forest with reasonable hyperparameters
  - [ ] Compare metrics with Logistic Regression
  - [ ] Document tradeoffs

- [ ] **10. Advanced Metrics & Class Imbalance**
  - [ ] Calculate F1-Score
  - [ ] Calculate ROC-AUC and plot ROC curve
  - [ ] Implement class imbalance handling:
    - [ ] Try class_weight='balanced' in Logistic Regression
    - [ ] Or adjust decision threshold
  - [ ] Show how recall changes with imbalance handling

- [ ] **11. Feature Importance**
  - [ ] Extract and visualize top 5 features from Logistic Regression (coefficients)
  - [ ] Or from Random Forest (feature_importances_)
  - [ ] Document interpretation

- [ ] **12. EDA Visualizations**
  - [ ] Create 2 meaningful EDA plots (e.g., churn rate by category, RFM distributions)
  - [ ] Document insights

- [ ] **13. Prediction Function / Streamlit App**
  - [ ] Create `predict_churn()` function that takes customer details
  - [ ] Or build simple Streamlit interface
  - [ ] Save trained model and preprocessing pipeline
  - [ ] Test prediction on new customer input

---

## Proposed Architecture

### File Structure
```
iris/
├── data/
│   └── Challenge 1 - Churn Data (AIML).csv   # Raw data (gitignored)
├── notebooks/                                 # Optional: Jupyter notebooks for exploration
│   └── 01_eda.ipynb
├── src/                                       # Core pipeline code
│   ├── __init__.py
│   ├── config.py                              # Constants: dates, file paths, random_state
│   ├── data_loader.py                         # Load and parse dates
│   ├── data_cleaning.py                       # Handle duplicates, nulls, invalid values
│   ├── feature_engineering.py                 # Create customer-level features
│   ├── modeling.py                            # Train/test split, preprocessing, models
│   └── evaluation.py                          # Metrics, confusion matrix, plots
├── models/                                    # Saved models (gitignored)
│   ├── logistic_model.pkl
│   ├── rf_model.pkl
│   └── preprocessor.pkl
├── outputs/                                   # Plots, reports
│   ├── confusion_matrix.png
│   ├── roc_curve.png
│   ├── feature_importance.png
│   └── model_report.txt
├── app.py                                     # Streamlit app (bonus)
├── churn_prediction.py                        # Main script orchestrating pipeline
├── requirements.txt
├── README.md
└── .gitignore
```

### Pipeline Flow

1. **Data Loading** (`data_loader.py`)
   - Read CSV
   - Parse mixed date formats with explicit error handling
   - Return clean DataFrame with datetime column

2. **Data Cleaning** (`data_cleaning.py`)
   - Remove or flag duplicate order_ids
   - Handle invalid quantities, prices, discounts
   - Impute or drop missing values
   - Document all decisions in docstrings

3. **Feature Engineering** (`feature_engineering.py`)
   - Filter to historical period (Jan-Sep 2025)
   - Aggregate to customer level
   - Create RFM and behavioral features
   - Return one-row-per-customer DataFrame

4. **Target Creation** (`feature_engineering.py`)
   - Use future period (Oct-Dec 2025) to label churn_proxy
   - Merge with feature DataFrame
   - Verify no leakage

5. **Modeling** (`modeling.py`)
   - Stratified train/test split
   - Create preprocessing pipeline
   - Fit on training data
   - Train Logistic Regression (+ Random Forest bonus)

6. **Evaluation** (`evaluation.py`)
   - Predict on test set
   - Calculate all metrics
   - Generate visualizations
   - Save results

7. **Prediction Interface** (`app.py` or function)
   - Load saved model and preprocessor
   - Accept new customer input
   - Return churn probability and interpretation

---

## Date Parsing Strategy (CRITICAL DECISION NEEDED)

**Observed Formats:**
- `dd-Mmm-yy`: "03-Oct-25", "16-Oct-25", "25-Nov-25"
- `dd-mm-yyyy`: "17-10-2025", "14-03-2025", "15-10-2025"

**Proposed Solution:**
```python
def parse_order_date(date_str):
    """
    Parse mixed date formats with explicit handling.
    
    Strategy:
    1. Try parsing as dd-Mmm-yy (e.g., "03-Oct-25")
    2. If fails, try dd-mm-yyyy (e.g., "17-10-2025")
    3. If fails, try mm-dd-yyyy (ambiguous case)
    4. Log any unparseable dates
    """
    # Implementation details to be reviewed
```

**Ambiguity Risk:** Dates like "03-10-2025" could be Oct 3 or March 10.

**Resolution:** 
- Check if month names (Jan, Feb, Oct, Nov) appear → prioritize that format
- For numeric-only dates, document assumption (day-month-year per European convention, common in India)
- Validate parsed dates are all within 2025
- Flag any dates outside expected range

---

## Next Steps

**Awaiting your approval on:**

1. **Date parsing strategy** above
2. **Duplicate order handling:** Keep first occurrence? Keep all? Investigate if truly duplicates?
3. **Invalid data handling:**
   - Negative quantities: Drop? Set to absolute value?
   - Zero prices: Drop? Impute with median per product?
   - Discount > 100%: Cap at 100%? Drop?
4. **Missing value strategy:** Per-column imputation or drop rows?
5. **Class imbalance:** Expect churn_proxy to be imbalanced. Use class_weight or SMOTE?

Once approved, I will implement the pipeline stage by stage, showing results at each step.

---

**Ready to proceed when you give the signal.**
