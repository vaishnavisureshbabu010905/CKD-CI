"""
Advanced ML Models & Deep Neural Networks Integration Example

This script demonstrates how to use the newly added advanced models:
- LightGBM: Fast gradient boosting with GPU support
- CatBoost: Optimized for categorical features
- Deep Neural Networks: Multi-layer perceptron with regularization
- Convolutional Neural Networks: For spatial feature patterns
- Recurrent Neural Networks (LSTM): For temporal clinical patterns
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold
import warnings
warnings.filterwarnings('ignore')

# Project imports
from data.generate_synthetic_data import CKDCognitiveDataGenerator
from src.preprocessing import preprocess_pipeline, FeatureEngineer
from src.feature_selection import comprehensive_feature_selection
from src.models import (
    ModelTrainer, ModelComparison, 
    LightGBMModel, CatBoostModel,
    DeepNeuralNetworkModel, ConvolutionalNeuralNetworkModel,
    RecurrentNeuralNetworkModel
)
from src.evaluation import EvaluationReport, ROCAnalysis
from src.explainability import SHAPExplainer
from src.utils import ModelSaver, ensure_directory

# Configuration
RANDOM_STATE = 42
DATASET_SIZE = 2000
TEST_SIZE = 0.2
VAL_SIZE = 0.2
RESULTS_DIR = 'results/advanced_models'

# Set random seeds
np.random.seed(RANDOM_STATE)

def main():
    """Execute advanced ML pipeline with deep learning models."""
    
    print("\n" + "="*80)
    print("ADVANCED ML & DEEP NEURAL NETWORKS - CKD-CI PIPELINE")
    print("="*80)
    
    # ==================== STEP 1: DATA GENERATION ====================
    print("\n[STEP 1] GENERATING SYNTHETIC DATASET...")
    print("-" * 80)
    
    generator = CKDCognitiveDataGenerator(random_state=RANDOM_STATE)
    df = generator.generate_dataset(n_samples=DATASET_SIZE)
    print(f"[OK] Generated dataset: {df.shape[0]} samples, {df.shape[1]} features")
    print(f"  Class distribution:\n{df['cognitive_risk'].value_counts()}\n")
    
    # ==================== STEP 2: PREPROCESSING ====================
    print("[STEP 2] DATA PREPROCESSING...")
    print("-" * 80)
    
    prep_result = preprocess_pipeline(df)
    X_train = prep_result['X_train']
    X_test = prep_result['X_test']
    y_train = prep_result['y_train']
    y_test = prep_result['y_test']
    print(f"[OK] Preprocessed data: Train={X_train.shape[0]}, Test={X_test.shape[0]}, Features={X_train.shape[1]}")
    
    # ==================== STEP 3: FEATURE SELECTION ====================
    print("\n[STEP 3] FEATURE SELECTION...")
    print("-" * 80)
    
    # Get feature names
    feature_names = X_train.columns.tolist() if hasattr(X_train, 'columns') else [f"Feature_{i}" for i in range(X_train.shape[1])]
    
    # Perform feature selection
    selection_result = comprehensive_feature_selection(
        X_train.values,
        y_train.values,
        feature_names=feature_names,
        top_n=25
    )
    
    # Get top features from correlation analysis
    correlation_scores = selection_result.get('correlation_scores', {})
    if isinstance(correlation_scores, dict):
        top_features = sorted(correlation_scores.items(), key=lambda x: abs(x[1]), reverse=True)[:25]
        selected_features = [f[0] for f in top_features]
    else:
        selected_features = feature_names[:25]
    
    X_train_selected = X_train[selected_features]
    X_test_selected = X_test[selected_features]
    
    print(f"[OK] Selected {len(selected_features)} features")
    print(f"  Features: {selected_features[:5]}..." if len(selected_features) > 5 else f"  Features: {selected_features}")
    
    # ==================== STEP 4: CREATING VALIDATION SET ====================
    print("\n[STEP 4] CREATING VALIDATION SET...")
    print("-" * 80)
    
    # Create validation set from training set
    X_train_main, X_val, y_train_main, y_val = train_test_split(
        X_train_selected,
        y_train,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y_train
    )
    
    print(f"[OK] Training set: {X_train_main.shape[0]} samples")
    print(f"[OK] Validation set: {X_val.shape[0]} samples")
    print(f"[OK] Test set: {X_test_selected.shape[0]} samples")
    
    # ==================== STEP 5: TRAINING ADVANCED MODELS ====================
    print("\n[STEP 5] TRAINING ADVANCED ML & DEEP LEARNING MODELS...")
    print("-" * 80)
    
    ensure_directory(RESULTS_DIR)
    
    # Train all models including advanced and deep learning ones
    trained_models = ModelTrainer.train_all_models(
        X_train_main.values,
        y_train_main.values,
        X_val=X_val.values,
        y_val=y_val.values,
        models_to_train=[
            'logistic_regression',
            'random_forest',
            'xgboost',
            'lightgbm',
            'catboost',
            'svm',
            'dnn',
            'cnn',
            'lstm'
        ],
        hyperparameter_tuning=True,
        include_deep_learning=True
    )
    
    print(f"✓ Trained {len(trained_models)} models:")
    for model_name in trained_models.keys():
        print(f"    • {model_name.upper()}")
    
    # ==================== STEP 6: MODEL EVALUATION ====================
    print("\n[STEP 6] MODEL EVALUATION & PERFORMANCE COMPARISON...")
    print("-" * 80)
    
    comparison_df = ModelComparison.compare_models(
        trained_models,
        X_test_selected.values,
        y_test.values,
        X_train_main.values,
        y_train_main.values
    )
    
    print("\n✓ MODEL PERFORMANCE SUMMARY:")
    print(comparison_df.to_string(index=False))
    
    # Save comparison results
    comparison_df.to_csv(f'{RESULTS_DIR}/model_comparison_advanced.csv', index=False)
    print(f"\n✓ Results saved to: {RESULTS_DIR}/model_comparison_advanced.csv")
    
    # ==================== STEP 7: VISUALIZATION ====================
    print("\n[STEP 7] GENERATING PERFORMANCE VISUALIZATIONS...")
    print("-" * 80)
    
    # Plot model comparison
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle('Advanced ML Models - Performance Comparison', fontsize=16, fontweight='bold')
    
    metrics = ['Accuracy', 'AUC-ROC', 'Precision (Weighted)', 'Recall (Weighted)', 'F1-Score (Weighted)', 'Log Loss']
    
    for idx, metric in enumerate(metrics):
        ax = axes[idx // 3, idx % 3]
        data = comparison_df.sort_values(metric, ascending=(metric == 'Log Loss'))
        colors = ['#2ecc71' if i == 0 else '#3498db' for i in range(len(data))]
        
        ax.barh(data['Model'], data[metric], color=colors)
        ax.set_xlabel(metric, fontweight='bold')
        ax.set_title(f'{metric} Comparison')
        ax.grid(axis='x', alpha=0.3)
        
        for i, v in enumerate(data[metric]):
            ax.text(v, i, f' {v:.4f}', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{RESULTS_DIR}/model_comparison_advanced.png', dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved to: {RESULTS_DIR}/model_comparison_advanced.png")
    plt.close()
    
    # ==================== STEP 8: TOP MODEL ANALYSIS ====================
    print("\n[STEP 8] TOP MODEL ANALYSIS...")
    print("-" * 80)
    
    best_model_name = comparison_df.loc[comparison_df['AUC-ROC'].idxmax(), 'Model']
    best_model, best_metadata = trained_models[best_model_name]
    
    print(f"\n✓ Best Performing Model: {best_model_name.upper()}")
    print(f"  AUC-ROC Score: {comparison_df.loc[comparison_df['Model'] == best_model_name, 'AUC-ROC'].values[0]:.4f}")
    print(f"  Accuracy: {comparison_df.loc[comparison_df['Model'] == best_model_name, 'Accuracy'].values[0]:.4f}")
    print(f"  F1-Score: {comparison_df.loc[comparison_df['Model'] == best_model_name, 'F1-Score (Weighted)'].values[0]:.4f}")
    
    # ==================== STEP 9: INTERPRETABILITY ====================
    print("\n[STEP 9] MODEL INTERPRETABILITY & EXPLANATIONS...")
    print("-" * 80)
    
    # Use SHAP for traditional ML models
    if best_model_name not in ['dnn', 'cnn', 'lstm']:
        print(f"\nGenerating SHAP explanations for {best_model_name}...")
        try:
            explainer = SHAPExplainer(best_model, X_train_main.values, feature_names=selected_features)
            shap_values = explainer.get_shap_values()
            
            # Plot feature importance
            fig, ax = plt.subplots(figsize=(10, 6))
            explainer.plot_feature_importance(shap_values, ax=ax)
            plt.title(f'Feature Importance - {best_model_name.upper()} (SHAP)', fontweight='bold')
            plt.tight_layout()
            plt.savefig(f'{RESULTS_DIR}/feature_importance_{best_model_name}.png', dpi=300, bbox_inches='tight')
            print(f"✓ SHAP explanation saved: {RESULTS_DIR}/feature_importance_{best_model_name}.png")
            plt.close()
        except Exception as e:
            print(f"  Note: SHAP explanation not available: {e}")
    else:
        print(f"\nNote: {best_model_name.upper()} is a deep learning model.")
        print("      Feature importance extraction requires different approaches (e.g., attention mechanisms)")
    
    # ==================== STEP 10: MODEL SAVING ====================
    print("\n[STEP 10] SAVING TRAINED MODELS...")
    print("-" * 80)
    
    saver = ModelSaver()
    
    for model_name, (model, metadata) in trained_models.items():
        save_path = saver.save_model(
            model,
            f'{RESULTS_DIR}/{model_name}_model',
            metadata=metadata
        )
        print(f"✓ {model_name}: {save_path}")
    
    # ==================== STEP 11: SUMMARY ====================
    print("\n" + "="*80)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("="*80)
    
    print("\n📊 SUMMARY:")
    print(f"  • Total Models Trained: {len(trained_models)}")
    print(f"  • Best Model: {best_model_name.upper()}")
    print(f"  • Best AUC-ROC: {comparison_df['AUC-ROC'].max():.4f}")
    print(f"  • Results Directory: {RESULTS_DIR}/")
    print("\n📁 Generated Files:")
    print(f"  • Model comparison CSV: model_comparison_advanced.csv")
    print(f"  • Performance visualization: model_comparison_advanced.png")
    print(f"  • Trained models (pickle format)")
    
    print("\n💡 ADVANCED MODELS INCLUDED:")
    print("  • LightGBM: Fast gradient boosting with optimal leaf-wise splitting")
    print("  • CatBoost: Specialized for categorical features with GPU acceleration")
    print("  • Deep Neural Network (DNN): 4-layer network with batch normalization")
    print("  • Convolutional Neural Network (CNN): 1D convolutions for feature patterns")
    print("  • Recurrent Neural Network (LSTM): Captures temporal clinical patterns")
    
    return trained_models, comparison_df


if __name__ == "__main__":
    trained_models, comparison_results = main()
