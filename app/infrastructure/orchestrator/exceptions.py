class PipelineError(Exception):
    """Base exception for pipeline orchestration."""


class PipelineConfigurationError(PipelineError):
    """Raised when the pipeline definition is invalid."""


class PipelineExecutionError(PipelineError):
    """Raised when pipeline execution fails."""