from django_wfe import workflows
from .example_workflow_steps import *
from django_wfe import steps


class ExampleWorkflow(workflows.Workflow):
    """
    Sample Workflow defining *.txt and *.json files handling.
    Files should be located under filesystem path, provided to ValidateFileStep
    """

    DIGRAPH = {
        steps.__start__: [ValidateFileStep],
        ValidateFileStep: [FileTypeDecision],
        FileTypeDecision: [JsonFileHandleStep, OtherFileHandleStep],
        OtherFileHandleStep: [FileHandlingCheckStep],
        JsonFileHandleStep: [FileHandlingCheckStep]
    }
