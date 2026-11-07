# Dataset Import Guide - NHANES & Charles

## 🎯 Quick Start

### Import NHANES Data Only
```bash
python import_real_datasets.py --source nhanes
```

### Import Charles Data Only
```bash
python import_real_datasets.py --source charles --charles-file /path/to/your/data.csv
```

### Import & Merge Both Datasets
```bash
python import_real_datasets.py --source both
```

---

## 📊 Data Sources

### 1. NHANES (National Health and Nutrition Examination Survey)
**What it is:** Real public health data from CDC
- Population-based survey data
- Includes kidney function markers
- Demographics and health measurements
- Publicly available (no authentication needed)

**Features available:**
- Age, gender, race/ethnicity
- Creatinine, BUN, urine albumin
- Blood pressure, glucose, cholesterol
- BMI, smoking status
- Calculated eGFR values

**Automatic download:** Yes (from CDC)

---

### 2. Charles Dataset
**What it is:** Clinical health records dataset
- Patient health measurements
- Laboratory results
- Medication records
- Visit history

**Features available:**
- Patient ID, visit dates
- Creatinine, eGFR, BUN
- Urine ACR
- Blood pressure, glucose
- Cholesterol panels
- CKD & diabetes diagnosis

**How to use:** Provide your own CSV/Excel file

---

## 🔧 In-Code Usage

### Import NHANES Data
```python
from src.data_importers import UnifiedDataLoader

# Load NHANES data
nhanes_df = UnifiedDataLoader.load_data('nhanes', process=True)
print(nhanes_df.shape)
print(nhanes_df.head())
```

### Import Charles Data
```python
from src.data_importers import UnifiedDataLoader

# Load Charles data from file
charles_df = UnifiedDataLoader.load_data(
    'charles',
    file_path='path/to/charles_data.csv',
    process=True
)
print(charles_df.shape)
```

### Merge Both Datasets
```python
from src.data_importers import UnifiedDataLoader

# Merge NHANES and Charles
merged_df = UnifiedDataLoader.merge_datasets(
    sources=['nhanes', 'charles'],
    file_paths={'charles': 'path/to/charles_data.csv'}
)
print(merged_df.shape)
```

---

## 📁 Output Files

After running import script, you'll have:

```
data/imported/
├── nhanes_data.csv              # NHANES data only
├── charles_data.csv             # Charles data only
└── merged_nhanes_charles.csv    # Combined dataset
```

---

## 🔬 Using Imported Data with ML Pipeline

### With NHANES Data
```python
from src.data_importers import UnifiedDataLoader
from src.preprocessing import preprocess_pipeline
from src.models import ModelTrainer

# Load NHANES
df = UnifiedDataLoader.load_data('nhanes', process=True)

# Preprocess
prep_result = preprocess_pipeline(df)
X_train = prep_result['X_train']
y_train = prep_result['y_train']

# Train models
models = ModelTrainer.train_all_models(X_train, y_train)
```

### With Charles Data
```python
from src.data_importers import UnifiedDataLoader
from src.preprocessing import preprocess_pipeline
from src.models import ModelTrainer

# Load Charles
df = UnifiedDataLoader.load_data(
    'charles',
    file_path='your_data.csv',
    process=True
)

# Preprocess
prep_result = preprocess_pipeline(df)
X_train = prep_result['X_train']
y_train = prep_result['y_train']

# Train models
models = ModelTrainer.train_all_models(X_train, y_train)
```

---

## 📋 Supported File Formats for Charles

- ✅ CSV files (.csv)
- ✅ Excel files (.xlsx)
- ✅ Tab-separated values (.tsv)

---

## ⚙️ Data Processing Details

### NHANES Processing
1. Downloads data from CDC if available
2. Extracts kidney function data
3. Calculates eGFR using CKD-EPI formula
4. Creates CKD stage categories (1-5)
5. Handles missing values with median imputation

### Charles Processing
1. Loads your CSV/Excel file
2. Standardizes column names
3. Handles missing values
4. Calculates CKD risk categories
5. Derives additional risk factors (diabetes, hypertension)

---

## 🎯 Available Features After Import

Both datasets will have these standardized features:
- Age, gender
- Creatinine, BUN, urine albumin-to-creatinine ratio
- eGFR (estimated glomerular filtration rate)
- Blood pressure (systolic/diastolic)
- Glucose/HbA1c
- Cholesterol (total, HDL, LDL)
- Triglycerides
- BMI
- Smoking status
- Diabetes diagnosis
- Hypertension diagnosis
- CKD stage classification

---

## 📊 Example: Complete Workflow

```bash
# Step 1: Import data
python import_real_datasets.py --source both

# Step 2: Train models with real data
python run_advanced_models.py  # Will use imported data if available

# Step 3: View results
cat results/advanced_models/model_comparison_advanced.csv
```

---

## 🐛 Troubleshooting

### Error: "Charles file not found"
```bash
# Provide the correct path
python import_real_datasets.py --source charles --charles-file C:\path\to\data.csv
```

### Error: "Can't download NHANES data"
- NHANES importer will automatically use mock data
- Or provide your own dataset via Charles option

### Error: "Column not found in Charles data"
- Check your CSV has expected column names
- Importer will auto-standardize common naming conventions

---

## 💡 Tips

1. **First time?** Start with mock data:
   ```python
   df = UnifiedDataLoader.load_data('mock', n_samples=5000)
   ```

2. **Have Charles data?** Use your own:
   ```bash
   python import_real_datasets.py --source charles --charles-file mydata.csv
   ```

3. **Want everything?** Merge both sources:
   ```bash
   python import_real_datasets.py --source both --charles-file mydata.csv
   ```

4. **Large datasets?** Process in chunks:
   ```python
   df = pd.read_csv('data.csv', chunksize=10000)
   # Process each chunk
   ```

---

## 📚 Related Files

- `src/data_importers.py` - Main import module
- `import_real_datasets.py` - Command-line script
- `src/preprocessing.py` - Data preprocessing
- `src/models.py` - ML models
- `run_advanced_models.py` - Full pipeline example

---

## ✅ Next Steps

1. **Run the importer:**
   ```bash
   python import_real_datasets.py --source both
   ```

2. **Use your data with ML:**
   ```python
   from src.data_importers import UnifiedDataLoader
   df = UnifiedDataLoader.load_data('charles', file_path='your_data.csv')
   # Train models...
   ```

3. **Check results:**
   ```bash
   ls data/imported/
   ```

---

**Status:** ✅ Ready to import real clinical data!
