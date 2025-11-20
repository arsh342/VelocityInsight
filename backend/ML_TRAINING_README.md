# ML Model Training & Optimization

## Overview
Optimized machine learning models for lap time prediction with hyperparameter tuning and enhanced feature engineering.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Train Models (with optimization)
```bash
# Default: Uses Optuna with 20 trials, 2 parallel jobs
python train_models_optimized.py

# Custom settings
python train_models_optimized.py --trials 30 --jobs 4

# Disable hyperparameter optimization (faster, less accurate)
python train_models_optimized.py --no-optuna
```

### 3. Train Models (legacy method)
```bash
python train_models.py
```

## Features

### Optimizations Implemented
- ✅ **Hyperparameter Tuning**: Optuna-based optimization (20 trials default)
- ✅ **Enhanced Features**: Rolling statistics, tire degradation proxy, race progress indicators
- ✅ **Parallel Training**: Multi-process training across tracks (2 jobs default)
- ✅ **Cross-Validation**: 5-fold CV during hyperparameter search
- ✅ **Better Regularization**: Added gamma, reg_alpha, reg_lambda
- ✅ **Improved Model**: XGBoost with optimized parameters

### Enhanced Features
1. **Rolling Statistics** (3-lap window)
   - Average, std, min, max recent lap times
   
2. **Tire Degradation Proxy**
   - Pace degradation vs. initial lap
   
3. **Race Progress Indicators**
   - Early/mid/late race flags
   - Continuous race progress percentage
   
4. **Consistency Metrics**
   - Standard deviation over last 5 laps

### Performance Metrics
Target metrics with optimizations:
- **MAE**: < 0.5s (Mean Absolute Error)
- **RMSE**: < 1.0s (Root Mean Squared Error)  
- **R²**: > 0.85 (R-squared score)

## Usage Examples

### Train all tracks with full optimization
```bash
python train_models_optim ized.py --trials 30 --jobs 4
```

### Quick training (no optimization)
```bash
python train_models_optimized.py --no-optuna --jobs 4
```

### Train single track (modify script)
```python
from train_models_optimized import train_single_track

track, predictor, metrics = train_single_track("barber", use_optuna=True, n_trials=20)
predictor.save(f"models/lap_time_predictor_{track}.pkl")
```

## Model Architecture

### Optimized Hyperparameters
- **n_estimators**: 300 (from Optuna tuning)
- **max_depth**: 6
- **learning_rate**: 0.05
- **subsample**: 0.9
- **colsample_bytree**: 0.9
- **min_child_weight**: 3
- **gamma**: 0.1
- **reg_alpha**: 0.5 (L1 regularization)
- **reg_lambda**: 1.0 (L2 regularization)

### Feature Count
- **Old**: 6 features
- **New**: 14+ features (depends on data availability)

## Benchmarks

### Training Time
- **Per track (no Optuna)**: ~10-30s
- **Per track (with Optuna, 20 trials)**: ~3-8 minutes
- **All tracks (parallel, 2 jobs, with Optuna)**: ~15-30 minutes

### Inference Time
- **Single prediction**: < 5ms
- **Batch (100 predictions)**: < 50ms

## File Structure
```
backend/
├── train_models_optimized.py  # New optimized training script
├── train_models.py              # Legacy training script
├── app/ml/
│   ├── models.py                # Updated with optimal params
│   ├── lap_time_predictor.py   # Production inference
│   └── ...
└── models/
    └── lap_time_predictor_{track}.pkl  # Trained models
```

## Troubleshooting

### API Connection Issues
If training fails to connect to API:
1. Ensure backend is running: `uvicorn app.main:app --reload`
2. Check API_BASE URL in script (default: `http://localhost:8000`)

### Out of Memory
If training uses too much memory:
- Reduce `--jobs` parameter
- Reduce `--trials` parameter
- Process fewer vehicles per track (edit `load_lap_times_from_api`)

### Slow Training
- Use `--no-optuna` flag to skip hyperparameter optimization
- Reduce `--trials` (e.g., `--trials 10`)
- Ensure `n_jobs=-1` in XGBoost params (uses all CPU cores)

## Next Steps

### TODO Optimizations (not yet implemented)
- [ ] GPU acceleration (requires CUDA GPU)
- [ ] Ensemble methods (XGBoost + LightGBM + RF)
- [ ] Model compression (reduce file size)
- [ ] Prediction batching API
- [ ] AutoML with AutoGluon or H2O

## Dependencies
- `xgboost>=2.1.1`
- `optuna>=3.0.0`
- `lightgbm>=4.0.0`
- `joblib>=1.3.0`
- `scikit-learn>=1.5.2`
- `pandas>=2.2.3`
- `numpy>=1.24.0`
