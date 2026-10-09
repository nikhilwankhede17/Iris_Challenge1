"""
Streamlit app for Customer Churn Prediction.

Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.predict import predict_churn

# Page config
st.set_page_config(
    page_title="Customer Churn Prediction",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Customer Churn Prediction")
st.markdown("### 90-Day Inactivity Proxy Model")
st.markdown("Predict whether a customer will make a purchase in the next 90 days based on their historical behavior.")
st.markdown("---")

# Sidebar for model selection
st.sidebar.header("Model Selection")
model_choice = st.sidebar.selectbox(
    "Choose Model:",
    ["logistic_regression", "logistic_regression_balanced", "random_forest"],
    format_func=lambda x: {
        "logistic_regression": "Logistic Regression",
        "logistic_regression_balanced": "Logistic Regression (Balanced)",
        "random_forest": "Random Forest"
    }[x]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This model predicts customer churn using a 90-day inactivity proxy. "
    "It analyzes historical purchase behavior (Jan-Sep 2025) to predict "
    "future activity (Oct-Dec 2025)."
)

# Main content - Input form
st.header("Enter Customer Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Purchase Behavior")
    recency_days = st.number_input("Days Since Last Order", min_value=0, max_value=365, value=30, step=1)
    frequency = st.number_input("Total Number of Orders", min_value=1, max_value=100, value=5, step=1)
    monetary_total = st.number_input("Total Order Value (₹)", min_value=0.0, max_value=1000000.0, value=5000.0, step=100.0)
    monetary_avg = st.number_input("Average Order Value (₹)", min_value=0.0, max_value=100000.0, value=1000.0, step=100.0)
    
with col2:
    st.subheader("Order Details")
    avg_quantity = st.number_input("Average Quantity per Order", min_value=0.0, max_value=100.0, value=2.0, step=0.1)
    total_quantity = st.number_input("Total Items Purchased", min_value=0, max_value=1000, value=10, step=1)
    avg_unit_price = st.number_input("Average Unit Price (₹)", min_value=0.0, max_value=100000.0, value=500.0, step=10.0)
    avg_discount = st.number_input("Average Discount (%)", min_value=0.0, max_value=100.0, value=5.0, step=1.0)

with col3:
    st.subheader("Customer Engagement")
    tenure_days = st.number_input("Customer Tenure (days)", min_value=1, max_value=365, value=180, step=1)
    order_velocity = st.number_input("Orders per Month", min_value=0.0, max_value=30.0, value=0.83, step=0.1)
    avg_days_between_orders = st.number_input("Avg Days Between Orders", min_value=0.0, max_value=365.0, value=36.0, step=1.0)

col4, col5, col6 = st.columns(3)

with col4:
    st.subheader("Order Outcomes")
    delivered_count = st.number_input("Delivered Orders", min_value=0, max_value=100, value=4, step=1)
    cancelled_count = st.number_input("Cancelled Orders", min_value=0, max_value=100, value=1, step=1)
    returned_count = st.number_input("Returned Orders", min_value=0, max_value=100, value=0, step=1)

with col5:
    st.subheader("Product Diversity")
    unique_categories = st.number_input("Unique Categories", min_value=1, max_value=20, value=3, step=1)
    unique_products = st.number_input("Unique Products", min_value=1, max_value=100, value=5, step=1)

with col6:
    st.subheader("Preferences")
    most_frequent_category = st.selectbox(
        "Most Frequent Category",
        ["Electronics", "Clothing", "Home & Kitchen", "Beauty", "Books", "Other"]
    )
    most_frequent_payment = st.selectbox(
        "Most Frequent Payment Method",
        ["UPI", "Credit Card", "Debit Card", "COD", "Net Banking"]
    )
    most_frequent_city = st.selectbox(
        "Most Frequent City",
        ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Other"]
    )

# Calculate rates
total_orders = delivered_count + cancelled_count + returned_count
if total_orders > 0:
    cancellation_rate = cancelled_count / total_orders
    return_rate = returned_count / total_orders
else:
    cancellation_rate = 0.0
    return_rate = 0.0

st.markdown("---")

# Predict button
if st.button("🔮 Predict Churn Risk", type="primary", use_container_width=True):
    # Prepare features
    customer_features = {
        'recency_days': recency_days,
        'frequency': frequency,
        'monetary_total': monetary_total,
        'monetary_avg': monetary_avg,
        'avg_quantity': avg_quantity,
        'total_quantity': total_quantity,
        'avg_unit_price': avg_unit_price,
        'avg_discount': avg_discount,
        'tenure_days': tenure_days,
        'order_velocity': order_velocity,
        'avg_days_between_orders': avg_days_between_orders,
        'delivered_count': delivered_count,
        'cancelled_count': cancelled_count,
        'returned_count': returned_count,
        'cancellation_rate': cancellation_rate,
        'return_rate': return_rate,
        'unique_categories': unique_categories,
        'unique_products': unique_products,
        'most_frequent_category': most_frequent_category,
        'most_frequent_payment': most_frequent_payment,
        'most_frequent_city': most_frequent_city
    }
    
    # Make prediction
    try:
        prediction = predict_churn(customer_features, model_name=model_choice)
        
        # Display results
        st.markdown("## 📊 Prediction Results")
        
        result_col1, result_col2, result_col3 = st.columns(3)
        
        with result_col1:
            st.metric("Churn Probability", f"{prediction['churn_probability']*100:.2f}%")
        
        with result_col2:
            st.metric("Prediction", prediction['churn_prediction'])
        
        with result_col3:
            risk_color = {
                'High': '🔴',
                'Medium': '🟡',
                'Low': '🟢'
            }
            st.metric("Risk Level", f"{risk_color[prediction['churn_risk']]} {prediction['churn_risk']}")
        
        # Interpretation
        st.markdown("### 💡 Interpretation")
        if prediction['churn_prediction'] == 'Churned':
            st.error(
                f"This customer has a **{prediction['churn_probability']*100:.1f}% probability** of churning "
                f"(not making a purchase in the next 90 days). Consider targeted retention campaigns."
            )
        else:
            st.success(
                f"This customer has a **{(1-prediction['churn_probability'])*100:.1f}% probability** of remaining active. "
                f"Continue engagement strategies."
            )
        
        # Recommendations
        st.markdown("### 🎯 Recommendations")
        if prediction['churn_probability'] > 0.5:
            st.markdown("""
            - **Send personalized discount offers** to re-engage the customer
            - **Reach out via email/SMS** with product recommendations
            - **Offer loyalty rewards** or exclusive deals
            - **Survey the customer** to understand pain points
            """)
        elif prediction['churn_probability'] > 0.3:
            st.markdown("""
            - **Monitor customer activity** closely
            - **Send reminder emails** about new products or deals
            - **Encourage repeat purchases** with small incentives
            """)
        else:
            st.markdown("""
            - **Maintain current engagement** strategies
            - **Cross-sell and upsell** related products
            - **Request feedback** to improve experience
            """)
        
    except Exception as e:
        st.error(f"Error making prediction: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Customer Churn Prediction Model | Built with Logistic Regression and Random Forest"
    "</div>",
    unsafe_allow_html=True
)
