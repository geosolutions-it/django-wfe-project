import os

from time import sleep
from pathlib import Path
from pydantic import BaseModel

from django_wfe import steps


# Note: when working with django-wfe all outputs and inputs should be JSON serializable,
# since values are stored in the DB between the execution calls

class ValidateFileStep(steps.Step):
    """
    Step executing validation against the file located under provided path
    """

    class UserInputSchema(BaseModel):
        file: str

    def execute(self, _input=None, external_input=None, *args, **kwargs):
        file_path = external_input['file']

        # All stdout and stderr messages will be captured and logged to job log file.
        print(f"Received file for validation: {file_path}")

        if not os.path.isfile(file_path):
            print(f'{file_path}: is not a file.')
            # raising an error will stop job execution and mark the job as FAILED
            raise Exception(f'{file_path} is not a file.')

        try:
            with open(file_path, 'r'):
                pass
        except Exception as e:
            print(f'{file_path}: open for reading failed with an exception: {e}.')
            raise e

        # return file_path for FileTypeDecision Step
        return file_path


class FileTypeDecision(steps.Decision):
    """
    Decision step specifying which file handling step should be executed next based on the provided file extension
    """

    def transition(self, _input=None, *args, **kwargs):
        print(f"FileTypeDecision received input: {_input}")

        # _input of the Step is previous step's returned output
        file_path = _input

        if Path(file_path).suffix == '.json':
            # Next a step with index 0 will be executed from the Workflow.DIGRAPH[FileTypeDecision]
            return 0
        else:
            # Next a step with index 1 will be executed from the Workflow.DIGRAPH[FileTypeDecision]
            return 1


class JsonFileHandleStep(steps.Step):
    """
    Step handling *.json files
    """

    def execute(self, _input=None, *args, **kwargs):

        # you can access the certain Job's storage inside the Step:
        # the storage is a JSON database field, containing results and external_inputs of all previously executed steps, e.g.:
        # {
        #    "data":[
        #       {
        #          "step":"django_wfe.steps.__start__",
        #          "result":null
        #       },
        #       {
        #          "step":"django_wfe_integration.example_workflow_steps.ValidateFileStep",
        #          "external_data":{
        #             "file":"/tmp/file.json"
        #          },
        #          "result":"/tmp/file.json"
        #       }
        #    ]
        # }

        file_path = self.job.storage["data"][-1].get('result')
        # some fancy logic, e.g. upload of the file to an external service
        sleep(3)

        return file_path


class OtherFileHandleStep(steps.Step):
    """
    Step handling other file types
    """

    def execute(self, _input=None, *args, **kwargs):
        file_path = self.job.storage["data"][-1].get('result')
        # some other fancy logic
        sleep(3)

        return file_path


class FileHandlingCheckStep(steps.Step):
    """
    Step performing check of file handling steps
    """

    def execute(self, _input=None, *args, **kwargs):
        file_path = _input

        # check the File handlers actions

        sleep(10)
