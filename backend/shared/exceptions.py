"""Aegis exception hierarchy."""


class AegisBaseError(Exception):
    """Root of all Aegis exceptions."""
    def __init__(self, message: str = "", **context: object) -> None:
        super().__init__(message)
        self.message = message
        self.context = context



class ConfigurationError(AegisBaseError):
    """Invalid or missing configuration."""


class InferenceError(AegisBaseError):
    """Model inference failure."""


class KnowledgeError(AegisBaseError):
    """Vector store / retrieval failure."""


class DocumentError(AegisBaseError):
    """Document processing failure."""


class TrainingError(AegisBaseError):
    """Fine-tuning / training failure."""


class PluginError(AegisBaseError):
    """Plugin loading or execution failure."""


class AuthenticationError(AegisBaseError):
    """Authentication failure (bad credentials, expired/invalid token)."""


class AuthorizationError(AegisBaseError):
    """Authorization failure (insufficient permissions)."""


class IntegrityError(AegisBaseError):
    """Data or model integrity check failed."""


class BackupError(AegisBaseError):
    """Backup / restore failure."""


class ModelNotFoundError(AegisBaseError):
    """Raised when a requested model cannot be found in the registry."""

    def __init__(self, message: str = "", model_id: str = "", **context: object) -> None:
        super().__init__(message or f"Model not found: {model_id}", **context)
        self.model_id = model_id


class ModelLoadError(Exception):
    """Auto-added: raised for modelload failures."""

    def __init__(self, message: str = "", **context: object) -> None:
        super().__init__(message)
        self.context = context
