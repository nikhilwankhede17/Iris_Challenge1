"""
Prediction module for making churn predictions on new customers.
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Dict

from src.config import MODEL_DIR


def load_model(model_name: str = "logistic_regression"):
    """
    Load a trained model pipeline.
    
    Parameters
    ----------
    model_name : str
        Name of the model file (without .joblib extension)
        
    Returns
    -------
    pipeline : Pipeline
        Loaded model pipeline
    """
    model_path = MODEL_DIR / f"{model_name}.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    pipeline = joblib.load(model_path)
    return pipeline


def predict_churn(customer_features: Dict, model_name: str = "logistic_regression") -> Dict:
    """
    Predict churn probability for a customer.
    
    Parameters
    ----------
    customer_features : dict
        Dictionary of customer features
    model_name : str
        Name of the model to use
        
    Returns
    -------
    prediction : dict
        Dictionary with prediction results
    """
    # Load model
    pipeline = load_model(model_name)
    
    # Convert to DataFrame
    X = pd.DataFrame([customer_features])
    
    # Make prediction
    churn_prob = pipeline.predict_proba(X)[0, 1]
    churn_pred = pipeline.predict(X)[0]
    
    result = {
        'churn_probability': float(churn_prob),
        'churn_prediction': 'Churned' if churn_pred == 1 else 'Active',
        'churn_risk': 'High' if churn_prob > 0.5 else 'Medium' if churn_prob > 0.3 else 'Low',
        'model_used': model_name
    }
    
    return result


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("CHURN PREDICTION EXAMPLE")
    print("=" * 80)
    print()
    
    # Example customer features
    example_customer = {
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
    
    print("Example customer features:")
    for key, value in example_customer.items():
        print(f"  {key}: {value}")
    print()
    
    # Predict
    prediction = predict_churn(example_customer)
    
    print("Prediction:")
    print(f"  Churn Probability: {prediction['churn_probability']:.4f} ({prediction['churn_probability']*100:.2f}%)")
    print(f"  Prediction: {prediction['churn_prediction']}")
    print(f"  Risk Level: {prediction['churn_risk']}")
    print(f"  Model Used: {prediction['model_used']}")
    print()
    print("=" * 80)
