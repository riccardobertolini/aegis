"""Aegis exception hierarchy."""


class AegisBaseError(Exception):
    """Root of all Aegis exceptions."""


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
