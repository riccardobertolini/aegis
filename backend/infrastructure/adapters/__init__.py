"""Concrete adapter implementations for each port."""
# Adapters are implemented in subsequent phases.
# Each adapter lives in its own module:
#   inference.py  -> MambaInferenceAdapter
#   knowledge.py  -> ChromaKnowledgeAdapter
#   memory.py     -> SQLiteMemoryAdapter
#   document.py   -> LocalDocumentAdapter
#   security.py   -> LocalSecurityAdapter
#   training.py   -> MambaTrainingAdapter
#   plugin.py     -> SandboxPluginAdapter
#   speech.py     -> WhisperCoquiSpeechAdapter
#   log_engine.py -> DuckDBLogAdapter
#   timeseries.py -> DuckDBTimeSeriesAdapter
#   translation.py-> ArgosTranslationAdapter
#   administration.py -> LocalAdministrationAdapter
