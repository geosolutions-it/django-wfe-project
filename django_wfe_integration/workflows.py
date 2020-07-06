from django_wfe import steps
from django_wfe import workflows

# from .example_workflow_steps import *


# class ExampleWorkflow(workflows.Workflow):
#     """
#     Sample Workflow defining *.txt and *.json files handling.
#     Files should be located under filesystem path, provided to ValidateFileStep
#     """

#     DIGRAPH = {
#         steps.__start__: [ValidateFileStep],
#         ValidateFileStep: [FileTypeDecision],
#         FileTypeDecision: [JsonFileHandleStep, OtherFileHandleStep],
#         OtherFileHandleStep: [FileHandlingCheckStep],
#         JsonFileHandleStep: [FileHandlingCheckStep],
#     }

from .upload_simple_workflow import *


class GeoServerSimpleUpload(workflows.Workflow):
    """
    Sample Workflow allowing to create a layer on GeoServer.
    Files should be located under filesystem path, provided to ValidateFileStep
    """

    DIGRAPH = {
        steps.__start__: [ValidateFileStep],
        ValidateFileStep: [FileTypeDecision],
        FileTypeDecision: [VectorFileHandleStep, RasterFileHandleStep],
        VectorFileHandleStep: [FileHandlingCheckStep],
        RasterFileHandleStep: [FileHandlingCheckStep],
    }
