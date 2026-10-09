# Quick Command Reference

## Setup (Already Complete)
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies (already done)
pip install -r requirements.txt
```

## Run Complete Pipeline
```bash
# Set Python path and run main pipeline
cd C:\Users\fe\Downloads\iris
$env:PYTHONPATH = "C:\Users\fe\Downloads\iris"
.\.venv\Scripts\python.exe churn_prediction.py
```

## Make Predictions

### Using Python Script
```bash
# Run example prediction
python src\predict.py
```

### Using Python Code
```python
from src.predict import predict_churn

# Define customer features
customer = {
    'recency_days': 30,
    'frequency': 5,
    'monetary_total': 5000.0,
    'monetary_avg': 1000.0,
    'avg_quantity': 2.0,
    'total_quantity': 10,
    'avg_unit_price': 500.0,
    'avg_discount': 5.0,
    'tenure_days': 180,
    'order_velocity': 0.83,
    'avg_days_between_orders': 36.0,
    'delivered_count': 4,
    'cancelled_count': 1,
    'returned_count': 0,
    'cancellation_rate': 0.2,
    'return_rate': 0.0,
    'unique_categories': 3,
    'unique_products': 5,
    'most_frequent_category': 'Electronics',
    'most_frequent_payment': 'UPI',
    'most_frequent_city': 'Mumbai'
}

# Predict
result = predict_churn(customer, model_name="logistic_regression_balanced")
print(f"Churn Probability: {result['churn_probability']:.2%}")
print(f"Prediction: {result['churn_prediction']}")
```

## Launch Streamlit App
```bash
# Start Streamlit web interface
streamlit run app.py

# App will open at http://localhost:8501
```

## Run Tests
```bash
# Test date parsing
python src\tests\test_date_parsing.py

# Run data quality audit
python src\tests\run_audit.py

# Analyze ambiguous dates (optional)
python src\tests\analyze_ambiguous_dates.py
```

## File Locations

### Models
- `models/logistic_regression.joblib` - Primary model
- `models/logistic_regression_balanced.joblib` - **RECOMMENDED** (best recall)
- `models/random_forest.joblib` - Comparison (not recommended)

### Reports
- `outputs/FINAL_REPORT.md` - **START HERE** - Complete project report
- `outputs/logistic_regression_balanced_metrics.txt` - Model performance
- `outputs/confusion_matrix_logistic.png` - Confusion matrix visualization
- `outputs/roc_curve_logistic.png` - ROC curve
- `outputs/feature_importance_logistic.csv` - Feature importance

### Audit Reports
- `outputs/data_quality_audit.txt` - Data quality findings
- `outputs/date_parsing_report.txt` - Date parsing results
- `outputs/SESSION_SUMMARY.md` - Implementation log

## Model Performance Summary

### Logistic Regression (Baseline)
- Accuracy: 69.96%
- Precision: 35.71%
- Recall: 6.94% (❌ Too low)
- F1-Score: 0.1163
- ROC-AUC: 0.5457

### Logistic Regression (Balanced) ⭐ RECOMMENDED
- Accuracy: 56.52%
- Precision: 32.41%
- Recall: 48.61% (✅ Much better)
- F1-Score: 0.3889
- ROC-AUC: 0.5473

### Random Forest
- Accuracy: 71.54%
- Precision: 0.00% (❌ Predicts all Active)
- Recall: 0.00%
- F1-Score: 0.00
- ROC-AUC: 0.4951

## Target Distribution
- **Eligible Customers:** 1,262
- **Churned (Class 1):** 360 (28.53%)
- **Active (Class 0):** 902 (71.47%)

## Key Insights
1. **Use balanced model** for better churn detection (48.61% recall)
2. **City is the strongest predictor** (Kolkata, Hyderabad, Mumbai)
3. **Purchase volume matters** (total_quantity, avg_quantity)
4. **Model has limitations** - ROC-AUC 0.55 (weak discriminative power)
5. **This is a 90-day inactivity proxy**, NOT confirmed churn

## Next Steps
1. Deploy the balanced Logistic Regression model
2. Monitor performance in production
3. Collect additional customer data (demographics, behavior)
4. Retrain periodically with new data
5. Optimize threshold based on business costs
