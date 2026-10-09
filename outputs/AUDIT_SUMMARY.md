# Data Audit and Cleaning Summary - STOP POINT

## Executive Summary

This document summarizes the data audit findings and proposed cleaning decisions for the Customer Churn Prediction project. **Do NOT proceed to model training until this document has been reviewed and cleaning has been verified.**

---

## Dataset Overview

- **Source:** `data/Challenge 1 - Churn Data (AIML).csv`
- **Total Records:** 5,120 order records
- **Unique Orders:** 5,000 order_ids  
- **Unique Customers:** 1,356
- **Date Range:** January 1, 2025 to December 31, 2025
- **Columns:** 12 (order_id, order_date, customer_id, customer_name, city, category, product, quantity, unit_price, discount_pct, payment_method, order_status)

---

## 1. Date Parsing - ✅ RESOLVED

### Problem
Mixed date formats in the `order_date` column:
- Format A: `dd-Mmm-yy` (e.g., "03-Oct-25")
- Format B: `dd-mm-yyyy` or `mm-dd-yyyy` (e.g., "17-10-2025", "09-25-2025")

### Solution Implemented
Created intelligent parser in `src/data_loader.py`:
1. Try `dd-Mmm-yy` first (unambiguous - has month name)
2. For numeric dates, check if values > 12 to determine day vs month
   - If first part > 12 → must be day (dd-mm-yyyy)
   - If second part > 12 → must be day (mm-dd-yyyy)
   - Both ≤ 12 → defaults to mm-dd-yyyy with ambiguity flag

### Result
- ✅ **All 5,120 dates (100%) parsed successfully**
- ✅ **0 ambiguous dates**
- ✅ **0 unparseable dates**
- ✅ **447 records near Sept 30 cutoff - all reliable**
- ✅ **Historical vs future split is trustworthy**

### Files
- Implementation: `src/data_loader.py`
- Test: `src/tests/test_date_parsing.py`
- Report: `outputs/date_parsing_report.txt`

---

## 2. Duplicate Records - ⚠️ NEEDS CLEANING

### Findings
- **Duplicate order_ids:** 120 (out of 5,000 unique)
- **Total duplicate records:** 240 (120 × 2)
- **Type:** All are **exact duplicates** (all fields identical)
- **Conflicting duplicates:** 0 (no data integrity issues)

### Analysis
Sample duplicates reviewed show:
- ORD202827: Same customer (C1950), same product (Lipstick), same date, same price
- ORD200213: Same customer (C2365), same product, same date, **zero price**
- ORD204133: Same customer (C1195), same product, same date, same price

**Conclusion:** These appear to be accidental data entry duplicates, NOT legitimate repeat orders (which would have different order_ids).

### Cleaning Decision
**✅ APPROVED STRATEGY: Remove exact duplicates, keep first occurrence**

