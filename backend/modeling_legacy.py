from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix,
    f1_score, mean_absolute_error, mean_squared_error, precision_score, r2_score, recall_score,
)
from sklearn.model_selection import KFold, StratifiedKFold, cross_validate, train_test_split
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC, SVR


@dataclass
class ModelRun:
    task: str
    target: str
    features: list[str]
    metrics: pd.DataFrame
    predictions: pd.DataFrame
    best_model_name: str
    best_pipeline: Pipeline
    confusion: pd.DataFrame | None
    class_report: pd.DataFrame | None
    cv_metrics: pd.DataFrame | None
    notes: list[str]


def infer_task(df: pd.DataFrame, target: str, forced: str = "Auto") -> str:
    if forced in {"Regression", "Classification"}:
        return forced.lower()
    s = df[target].dropna()
    if not pd.api.types.is_numeric_dtype(s):
        return "classification"
    unique = s.nunique()
    if unique <= max(10, int(len(s) * 0.05)):
        return "classification"
    return "regression"


def make_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    num_cols = list(X.select_dtypes(include=[np.number, "bool"]).columns)
    cat_cols = [c for c in X.columns if c not in num_cols]
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    cat_pipe = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return ColumnTransformer([("num", numeric_pipe, num_cols), ("cat", cat_pipe, cat_cols)], remainder="drop", verbose_feature_names_out=False)


def get_models(task: str, random_state: int = 42) -> dict[str, Any]:
    if task == "regression":
        return {
            "Linear Regression": LinearRegression(),
            "Ridge": Ridge(alpha=1.0),
            "Random Forest": RandomForestRegressor(n_estimators=250, random_state=random_state, n_jobs=-1),
            "Gradient Boosting": GradientBoostingRegressor(random_state=random_state),
            "KNN": KNeighborsRegressor(n_neighbors=5),
            "SVR": SVR(kernel="rbf", C=10.0, epsilon=0.1),
        }
    return {
        "Logistic Regression": LogisticRegression(max_iter=1500, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=250, random_state=random_state, n_jobs=-1, class_weight="balanced"),
        "Gradient Boosting": GradientBoostingClassifier(random_state=random_state),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "SVC": SVC(kernel="rbf", C=3.0, probability=True, class_weight="balanced"),
    }


def _reg_metrics(y_true, y_pred) -> dict[str, float]:
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    return {"R2": r2_score(y_true, y_pred), "RMSE": rmse, "MAE": mean_absolute_error(y_true, y_pred)}


def _clf_metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Balanced Accuracy": balanced_accuracy_score(y_true, y_pred),
        "F1 weighted": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "Precision weighted": precision_score(y_true, y_pred, average="weighted", zero_division=0),
        "Recall weighted": recall_score(y_true, y_pred, average="weighted", zero_division=0),
    }


