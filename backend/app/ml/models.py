from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor


class LapTimePredictor:
    def __init__(self):
        self.model: Optional[XGBRegressor] = None
        self.feature_names: Optional[list[str]] = None

    def fit(self, df_features: pd.DataFrame, target_col: str = "lap_time_s") -> dict:
        df = df_features.dropna(subset=[target_col]).copy()
        y = df[target_col].astype(float)
        X = df.drop(columns=[target_col])
        self.feature_names = list(X.columns)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, shuffle=False)
        # Optimized hyperparameters from tuning experiments
        self.model = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.5,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)
        preds = self.model.predict(X_test)
        return {
            "mae": float(mean_absolute_error(y_test, preds)),
            "r2": float(r2_score(y_test, preds)),
        }

    def predict(self, X: pd.DataFrame) -> pd.Series:
        if self.model is None:
            raise RuntimeError("Model not fitted")
        return pd.Series(self.model.predict(X), index=X.index)
