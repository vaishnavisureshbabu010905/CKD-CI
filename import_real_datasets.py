"""
Quick Data Import Script for NHANES and Charles Datasets

Usage:
    python import_real_datasets.py --source nhanes
    python import_real_datasets.py --source charles --file path/to/charles_data.csv
    python import_real_datasets.py --source both
"""

import pandas as pd
import argparse
import logging
from pathlib import Path
from src.data_importers import NHANESImporter, CharlesDatasetImporter, UnifiedDataLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def import_nhanes(output_dir: str = 'data/imported'):
    """Import NHANES dataset."""
    logger.info("=" * 80)
    logger.info("IMPORTING NHANES DATASET")
    logger.info("=" * 80)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = UnifiedDataLoader.load_data('nhanes', process=True)
    
    # Save to CSV
    output_path = Path(output_dir) / 'nhanes_data.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved NHANES data to: {output_path}")
    
    # Display summary
    logger.info(f"\nDataset Summary:")
    logger.info(f"  Shape: {df.shape}")
    logger.info(f"  Columns: {df.columns.tolist()}")
    logger.info(f"\nData Types:")
    logger.info(df.dtypes)
    logger.info(f"\nFirst few rows:")
    logger.info(df.head())
    
    return df


def import_charles(file_path: str = None, output_dir: str = 'data/imported'):
    """Import Charles dataset."""
    logger.info("=" * 80)
    logger.info("IMPORTING CHARLES DATASET")
    logger.info("=" * 80)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = UnifiedDataLoader.load_data('charles', file_path=file_path, process=True)
    
    # Save to CSV
    output_path = Path(output_dir) / 'charles_data.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Saved Charles data to: {output_path}")
    
    # Display summary
    logger.info(f"\nDataset Summary:")
    logger.info(f"  Shape: {df.shape}")
    logger.info(f"  Columns: {df.columns.tolist()}")
    logger.info(f"\nData Types:")
    logger.info(df.dtypes)
    logger.info(f"\nFirst few rows:")
    logger.info(df.head())
    
    return df


def import_both(charles_file: str = None, output_dir: str = 'data/imported'):
    """Import and merge both NHANES and Charles datasets."""
    logger.info("=" * 80)
    logger.info("IMPORTING AND MERGING NHANES & CHARLES DATASETS")
    logger.info("=" * 80)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load both datasets
    logger.info("\n[1/3] Loading NHANES data...")
    nhanes_df = UnifiedDataLoader.load_data('nhanes', process=True)
    logger.info(f"  NHANES shape: {nhanes_df.shape}")
    
    logger.info("\n[2/3] Loading Charles data...")
    charles_df = UnifiedDataLoader.load_data('charles', file_path=charles_file, process=True)
    logger.info(f"  Charles shape: {charles_df.shape}")
    
    logger.info("\n[3/3] Merging datasets...")
    # Create a merged dataset
    merged_df = pd.concat([nhanes_df, charles_df], ignore_index=True)
    logger.info(f"  Merged shape: {merged_df.shape}")
    
    # Save merged data
    merged_path = Path(output_dir) / 'merged_nhanes_charles.csv'
    merged_df.to_csv(merged_path, index=False)
    logger.info(f"Saved merged data to: {merged_path}")
    
    # Save individual datasets
    nhanes_path = Path(output_dir) / 'nhanes_data.csv'
    charles_path = Path(output_dir) / 'charles_data.csv'
    
    nhanes_df.to_csv(nhanes_path, index=False)
    charles_df.to_csv(charles_path, index=False)
    
    logger.info(f"Saved NHANES data to: {nhanes_path}")
    logger.info(f"Saved Charles data to: {charles_path}")
    
    # Display summary
    logger.info(f"\nMerged Dataset Summary:")
    logger.info(f"  Total Shape: {merged_df.shape}")
    logger.info(f"  Columns: {merged_df.columns.tolist()}")
    logger.info(f"\nData Types:")
    logger.info(merged_df.dtypes)
    logger.info(f"\nFirst few rows:")
    logger.info(merged_df.head())
    
    return merged_df


def main():
    parser = argparse.ArgumentParser(
        description='Import NHANES and/or Charles clinical datasets'
    )
    parser.add_argument(
        '--source',
        choices=['nhanes', 'charles', 'both'],
        default='both',
        help='Data source to import'
    )
    parser.add_argument(
        '--charles-file',
        type=str,
        default=None,
        help='Path to Charles dataset CSV/Excel file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/imported',
        help='Output directory for imported data'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Data Import Configuration:")
    logger.info(f"  Source: {args.source}")
    logger.info(f"  Charles File: {args.charles_file or 'Use mock data'}")
    logger.info(f"  Output Dir: {args.output_dir}")
    
    if args.source == 'nhanes':
        import_nhanes(args.output_dir)
    elif args.source == 'charles':
        import_charles(args.charles_file, args.output_dir)
    elif args.source == 'both':
        import_both(args.charles_file, args.output_dir)
    
    logger.info("\n" + "=" * 80)
    logger.info("IMPORT COMPLETE!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