def run_model_comparison(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    task_choice: str = "Auto",
    test_size: float = 0.2,
    random_state: int = 42,
    use_cv: bool = False,
    cv_folds: int = 5,
    selected_models: list[str] | None = None,
) -> ModelRun:
    work = df[[target] + features].replace([np.inf, -np.inf], np.nan).dropna(subset=[target]).copy()
    notes: list[str] = []
    task = infer_task(work, target, task_choice)
    X = work[features]
    y = work[target]
    if task == "classification":
        y = y.astype(str)
        counts = y.value_counts()
        if len(counts) < 2:
            raise ValueError("Classification target must contain at least two classes.")
        if counts.min() < 2:
            notes.append("Some classes have fewer than two samples; stratified splitting may be disabled.")
    else:
        y = pd.to_numeric(y, errors="coerce")
        valid = y.notna()
        X, y = X.loc[valid], y.loc[valid]
    if len(X) < 10:
        notes.append("Dataset is small; results should be treated as exploratory.")
    pre = make_preprocessor(X)
    models = get_models(task, random_state)
    if selected_models:
        models = {k: v for k, v in models.items() if k in selected_models}
    stratify = y if task == "classification" and y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=stratify)
    rows = []
    pred_store = pd.DataFrame({"actual": y_test.reset_index(drop=True)})
    fitted: dict[str, Pipeline] = {}
    for name, model in models.items():
        pipe = Pipeline([("preprocess", pre), ("model", model)])
        try:
            pipe.fit(X_train, y_train)
            pred = pipe.predict(X_test)
            fitted[name] = pipe
            pred_store[name] = pred
            metrics = _reg_metrics(y_test, pred) if task == "regression" else _clf_metrics(y_test, pred)
            metrics.update({"Model": name})
            rows.append(metrics)
        except Exception as exc:
            notes.append(f"{name} failed: {exc}")
    metrics_df = pd.DataFrame(rows)
    if metrics_df.empty:
        raise RuntimeError("No model could be trained successfully.")
    if task == "regression":
        metrics_df = metrics_df.sort_values(["R2", "RMSE"], ascending=[False, True])
        best_name = str(metrics_df.iloc[0]["Model"])
    else:
        metrics_df = metrics_df.sort_values(["F1 weighted", "Balanced Accuracy"], ascending=False)
        best_name = str(metrics_df.iloc[0]["Model"])
    best_pipe = fitted[best_name]
    best_pred = pred_store[best_name]
    confusion_df = None
    report_df = None
    if task == "classification":
        labels = sorted(pd.Series(y_test).astype(str).unique())
        cm = confusion_matrix(y_test.astype(str), pd.Series(best_pred).astype(str), labels=labels)
        confusion_df = pd.DataFrame(cm, index=[f"Actual {x}" for x in labels], columns=[f"Pred {x}" for x in labels])
        report_df = pd.DataFrame(classification_report(y_test.astype(str), pd.Series(best_pred).astype(str), output_dict=True, zero_division=0)).T.reset_index().rename(columns={"index": "class"})
    cv_df = None
    if use_cv:
        cv_rows = []
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state) if task == "classification" else KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
        scoring = ["r2", "neg_root_mean_squared_error", "neg_mean_absolute_error"] if task == "regression" else ["accuracy", "balanced_accuracy", "f1_weighted"]
        for name, model in models.items():
            pipe = Pipeline([("preprocess", make_preprocessor(X)), ("model", model)])
            try:
                scores = cross_validate(pipe, X, y, cv=cv, scoring=scoring, error_score="raise")
                row = {"Model": name}
                for key, values in scores.items():
                    if key.startswith("test_"):
                        metric = key.replace("test_", "")
                        val = float(np.mean(values))
                        if metric.startswith("neg_"):
                            metric = metric.replace("neg_", "")
                            val = -val
                        row[f"CV {metric}"] = val
                cv_rows.append(row)
            except Exception as exc:
                notes.append(f"CV failed for {name}: {exc}")
        if cv_rows:
            cv_df = pd.DataFrame(cv_rows)
    return ModelRun(task, target, features, metrics_df.reset_index(drop=True), pred_store, best_name, best_pipe, confusion_df, report_df, cv_df, notes)


def get_feature_names(pipe: Pipeline, X: pd.DataFrame) -> list[str]:
    pre = pipe.named_steps["preprocess"]
    try:
        return list(pre.get_feature_names_out())
    except Exception:
        return list(X.columns)


def model_importance(pipe: Pipeline, X: pd.DataFrame) -> pd.DataFrame:
    model = pipe.named_steps["model"]
    names = get_feature_names(pipe, X)
    if hasattr(model, "feature_importances_"):
        vals = model.feature_importances_
    elif hasattr(model, "coef_"):
        coef = model.coef_
        vals = np.abs(coef).mean(axis=0) if getattr(coef, "ndim", 1) > 1 else np.abs(coef)
    else:
        return pd.DataFrame(columns=["Feature", "Importance"])
    n = min(len(names), len(vals))
    return pd.DataFrame({"Feature": names[:n], "Importance": vals[:n]}).sort_values("Importance", ascending=False).reset_index(drop=True)
