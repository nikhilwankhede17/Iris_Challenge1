"""
Modeling module.

Trains Logistic Regression (mandatory) and optionally Random Forest.
Uses scikit-learn Pipeline with preprocessing.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve
)
import joblib
from pathlib import Path

from src.config import RANDOM_STATE, TEST_SIZE, MODEL_DIR, OUTPUT_DIR


def prepare_data_for_modeling(features_df: pd.DataFrame, target_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str], List[str]]:
    """
    Merge features with target and identify feature types.
    
    Parameters
    ----------
    features_df : pd.DataFrame
        Customer-level features
    target_df : pd.DataFrame
        Customer-level target (churn_proxy)
        
    Returns
    -------
    X : pd.DataFrame
        Features (excluding customer_id)
    y : pd.Series
        Target variable
    numerical_features : list
        Names of numerical features
    categorical_features : list
        Names of categorical features
    """
    # Merge features and target
    data = features_df.merge(target_df, on='customer_id', how='inner')
    
    # Separate features and target
    X = data.drop(columns=['customer_id', 'churn_proxy'])
    y = data['churn_proxy']
    
    # Identify numerical and categorical features
    numerical_features = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = X.select_dtypes(include=['object']).columns.tolist()
    
    return X, y, numerical_features, categorical_features


def create_preprocessing_pipeline(numerical_features: List[str], categorical_features: List[str]) -> ColumnTransformer:
    """
    Create preprocessing pipeline with imputation, scaling and encoding.
    
    Parameters
    ----------
    numerical_features : list
        Names of numerical features
    categorical_features : list
        Names of categorical features
        
    Returns
    -------
    preprocessor : ColumnTransformer
        Preprocessing pipeline
    """
    # Numerical: Impute with median, then StandardScaler
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Categorical: Impute with constant 'Unknown', then OneHotEncoder
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='Unknown')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ],
        remainder='drop'
    )
    
    return preprocessor


def train_logistic_regression(X_train: pd.DataFrame, y_train: pd.Series, 
                               preprocessor: ColumnTransformer,
                               use_class_weight: bool = False) -> Pipeline:
    """
    Train Logistic Regression model (MANDATORY PRIMARY MODEL).
    
    Parameters
    ----------
    X_train : pd.DataFrame
        Training features
    y_train : pd.Series
        Training target
    preprocessor : ColumnTransformer
        Preprocessing pipeline
    use_class_weight : bool
        Whether to use class_weight='balanced'
        
    Returns
    -------
    pipeline : Pipeline
        Trained pipeline
    """
    # Create pipeline
    if use_class_weight:
        model = LogisticRegression(
            random_state=RANDOM_STATE,
            max_iter=1000,
            class_weight='balanced'
        )
    else:
        model = LogisticRegression(
            random_state=RANDOM_STATE,
            max_iter=1000
        )
    
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])
    
    # Fit pipeline
    pipeline.fit(X_train, y_train)
    
    return pipeline


def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series,
                        preprocessor: ColumnTransformer,
                        use_class_weight: bool = False) -> Pipeline:
    """
    Train Random Forest model (OPTIONAL for comparison).
    
    Parameters
    ----------
    X_train : pd.DataFrame
        Training features
    y_train : pd.Series
        Training target
    preprocessor : ColumnTransformer
        Preprocessing pipeline
    use_class_weight : bool
        Whether to use class_weight='balanced'
        
    Returns
    -------
    pipeline : Pipeline
        Trained pipeline
    """
    if use_class_weight:
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=RANDOM_STATE,
            class_weight='balanced',
            n_jobs=-1
        )
    else:
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])
    
    pipeline.fit(X_train, y_train)
    
    return pipeline


def evaluate_model(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series, 
                   model_name: str) -> Dict:
    """
    Evaluate model and return metrics.
    
    Parameters
    ----------
    pipeline : Pipeline
        Trained pipeline
    X_test : pd.DataFrame
        Test features
    y_test : pd.Series
        Test target
    model_name : str
        Name of the model for reporting
        
    Returns
    -------
    metrics : dict
        Dictionary of evaluation metrics
    """
    # Predictions
    y_pred = pipeline.predict(X_test)
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'model_name': model_name,
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'confusion_matrix': confusion_matrix(y_test, y_pred),
        'classification_report': classification_report(y_test, y_pred, zero_division=0)
    }
    
    # ROC-AUC (only if both classes present)
    try:
        metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba)
        metrics['roc_curve'] = roc_curve(y_test, y_pred_proba)
    except:
        metrics['roc_auc'] = None
        metrics['roc_curve'] = None
    
    return metrics


def get_feature_importance(pipeline: Pipeline, feature_names: List[str], model_type: str = 'logistic') -> pd.DataFrame:
    """
    Extract feature importance or coefficients.
    
    Parameters
    ----------
    pipeline : Pipeline
        Trained pipeline
    feature_names : list
        Original feature names (before one-hot encoding)
    model_type : str
        'logistic' or 'random_forest'
        
    Returns
    -------
    importance_df : pd.DataFrame
        Feature importance/coefficients
    """
    model = pipeline.named_steps['classifier']
    preprocessor = pipeline.named_steps['preprocessor']
    
    # Get feature names after preprocessing
    try:
        feature_names_transformed = preprocessor.get_feature_names_out()
    except:
        # Fallback if get_feature_names_out not available
        feature_names_transformed = [f"feature_{i}" for i in range(len(model.coef_[0]) if model_type == 'logistic' else len(model.feature_importances_))]
    
    if model_type == 'logistic':
        # Logistic Regression coefficients
        importance = np.abs(model.coef_[0])
    else:
        # Random Forest feature importances
        importance = model.feature_importances_
    
    importance_df = pd.DataFrame({
        'feature': feature_names_transformed,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    return importance_df


def save_model_and_artifacts(pipeline: Pipeline, feature_names: List[str], 
                              metrics: Dict, model_name: str):
    """
    Save trained model and artifacts.
    
    Parameters
    ----------
    pipeline : Pipeline
        Trained pipeline
    feature_names : list
        Feature names
    metrics : dict
        Evaluation metrics
    model_name : str
        Name for saving
    """
    # Ensure directories exist
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = MODEL_DIR / f"{model_name}.joblib"
    joblib.dump(pipeline, model_path)
    
    # Save feature names
    feature_path = MODEL_DIR / f"{model_name}_features.txt"
    with open(feature_path, 'w') as f:
        for feat in feature_names:
            f.write(f"{feat}\n")
    
    # Save metrics
    metrics_path = OUTPUT_DIR / f"{model_name}_metrics.txt"
    with open(metrics_path, 'w') as f:
        f.write(f"Model: {metrics['model_name']}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Accuracy:  {metrics['accuracy']:.4f}\n")
        f.write(f"Precision: {metrics['precision']:.4f}\n")
        f.write(f"Recall:    {metrics['recall']:.4f}\n")
        f.write(f"F1-Score:  {metrics['f1_score']:.4f}\n")
        if metrics['roc_auc'] is not None:
            f.write(f"ROC-AUC:   {metrics['roc_auc']:.4f}\n")
        f.write("\n" + "=" * 80 + "\n\n")
        f.write("Confusion Matrix:\n")
        f.write(str(metrics['confusion_matrix']) + "\n\n")
        f.write("=" * 80 + "\n\n")
        f.write("Classification Report:\n")
        f.write(metrics['classification_report'])
    
    print(f"Saved model to: {model_path}")
    print(f"Saved metrics to: {metrics_path}")
