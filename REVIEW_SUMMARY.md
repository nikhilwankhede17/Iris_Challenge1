# Project Setup Complete - Awaiting Approval

## ✅ What's Done

1. **Environment Setup**
   - Python 3.11 installed
   - Virtual environment created at `.venv`
   - All dependencies installed (pandas, scikit-learn, matplotlib, seaborn, streamlit, etc.)

2. **Dataset Verified**
   - File: `data/Challenge 1 - Churn Data (AIML).csv` (506 KB, 5,120 rows)
   - Initial inspection completed (`inspect_data.py`)

3. **Data Understanding Complete**
   - 5,120 order records
   - 1,356 unique customers
   - 12 columns (order details, customer info, product info)
   - Date range appears to cover 2025

4. **Documentation Created**
   - `PROJECT_PLAN.md`: Full requirements checklist and architecture
   - `REVIEW_SUMMARY.md`: This file
   - `inspect_data.py`: Initial data inspection script

---

## ⚠️ Critical Issues Identified

### 1. Mixed Date Formats (MUST RESOLVE)
- Format A: `dd-Mmm-yy` (e.g., "03-Oct-25", "16-Oct-25")
- Format B: `dd-mm-yyyy` (e.g., "17-10-2025", "14-03-2025")
- Total unique dates: 780
- **Ambiguity risk:** Numeric dates like "03-10-2025" unclear (Oct 3 vs March 10)

**Proposed solution:** Try month-name format first, fallback to dd-mm-yyyy, log failures

### 2. Duplicate Order Records
- 5,120 total rows but only 5,000 unique order_ids
- 120 duplicate records
- **Need decision:** Drop duplicates? Keep all? Investigate further?

### 3. Data Quality Issues
| Issue | Count | Proposed Action |
|-------|-------|-----------------|
| Negative/zero quantities | 52 | Drop or take absolute value? |
| Zero unit prices | 26 | Drop or impute with product median? |
| Discounts > 100% | 10 | Cap at 100% or drop? |
| Missing customer_name | 93 | Keep (not used as feature) |
| Missing city | 186 | Impute with "Unknown" or drop? |
| Missing unit_price | 153 | Impute with product/category median or drop? |
| Missing discount_pct | 123 | Impute with 0 or median? |
| Missing payment_method | 40 | Impute with "Unknown" or mode? |

---

## 🎯 Proposed Approach (Awaiting Approval)

### Data Cleaning Strategy

**Date Parsing:**
```python
# Try formats in this order:
1. dd-Mmm-yy (has month abbreviation)
2. dd-mm-yyyy (numeric, day-first European convention)
3. Log any unparseable dates
4. Validate all dates fall within 2025
```

**Duplicate Orders:**
- **Option A (Recommended):** Drop exact duplicates (same order_id, keep first)
- **Option B:** Investigate if truly duplicates or legitimate re-orders
- **Option C:** Keep all, treat as separate transactions

**Invalid Data:**
- Negative quantities: **Drop these orders** (likely data errors)
- Zero quantities: **Drop these orders** (no meaningful transaction)
- Zero prices: **Drop if quantity > 0** (invalid), else keep
- Discounts > 100%: **Cap at 100%** (likely typo, e.g., 150% → 100%)

**Missing Values:**
- `customer_name`: Keep as-is (not used as feature)
- `city`: Impute with **"Unknown"** category
- `unit_price`: **Drop order** if missing (critical for monetary features)
- `discount_pct`: Impute with **0** (assume no discount)
- `payment_method`: Impute with **"Unknown"** category

### Feature Engineering Plan

**Customer-Level Features (Historical Period: Jan-Sep 2025):**

1. **RFM Features**
   - Recency: Days since last order (as of 2025-09-30)
   - Frequency: Total number of orders
   - Monetary: Total revenue (sum of quantity × unit_price × (1 - discount_pct/100))

2. **Behavioral Features**
   - Average order value
   - Average quantity per order
   - Average discount received
   - Most frequent category
   - Most frequent payment method
   - Most frequent city

3. **Order Status Patterns**
   - Delivered order count
   - Cancelled order count
   - Returned order count
   - Cancellation rate (cancelled / total)
   - Return rate (returned / total)

4. **Temporal Features**
   - Days since first order (tenure)
   - Order velocity (orders per month)
   - Days between orders (average)

5. **Product Diversity**
   - Number of unique categories purchased
   - Number of unique products purchased

**Target:**
- `churn_proxy = 1` if customer has NO orders Oct-Dec 2025
- `churn_proxy = 0` if customer has ≥1 order Oct-Dec 2025

### Modeling Plan

1. **Train/Test Split:** 80/20 stratified by churn_proxy
2. **Preprocessing:**
   - Numerical: StandardScaler
   - Categorical: OneHotEncoder (for most_frequent_category, payment_method, city)
3. **Baseline Model:** Logistic Regression (C=1.0, class_weight='balanced')
4. **Bonus Model:** Random Forest (n_estimators=100, max_depth=10)
5. **Evaluation:** Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix

---

## 🚦 Decision Points (Your Input Needed)

### 1. Date Parsing
**Q:** Accept proposed multi-format parsing strategy?
- [ ] Yes, proceed as proposed
- [ ] No, suggest alternative: _______________

### 2. Duplicate Orders
**Q:** How to handle 120 duplicate order_ids?
- [ ] Option A: Drop duplicates (keep first occurrence)
- [ ] Option B: Investigate further before deciding
- [ ] Option C: Keep all as separate transactions

### 3. Invalid Quantities/Prices
**Q:** Accept proposed strategy (drop negatives/zeros)?
- [ ] Yes, drop invalid records
- [ ] No, suggest alternative: _______________

### 4. Missing Values
**Q:** Accept proposed imputation strategy?
- [ ] Yes, proceed as proposed
- [ ] No, modify: _______________

### 5. Class Imbalance
**Q:** Expect churn_proxy imbalance. Preferred handling?
- [ ] class_weight='balanced' in Logistic Regression
- [ ] Threshold tuning (e.g., lower threshold for churn)
- [ ] SMOTE oversampling (via imbalanced-learn)
- [ ] Try all, compare results

---

## 📋 Next Steps (Once Approved)

1. Implement `src/config.py` with constants
2. Implement `src/data_loader.py` with date parsing
3. Implement `src/data_cleaning.py` with approved strategies
4. Run cleaning, show before/after stats
5. Implement `src/feature_engineering.py`
6. Show feature DataFrame sample and target distribution
7. Proceed to modeling (only after feature validation)

---

## 📌 Questions for You

1. Do you approve the date parsing strategy?
2. Do you approve the data cleaning decisions?
3. Do you approve the feature engineering plan?
4. Any features you'd like added or removed?
5. Any specific concerns about the approach?

**Please review `PROJECT_PLAN.md` for full details.**

**Type "approved" or provide feedback to proceed.**
