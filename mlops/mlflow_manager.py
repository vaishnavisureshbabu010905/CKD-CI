import mlflow
from datetime import datetime
from typing import Dict, Optional


MLFLOW_EXPERIMENT_NAME = "CKD-CI"


def start_run(run_name: Optional[str] = None):
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    return mlflow.start_run(run_name=run_name)


def log_metrics(metrics: Dict[str, float], step: Optional[int] = None) -> None:
    for k, v in metrics.items():
        mlflow.log_metric(k, float(v), step=step)


def log_params(params: Dict[str, object]) -> None:
    for k, v in params.items():
        mlflow.log_param(k, v)


def log_model(model, artifact_path: str = "model") -> None:
    # model is expected to be a pickle-able object or a supported flavor
    mlflow.sklearn.log_model(sk_model=model, artifact_path=artifact_path)


def register_model(model_uri: str, name: str = "CKD_CI_MODEL") -> str:
    """Register a model in MLflow Model Registry and return the registered model version string."""
    result = mlflow.register_model(model_uri=model_uri, name=name)
    # wait for model to be ready may be required in some setups
    return f"{result.name}:{result.version}"
