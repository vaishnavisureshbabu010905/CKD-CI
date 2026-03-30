class APIError(Exception):
    """Raised for general API errors."""
    pass


class AuthError(Exception):
    """Raised for authentication/authorization issues."""
    pass


class PredictionError(Exception):
    """Raised for prediction-specific failures."""
    pass
