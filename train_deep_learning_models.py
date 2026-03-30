#!/usr/bin/env python3
"""
Deep Learning Models Training Script
Trains DNN, CNN, and LSTM models separately
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from data.generate_synthetic_data import CKDCognitiveDataGenerator
from src.preprocessing import preprocess_pipeline
from src.models import DeepNeuralNetworkModel, ConvolutionalNeuralNetworkModel, RecurrentNeuralNetworkModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("=" * 70)
    print("DEEP LEARNING MODELS TRAINING")
    print("=" * 70)
    
    # Step 1: Generate synthetic data
    print("\n[STEP 1] Generating synthetic dataset...")
    generator = CKDCognitiveDataGenerator()
    df = generator.generate_dataset(n_samples=2000)
    print(f"✓ Generated {len(df)} samples with {df.shape[1]} features")
    
    # Step 2: Preprocess data
    print("\n[STEP 2] Preprocessing data...")
    result = preprocess_pipeline(
        df,
        target_col='cognitive_risk',
        test_size=0.2,
        handle_imbalance=True,
        engineer_features=True
    )
    
    X_train = result['X_train']
    X_test = result['X_test']
    y_train = result['y_train']
    y_test = result['y_test']
    
    print(f"✓ Training set: {X_train.shape}")
    print(f"✓ Test set: {X_test.shape}")
    
    # Step 3: Train DNN
    print("\n[STEP 3] Training Deep Neural Network (DNN)...")
    print("-" * 70)
    try:
        dnn_model, dnn_metadata = DeepNeuralNetworkModel.create_and_train(
            X_train, y_train
        )
        if dnn_model:
            y_pred_dnn = dnn_model.predict(X_test)
            y_pred_proba_dnn = dnn_model.predict_proba(X_test) if hasattr(dnn_model, 'predict_proba') else None
            print(f"✓ DNN trained successfully")
            print(f"  - Training accuracy: {dnn_metadata.get('training_accuracy', 'N/A')}")
            print(f"  - Validation loss: {dnn_metadata.get('validation_loss', 'N/A')}")
            print(f"  - Test predictions shape: {y_pred_dnn.shape}")
        else:
            print("✗ DNN training failed")
    except Exception as e:
        print(f"✗ DNN training error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Train CNN
    print("\n[STEP 4] Training Convolutional Neural Network (CNN)...")
    print("-" * 70)
    try:
        cnn_model, cnn_metadata = ConvolutionalNeuralNetworkModel.create_and_train(
            X_train, y_train
        )
        if cnn_model:
            y_pred_cnn = cnn_model.predict(X_test)
            y_pred_proba_cnn = cnn_model.predict_proba(X_test) if hasattr(cnn_model, 'predict_proba') else None
            print(f"✓ CNN trained successfully")
            print(f"  - Training accuracy: {cnn_metadata.get('training_accuracy', 'N/A')}")
            print(f"  - Validation loss: {cnn_metadata.get('validation_loss', 'N/A')}")
            print(f"  - Test predictions shape: {y_pred_cnn.shape}")
        else:
            print("✗ CNN training failed")
    except Exception as e:
        print(f"✗ CNN training error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Train LSTM
    print("\n[STEP 5] Training Long Short-Term Memory Network (LSTM)...")
    print("-" * 70)
    try:
        lstm_model, lstm_metadata = RecurrentNeuralNetworkModel.create_and_train(
            X_train, y_train
        )
        if lstm_model:
            y_pred_lstm = lstm_model.predict(X_test)
            y_pred_proba_lstm = lstm_model.predict_proba(X_test) if hasattr(lstm_model, 'predict_proba') else None
            print(f"✓ LSTM trained successfully")
            print(f"  - Training accuracy: {lstm_metadata.get('training_accuracy', 'N/A')}")
            print(f"  - Validation loss: {lstm_metadata.get('validation_loss', 'N/A')}")
            print(f"  - Test predictions shape: {y_pred_lstm.shape}")
        else:
            print("✗ LSTM training failed")
    except Exception as e:
        print(f"✗ LSTM training error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("DEEP LEARNING TRAINING COMPLETED")
    print("=" * 70)

if __name__ == '__main__':
    main()
