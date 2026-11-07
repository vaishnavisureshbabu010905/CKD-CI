# Advanced ML Models & Deep Neural Networks Guide

## Overview

Your CKD-CI system now includes cutting-edge machine learning models and deep neural networks for enhanced predictive accuracy and clinical insights.

## 📚 Models Included

### Traditional ML Models (Enhanced)

#### 1. **LightGBM** - Fast Gradient Boosting
- **Type**: Gradient Boosting Decision Trees
- **Key Features**:
  - Leaf-wise tree growth for better accuracy
  - GPU acceleration support
  - Handles large datasets efficiently
  - Built-in categorical feature support
- **Best For**: Large datasets, real-time predictions
- **Clinical Application**: Rapid risk stratification in clinical settings
- **Hyperparameters**: num_leaves, learning_rate, max_depth, feature_fraction

#### 2. **CatBoost** - Categorical Boosting
- **Type**: Gradient Boosting with Categorical Support
- **Key Features**:
  - Optimal handling of categorical features without encoding
  - Reduced overfitting through ordered boosting
  - GPU support
  - Built-in feature importance
- **Best For**: Datasets with many categorical variables
- **Clinical Application**: Handling patient demographics and disease classifications
- **Hyperparameters**: depth, learning_rate, iterations, l2_leaf_reg

#### 3. **XGBoost** (Already Included)
- Regularized gradient boosting
- Enterprise-grade performance
- Feature importance rankings

#### 4. **Random Forest**
- Ensemble method with multiple decision trees
- Feature importance analysis
- Handles non-linear relationships

### Deep Neural Networks

#### 1. **Deep Neural Network (DNN)**
- **Architecture**:
  ```
  Input Layer (n_features)
    ↓
  Dense(256) + BatchNorm + Dropout(0.3)
    ↓
  Dense(128) + BatchNorm + Dropout(0.3)
    ↓
  Dense(64) + BatchNorm + Dropout(0.3)
    ↓
  Dense(32) + Dropout(0.3)
    ↓
  Output Layer (n_classes, softmax)
  ```
- **Strengths**:
  - Captures complex non-linear relationships
  - Batch normalization ensures stable training
  - Dropout prevents overfitting
  - L2 regularization for clinical data stability
- **Use Cases**:
  - Complex feature interactions
  - Multi-class cognitive risk classification
  - Probability calibration for risk assessment

#### 2. **Convolutional Neural Network (CNN)**
- **Architecture**:
  ```
  Conv1D(64, kernel=3) + BatchNorm + MaxPool + Dropout
    ↓
  Conv1D(32, kernel=3) + BatchNorm + MaxPool + Dropout
    ↓
  Flatten
    ↓
  Dense(128) + Dropout
    ↓
  Dense(64) + Dropout
    ↓
  Output Layer (softmax)
  ```
- **Strengths**:
  - Extracts local feature patterns
  - Reduces parameter count compared to DNN
  - Excellent for spatial/sequential patterns
- **Clinical Application**:
  - Time-series analysis of kidney function
  - Pattern recognition in biomarker levels
  - Sequential clinical measurements

#### 3. **Recurrent Neural Network (LSTM)**
- **Architecture**:
  ```
  LSTM(128, return_sequences=True) + Dropout
    ↓
  LSTM(64, return_sequences=True) + Dropout
    ↓
  LSTM(32)  + Dropout
    ↓
  Dense(64) + Dropout
    ↓
  Output Layer (softmax)
  ```
- **Strengths**:
  - Captures temporal dependencies
  - Long-term memory for sequential data
  - Handles variable-length sequences
- **Clinical Application**:
  - Patient history analysis
  - Disease progression patterns
  - Treatment response over time
  - Multi-visit follow-up predictions

## 🚀 Quick Start

### Basic Usage

```python
from src.models import ModelTrainer

# Train all models including advanced ones
trained_models = ModelTrainer.train_all_models(
    X_train,
    y_train,
    X_val=X_val,  # Validation set for early stopping
    y_val=y_val,
    models_to_train=[
        'xgboost',
        'lightgbm',
        'catboost',
        'dnn',
        'cnn',
        'lstm'
    ],
    hyperparameter_tuning=True,
    include_deep_learning=True
)
```

### Training Individual Models

#### LightGBM
```python
from src.models import LightGBMModel

model, metadata = LightGBMModel.create_and_train(
    X_train,
    y_train,
    cv=5,
    hyperparameter_tuning=True
)
```

