"""Aegis — unified client that combines all mixins.

Example usage::

    from client.aegis import Aegis

    a = Aegis()                          # connects to localhost:8000
    print(a.health())                    # {'status': 'ok', 'version': '...'}

    models = a.list_models()             # inference
    print(models)

    result = a.complete("Hello, world!") # inference
    print(result["text"])

    a.upload_document("docs/manual.pdf") # RAG
    answer = a.rag_query("What is Aegis?")
    print(answer["answer"])

    a.login("admin", "supersecret")      # security
    print(a.list_users())
"""
from .base import AegisClient
from .inference import InferenceMixin
from .documents import DocumentsMixin
from .training import TrainingMixin
from .admin import AdminMixin
from .security import SecurityMixin


class Aegis(SecurityMixin, AdminMixin, TrainingMixin, DocumentsMixin, InferenceMixin, AegisClient):
    """All-in-one Aegis API client.

    Args:
        base_url: Backend base URL (default: http://localhost:8000).
        token:    Optional pre-existing JWT bearer token.
        timeout:  HTTP timeout in seconds (default: 30).
    """