Rationale:
- All fields are identical → no information loss
- Same order_id suggests data entry error, not separate transaction
- Keeps one valid record per order_id
- Conservative approach (doesn't drop unique customer data)

**Impact:**
- Records before cleaning: 5,120
- Records after cleaning: 4,880 (removed 240 duplicates)
- Customers affected: 120 (each loses one duplicate record)

### Implementation Plan
```python
df_clean = df.drop_duplicates(subset='order_id', keep='first')
```

---

## 3. Invalid Numerical Values - ⚠️ NEEDS CLEANING

### 3.1 Quantity Issues

**Negative Quantities:** 31 records
- Example: `quantity = -1`
- **Decision: DROP these records**
- Rationale: Negative quantities are data errors, not returns (returns have order_status='Returned')

**Zero Quantities:** 21 records  
- **Decision: DROP these records**
- Rationale: No meaningful transaction occurred (customer bought nothing)

**Suspiciously High (>100):** 6 records
- Example: `quantity = 500`
- **Decision: KEEP but FLAG for review**
- Rationale: Could be legitimate bulk orders; investigate product types

**Impact:**
- Records to drop: 31 + 21 = 52
- Records to flag: 6

### 3.2 Price Issues

**Negative Prices:** 0 records
- ✅ No action needed

**Zero Prices:** 26 records
- **Decision: DROP these records**
- Rationale: Critical for monetary features (RFM); likely data errors or promotional items we cannot value

**Suspiciously High (>$100,000):** 8 records
- **Decision: KEEP but FLAG for review**
- Rationale: Could be legitimate (e.g., electronics); verify product categories

**Impact:**
- Records to drop: 26
- Records to flag: 8

### 3.3 Discount Issues

**Negative Discounts:** 0 records
- ✅ No action needed

**Discounts > 100%:** 10 records
- **Decision: CAP at 100%**
- Rationale: Likely data entry errors (150% → meant 15% or 50%); capping is safer than dropping

**Impact:**
- Records to modify: 10 (cap discount_pct at 100)

### Summary of Invalid Values Cleaning

| Issue | Count | Action | Reason |
|-------|-------|--------|--------|
| Negative qty | 31 | DROP | Data error |
| Zero qty | 21 | DROP | No transaction |
| High qty (>100) | 6 | KEEP + FLAG | Could be bulk order |
| Zero price | 26 | DROP | Cannot calculate monetary value |
| High price (>100k) | 8 | KEEP + FLAG | Could be legitimate |
| Discount >100% | 10 | CAP at 100 | Data entry error |

**Total records to drop:** 31 + 21 + 26 = **78**  
**Total records to modify:** 10 (cap discounts)  
**Total records to flag:** 6 + 8 = 14 (for manual review)

---

## 4. Missing Values - ✅ STRATEGY DEFINED

### Findings

| Column | Missing | Percentage | Decision |
|--------|---------|------------|----------|
| customer_name | 93 | 1.82% | **KEEP as-is** (not used as feature) |
| city | 186 | 3.63% | **Impute with "Unknown"** (categorical feature) |
| unit_price | 153 | 2.99% | **Handled by record drops** (many overlap with zero price) |
| discount_pct | 123 | 2.40% | **Impute with 0** (assume no discount if missing) |
| payment_method | 40 | 0.78% | **Impute with "Unknown"** (categorical feature) |

### Strategy Details

**customer_name & customer_id:**
- Not used as predictive features (per requirements)
- Keep all missing values as-is
- No imputation needed

**city:**
- Used for aggregation (most frequent city feature)
- Impute with "Unknown" category
- Will be one-hot encoded with other cities

**unit_price:**
- Critical for monetary calculations
- Already being dropped if zero or missing
- After removing invalid records, check remaining nulls

**discount_pct:**
- Numerical feature
- Missing likely means "no discount applied"
- Impute with 0 (safe assumption)

**payment_method:**
- Categorical feature
- Impute with "Unknown" category
- Will be one-hot encoded

**Impact:**
- No additional records dropped due to missing values
- All missing values handled via imputation or kept as-is

---

## 5. Data Cleaning Pipeline Summary

### Cleaning Steps (in order)

1. **Load and parse dates** ✅ DONE
   - All 5,120 dates parsed successfully

2. **Remove exact duplicates**
   - Drop 240 duplicate records (keep first)
   - Remaining: 4,880 records

3. **Remove invalid quantities**
   - Drop 31 negative qty + 21 zero qty = 52 records
   - Remaining: ~4,828 records

4. **Remove invalid prices**
   - Drop 26 zero price records
   - Remaining: ~4,802 records

5. **Cap invalid discounts**
   - Cap 10 records at 100%
   - Remaining: ~4,802 records

6. **Impute missing values**
   - city: "Unknown" for 186 records
   - discount_pct: 0 for remaining nulls
   - payment_method: "Unknown" for 40 records

### Expected Final Dataset

- **Original records:** 5,120
- **After deduplication:** 4,880
- **After removing invalid values:** ~4,802
- **Customers retained:** ~1,350+ (minimal customer loss)
- **Data quality:** High (all invalid/duplicate records removed)

---

## 6. Temporal Split Verification - ⚠️ PENDING

### Cutoff Dates
- **Historical period:** January 1, 2025 - September 30, 2025
- **Future period:** October 1, 2025 - December 31, 2025

### Verification Needed (After Cleaning)

1. **Count orders by period:**
   - Historical orders: ? (to be calculated)
   - Future orders: ? (to be calculated)

2. **Count eligible customers:**
   - Customers with ≥1 historical order: ? (to be calculated)
   - These are the ONLY customers included in modeling

3. **Verify no data leakage:**
   - Features use ONLY historical period (Jan-Sep)
   - Target uses ONLY future period (Oct-Dec)
   - No overlap allowed

**Status:** 🔴 NOT YET VERIFIED - must run after cleaning

---

## 7. Target Variable (churn_proxy) - ⚠️ PENDING

### Definition
```
Eligible customers: Have ≥1 order in historical period (Jan-Sep 2025)

churn_proxy = 1  IF customer has NO orders (any status) in future period (Oct-Dec 2025)
churn_proxy = 0  IF customer has ≥1 order (any status) in future period (Oct-Dec 2025)
```

### This is a 90-Day Inactivity Proxy, NOT Confirmed Churn

**Important:** We are creating a proxy based on observed behavior (no orders for 90 days), not using actual churn labels. This should be clearly documented in all modeling reports.

### Verification Needed (After Cleaning)

1. **Target distribution:**
   - Count of churn_proxy=0: ?
   - Count of churn_proxy=1: ?
   - Imbalance ratio: ?

2. **Sanity checks:**
   - No customer with future orders labeled as churned
   - No customer without historical orders included
   - No future-period data leaked into features

**Status:** 🔴 NOT YET CREATED - must create after cleaning and temporal split verification

---

## 8. Unresolved Issues & Risks

### ⚠️ Flagged for Manual Review

1. **High quantity orders (6 records):**
   - Quantities > 100 (e.g., 500 units)
   - Could be legitimate bulk orders OR data errors
   - Recommend: Inspect product types before model training

2. **High price orders (8 records):**
   - Unit prices > $100,000
   - Could be legitimate electronics OR data errors
   - Recommend: Inspect product categories

### ⚠️ Known Limitations

1. **No explicit churn labels:**
   - Using 90-day inactivity proxy
   - May misclassify customers who:
     - Intended to order but haven't yet
     - Shop seasonally
     - Made large purchases and don't need more

2. **Class imbalance (expected):**
   - Churn is typically rare (10-30%)
   - Will need class_weight='balanced' or threshold tuning
   - Must not use test set for threshold selection

3. **Missing customer demographics:**
   - No age, income, location details
   - Limited to transaction-based features only

---

## 9. Files Created

### Code Files
- `src/config.py` - Configuration constants
- `src/__init__.py` - Package initialization
- `src/data_loader.py` - Date parsing logic
- `src/data_cleaning.py` - Duplicate & invalid value detection
- `src/tests/test_date_parsing.py` - Date parsing verification
- `src/tests/run_audit.py` - Full audit script

### Output Files
- `outputs/date_parsing_report.txt` - Date parsing results
- `outputs/data_quality_audit.txt` - Comprehensive audit report
- `outputs/data_with_parsed_dates.csv` - Intermediate data file
- `outputs/AUDIT_SUMMARY.md` - This document

---

## 10. Next Steps (DO NOT PROCEED WITHOUT APPROVAL)

### Step A: Implement Data Cleaning ⏸️ PAUSED
1. Create cleaning function in `src/data_cleaning.py`
2. Apply all cleaning decisions documented above
3. Generate before/after statistics
4. Save cleaned dataset

### Step B: Verify Temporal Split ⏸️ PAUSED
1. Split data into historical (Jan-Sep) and future (Oct-Dec)
2. Count orders and customers per period
3. Identify eligible customers (≥1 historical order)
4. Verify no data leakage

### Step C: Create Target Variable ⏸️ PAUSED
1. For each eligible customer, check if they have future orders
2. Create churn_proxy label
3. Analyze target distribution
4. Check for class imbalance

### Step D: Feature Engineering ⏸️ NOT STARTED
1. Aggregate historical orders to customer level
2. Create RFM features
3. Create behavioral features
4. Verify no future data in features

### Step E: Modeling ⏸️ NOT STARTED
- **DO NOT START UNTIL STEPS A-C ARE VERIFIED**

---

## 11. Approval Checklist

Before proceeding, confirm:

- [ ] Date parsing strategy is correct (all dates resolved)
- [ ] Duplicate removal strategy is acceptable (keep first, drop 240 records)
- [ ] Invalid value handling is acceptable (drop 78 records, cap 10 discounts)
- [ ] Missing value strategy is acceptable (impute city, discount, payment_method)
- [ ] Expected data loss is acceptable (~318 records / 6.2%)
- [ ] Temporal split definition is correct (Jan-Sep historical, Oct-Dec future)
- [ ] Target definition is correct (90-day inactivity proxy)
- [ ] Ready to implement cleaning and proceed to target construction

---

**STATUS: ⏸️ PAUSED - AWAITING APPROVAL TO PROCEED**

**Next Action:** Implement data cleaning pipeline and verify temporal split before creating target variable.