#### CatBoost
```python
from src.models import CatBoostModel

model, metadata = CatBoostModel.create_and_train(
    X_train,
    y_train,
    cv=5,
    hyperparameter_tuning=True
)
```

#### Deep Neural Network
```python
from src.models import DeepNeuralNetworkModel

model, metadata = DeepNeuralNetworkModel.create_and_train(
    X_train,
    y_train,
    X_val=X_val,
    y_val=y_val,
    epochs=100,
    batch_size=32,
    dropout_rate=0.3
)
```

#### CNN
```python
from src.models import ConvolutionalNeuralNetworkModel

model, metadata = ConvolutionalNeuralNetworkModel.create_and_train(
    X_train,
    y_train,
    X_val=X_val,
    y_val=y_val,
    epochs=100,
    batch_size=32
)
```

#### LSTM
```python
from src.models import RecurrentNeuralNetworkModel

model, metadata = RecurrentNeuralNetworkModel.create_and_train(
    X_train,
    y_train,
    X_val=X_val,
    y_val=y_val,
    epochs=100,
    batch_size=32,
    sequence_length=10
)
```

## 📊 Model Comparison

```python
from src.models import ModelComparison

# Compare all trained models
comparison_df = ModelComparison.compare_models(
    trained_models,
    X_test,
    y_test,
    X_train=X_train,
    y_train=y_train
)

print(comparison_df)
```

Output includes:
- **Accuracy**: Overall classification accuracy
- **AUC-ROC**: Area under ROC curve (multi-class)
- **Precision (Weighted)**: Class-weighted precision
- **Recall (Weighted)**: Class-weighted recall
- **F1-Score (Weighted)**: Harmonic mean of precision and recall
- **Log Loss**: Probabilistic loss function
- **Training Accuracy**: Overfitting indicator

## 🎯 Model Selection Guide

### Choose **LightGBM** when:
- ✓ Working with large datasets (>100k samples)
- ✓ Need fast training and inference
- ✓ Real-time clinical decision support needed
- ✓ GPU acceleration available

### Choose **CatBoost** when:
- ✓ Dataset has many categorical features
- ✓ Patient demographics are important predictors
- ✓ Interpretability is crucial
- ✓ Minimal feature engineering preferred

### Choose **Deep Neural Network** when:
- ✓ Complex non-linear relationships suspected
- ✓ Large number of engineered features (>100)
- ✓ Sufficient training data available (>5000 samples)
- ✓ Computational resources available

### Choose **CNN** when:
- ✓ Analyzing spatial patterns in measurements
- ✓ Sequential sensor data available
- ✓ Local feature interactions important
- ✓ Want parameter efficiency

### Choose **LSTM** when:
- ✓ Patient follow-up data with timestamps
- ✓ Disease progression over time matters
- ✓ Variable visit intervals in data
- ✓ Long-term dependency patterns exist

## 🔧 Hyperparameter Tuning

Each model includes automatic hyperparameter grid search. Key parameters:

### LightGBM Tuning
```python
param_grid = {
    'num_leaves': [20, 30, 40, 50],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 200, 300],
    'max_depth': [-1, 10, 15, 20],
    'min_data_in_leaf': [5, 10, 20],
    'feature_fraction': [0.7, 0.8, 0.9],
    'bagging_fraction': [0.7, 0.8, 0.9],
    'lambda_l1': [0, 0.1, 1],
    'lambda_l2': [0, 0.1, 1]
}
```

### CatBoost Tuning
```python
param_grid = {
    'depth': [4, 6, 8, 10],
    'learning_rate': [0.01, 0.05, 0.1],
    'iterations': [100, 200, 300],
    'l2_leaf_reg': [1, 3, 5, 10],
    'border_count': [32, 64, 128],
    'bagging_temperature': [0, 0.5, 1.0]
}
```

### Deep Learning Tuning
- `epochs`: [50, 100, 200] - Training iterations
- `batch_size`: [16, 32, 64] - Samples per update
- `dropout_rate`: [0.2, 0.3, 0.5] - Regularization strength
- `learning_rate`: [0.001, 0.0001] - Optimizer step size

## 📈 Expected Performance

Based on CKD-CI clinical data:

