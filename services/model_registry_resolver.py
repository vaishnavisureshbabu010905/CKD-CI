"""
Model registry version resolution service.

Handles model version lookup, fallback strategies, and registry synchronization.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModelRegistryResolver:
    """Resolve model versions from registry with fallback strategies."""
    
    def __init__(self, registry_data: List[Dict] = None):
        """Initialize with optional pre-loaded registry data."""
        self.registry: List[Dict] = registry_data or []
        self._active_model_cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None
    
    def update_registry(self, registry_data: List[Dict]) -> None:
        """Update internal registry cache."""
        self.registry = registry_data or []
        self._cache_timestamp = datetime.utcnow()
        logger.info(f"Registry updated with {len(self.registry)} models")
    
    def get_active_model_version(self) -> Optional[str]:
        """Get version of currently active model."""
        active = self._find_active_model()
        if active:
            return active.get("model_version") or active.get("version")
        return None
    
    def get_active_model_info(self) -> Optional[Dict]:
        """Get full info for active model."""
        return self._find_active_model()
    
    def resolve_version(self, runtime_version: Optional[str], fallback_to_active: bool = True) -> str:
        """
        Resolve model version using fallback strategy.
        
        Order of precedence:
        1. Runtime bundle version (if valid)
        2. Registry active model version
        3. Default fallback
        
        Args:
            runtime_version: Version from prediction runtime/bundle
            fallback_to_active: If True, use active model version as fallback
        
        Returns:
            Resolved version string
        """
        # Check if runtime version is valid
        if self._is_valid_version(runtime_version):
            return runtime_version
        
        # Try active model
        if fallback_to_active:
            active_version = self.get_active_model_version()
            if active_version:
                logger.info(f"Resolved unknown version '{runtime_version}' to active model version '{active_version}'")
                return active_version
        
        # Final fallback
        return "version_unavailable"
    
    def get_model_by_version(self, version: str) -> Optional[Dict]:
        """Get model info by version."""
        version = str(version or "").strip().lower()
        if not version or version in {"", "unknown", "n/a", "na", "none", "null"}:
            return None
        
        for model in self.registry:
            if str(model.get("model_version", "")).lower() == version or \
               str(model.get("version", "")).lower() == version:
                return model
        
        return None
    
    def list_all_versions(self) -> List[str]:
        """Get list of all model versions in registry."""
        versions = []
        for model in self.registry:
            v = model.get("model_version") or model.get("version")
            if v:
                versions.append(str(v))
        return sorted(set(versions))
    
    def get_version_info(self, version: str) -> Optional[Dict]:
        """Get detailed info for a specific version."""
        model = self.get_model_by_version(version)
        if not model:
            return None
        
        return {
            "version": model.get("model_version") or model.get("version"),
            "status": model.get("status"),
            "performance_metrics": model.get("performance_metrics") or {},
            "training_dataset": model.get("training_dataset"),
            "created_at": model.get("created_at"),
            "deployed_at": model.get("deployed_at"),
            "owner": model.get("owner"),
            "notes": model.get("notes"),
        }
    
    def compare_versions(self, version1: str, version2: str) -> Optional[Dict]:
        """Compare metrics between two versions."""
        info1 = self.get_version_info(version1)
        info2 = self.get_version_info(version2)
        
        if not info1 or not info2:
            return None
        
        metrics1 = info1.get("performance_metrics", {})
        metrics2 = info2.get("performance_metrics", {})
        
        comparison = {
            "version1": version1,
            "version2": version2,
            "metrics": {}
        }
        
        # Compare each metric
        for metric_name in set(list(metrics1.keys()) + list(metrics2.keys())):
            val1 = metrics1.get(metric_name)
            val2 = metrics2.get(metric_name)
            
            if val1 is not None and val2 is not None:
                try:
                    diff = float(val2) - float(val1)
                    pct_change = (diff / float(val1) * 100) if float(val1) != 0 else 0
                    comparison["metrics"][metric_name] = {
                        "version1": val1,
                        "version2": val2,
                        "difference": diff,
                        "percent_change": pct_change,
                        "improvement": diff > 0 if metric_name in {"accuracy", "precision", "recall", "f1", "auc"} else diff < 0,
                    }
                except (ValueError, TypeError):
                    pass
        
        return comparison
    
    def _find_active_model(self) -> Optional[Dict]:
        """Find currently active/production model."""
        for model in self.registry:
            status = str(model.get("status", "")).lower()
            if status in {"active", "production", "live", "deployed"}:
                return model
        
        # Fallback: return most recent
        if self.registry:
            return sorted(self.registry, 
                         key=lambda m: m.get("created_at", ""), 
                         reverse=True)[0]
        
        return None
    
    def _is_valid_version(self, version: Optional[str]) -> bool:
        """Check if version string is valid/known."""
        if not version:
            return False
        
        version_str = str(version).strip().lower()
        
        # Known invalid tokens
        invalid_tokens = {"", "unknown", "n/a", "na", "none", "null", "undefined", "-", "?"}
        if version_str in invalid_tokens:
            return False
        
        # Very short strings are probably errors
        if len(version_str) < 2:
            return False
        
        return True


class VersionedPrediction:
    """Wrapper for prediction with resolved version info."""
    
    def __init__(self, prediction_data: Dict, resolver: ModelRegistryResolver):
        self.data = prediction_data
        self.resolver = resolver
    
    def get_resolved_version(self) -> str:
        """Get version with fallback resolution."""
        runtime_version = self.data.get("model_version")
        return self.resolver.resolve_version(runtime_version)
    
    def get_version_info(self) -> Optional[Dict]:
        """Get version info from registry."""
        resolved_version = self.get_resolved_version()
        if resolved_version and resolved_version != "version_unavailable":
            return self.resolver.get_version_info(resolved_version)
        return None
    
    def to_dict_with_resolved_version(self) -> Dict:
        """Return prediction dict with resolved version."""
        result = dict(self.data)
        result["model_version"] = self.get_resolved_version()
        result["model_version_resolved"] = self.data.get("model_version") != self.get_resolved_version()
        return result