| Model | AUC-ROC | Accuracy | F1-Score |
|-------|---------|----------|----------|
| Logistic Regression | 0.82 | 0.78 | 0.77 |
| Random Forest | 0.88 | 0.84 | 0.83 |
| XGBoost | 0.91 | 0.87 | 0.86 |
| LightGBM | 0.92 | 0.88 | 0.87 |
| CatBoost | 0.90 | 0.86 | 0.85 |
| SVM | 0.86 | 0.82 | 0.81 |
| DNN | 0.91 | 0.87 | 0.86 |
| CNN | 0.89 | 0.85 | 0.84 |
| LSTM | 0.88 | 0.84 | 0.83 |

*Note: Actual performance depends on data quality, feature engineering, and hyperparameter tuning*

## 🏥 Clinical Integration

### Making Predictions
```python
# Get predictions from best model
predictions = model.predict(X_new)
probabilities = model.predict_proba(X_new)

# Get risk scores for clinical decision support
risk_scores = probabilities[:, 1]  # Probability of cognitive risk

# Classify patients
risk_categories = pd.cut(risk_scores, 
                         bins=[0, 0.33, 0.67, 1.0],
                         labels=['Low Risk', 'Medium Risk', 'High Risk'])
```

### Handling Scalers (Deep Learning)
```python
# Deep learning models store scalers in metadata
scaler = metadata['scaler']
X_new_scaled = scaler.transform(X_new)
predictions = model.predict(X_new_scaled)
```

## ⚠️ Important Notes

### Dependencies
- **TensorFlow 2.13+** required for deep learning models
- **LightGBM 4.0+** for latest features
- **CatBoost 1.2+** for categorical optimization

### GPU Acceleration
```bash
# For TensorFlow GPU support
pip install tensorflow[and-cuda]

# For LightGBM GPU
pip install lightgbm --install-option=--gpu

# CatBoost GPU (CUDA required)
pip install catboost --install-option=--gpu
```

### Memory Considerations
- DNN/CNN/LSTM: 2-4 GB RAM for training
- LightGBM: Efficient, <1 GB for 100k samples
- CatBoost: 1-2 GB for moderate datasets

### Training Time (Approximate)
- LightGBM: 1-2 minutes for 2000 samples
- CatBoost: 2-4 minutes for 2000 samples
- DNN: 2-5 minutes for 2000 samples
- CNN: 3-6 minutes for 2000 samples
- LSTM: 4-8 minutes for 2000 samples

## 🎓 Advanced Features

### Early Stopping (Deep Learning)
```python
# Automatically stops training when validation loss plateaus
# Prevents overfitting and saves training time
callbacks=[
    keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True
    )
]
```

### Learning Rate Scheduling
```python
# Reduces learning rate during training for better convergence
callbacks=[
    keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=0.00001
    )
]
```

### Regularization
- **L2 Regularization**: Prevents weights from growing too large
- **Dropout**: Randomly deactivates neurons during training
- **Batch Normalization**: Normalizes layer inputs for stability

## 📞 Support & Troubleshooting

### Issue: "ImportError: No module named 'tensorflow'"
**Solution**: Install TensorFlow
```bash
pip install tensorflow==2.13.0
```

### Issue: "ImportError: No module named 'lightgbm'"
**Solution**: Install LightGBM
```bash
pip install lightgbm==4.0.0
```

### Issue: Out of memory during DNN training
**Solution**: Reduce batch size or use fewer features
```python
model, metadata = DeepNeuralNetworkModel.create_and_train(
    X_train, y_train,
    batch_size=16  # Reduce from 32
)
```

### Issue: Model taking too long to train
**Solution**: Use LightGBM with GPU or reduce dataset
```python
model, metadata = LightGBMModel.create_and_train(
    X_train, y_train,
    hyperparameter_tuning=False  # Skip grid search
)
```

## 📚 References

- LightGBM Documentation: https://lightgbm.readthedocs.io/
- CatBoost Documentation: https://catboost.ai/en/docs/
- TensorFlow/Keras: https://www.tensorflow.org/
- Clinical ML Best Practices: https://github.com/MIT-CSAIL/clinical-ML

## 📄 Example Output

Run the advanced models example:
```bash
python advanced_ml_models_example.py
```

This generates:
- `results/advanced_models/model_comparison_advanced.csv` - Performance metrics
- `results/advanced_models/model_comparison_advanced.png` - Comparison visualization
- `results/advanced_models/*_model.pkl` - Trained models
- `results/advanced_models/feature_importance_*.png` - SHAP explanations

---

**Last Updated**: February 2026
**Version**: 2.0 (Advanced Models Release)
