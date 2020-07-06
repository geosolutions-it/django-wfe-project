import os
import uuid
import shutil
import zipfile
import tempfile

from time import sleep
from pathlib import Path
from pydantic import BaseModel

from django_wfe import steps

# Note: when working with django-wfe all outputs and inputs should be JSON serializable,
# since values are stored in the DB between the execution calls

from osgeo import gdal

from .utils import (
    SUPPORTED_EXTS, vec_exts, cov_exts,
    get_files,
    upload_to_geoserver
)


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def get_base_filename(files):
    base_filename = None
    for _ext, _file in files.items():
        if f'.{_ext}' in SUPPORTED_EXTS:
            base_filename = _file
            break
    return base_filename


class ValidateFileStep(steps.Step):
    """
    Step executing validation against the file located under provided path
    """

    class UserInputSchema(BaseModel):
        file: str
        name: str
        workspace: str

    def execute(self, _input=None, external_input=None, *args, **kwargs):
        file_path = external_input["file"]

        # All stdout and stderr messages will be captured and logged to job log file.
        print(f"Received file for validation: {file_path}")

        if not os.path.isfile(file_path):
            print(f"{file_path}: is not a file.")
            # raising an error will stop job execution and mark the job as FAILED
            raise Exception(f"{file_path} is not a file.")

        try:
            with open(file_path, "r"):
                pass
        except Exception as e:
            print(f"{file_path}: open for reading failed with an exception: {e}.")
            raise e

        print(f"Testing zip file: {file_path}")
        the_zip_file = zipfile.ZipFile(file_path)
        ret = the_zip_file.testzip()
        if ret:
            print(f"First bad file in zip: {ret}")
            raise Exception(f"First bad file in zip: {ret}")
        else:
            print(f"Zip file is good: {file_path}")

        temp_dir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            print(f"Exctracting to: {temp_dir.name}")
            zip_ref.extractall(temp_dir.name)

        dst = os.path.join(os.path.dirname(file_path),
                           str(uuid.uuid4())[:8])
        if not os.path.exists(dst):
            os.makedirs(dst)
        copytree(temp_dir.name, dst)

        files = get_files(dst)
        print(f"Geospatial data files found: {files}")

        base_filename = get_base_filename(files)
        ds = gdal.OpenEx(base_filename)
        if ds and (ds.RasterCount > 0 or ds.GetLayerCount() > 0):
            print(f"{base_filename}: is a valid geospatial datasource.")
            pass
        else:
            print(
                f"{base_filename}: is not a valid or readbale geospatial datasource.")
            raise Exception(
                f"{base_filename}: is not a valid or readbale geospatial datasource.")

        # return files for FileTypeDecision Step
        return files


class FileTypeDecision(steps.Decision):
    """
    Decision step specifying which file handling step should be executed next based on the provided file extension
    """

    def transition(self, _input=None, external_input=None, *args, **kwargs):
        print(f"FileTypeDecision received input: {_input}")

        # _input of the Step is previous step's returned output
        files = _input
        base_filename = get_base_filename(files)
        if Path(base_filename).suffix in vec_exts:
            # Next a step with index 0 will be executed from the Workflow.DIGRAPH[FileTypeDecision]
            print(f"FileTypeDecision VECTOR data file found: {base_filename}")
            return 0
        elif Path(base_filename).suffix in cov_exts:
            # Next a step with index 1 will be executed from the Workflow.DIGRAPH[FileTypeDecision]
            print(f"FileTypeDecision RASTER data file found: {base_filename}")
            return 1
        else:
            print(f"FileTypeDecision not a valid input: {_input}")
            raise Exception(f"FileTypeDecision not a valid input: {_input}")


class VectorFileHandleStep(steps.Step):
    """
    Step handling VECTOR files ingestion
    """

    def execute(self, _input=None, *args, **kwargs):
        # you can access the certain Job's storage inside the Step:
        # the storage is a JSON database field, containing results and external_inputs of all previously executed steps, e.g.:
        # {
        #     "data": [
        #         {
        #             "step": "django_wfe.steps.__start__",
        #             "result": null
        #         },
        #         {
        #             "step": "django_wfe_integration.upload_simple_workflow.ValidateFileStep",
        #             "external_data": {
        #                 "file": "/tmp/san_andres_y_providencia_administrative.zip"
        #             },
        #             "result": {
        #                 "shp": "/tmp/8374917a/san_andres_y_providencia_administrative.shp",
        #                 "dbf": "/tmp/8374917a/san_andres_y_providencia_administrative.dbf",
        #                 "shx": "/tmp/8374917a/san_andres_y_providencia_administrative.shx",
        #                 "prj": "/tmp/8374917a/san_andres_y_providencia_administrative.prj"
        #             }
        #         },
        #         {
        #             "step": "django_wfe_integration.upload_simple_workflow.FileTypeDecision",
        #             "result": null
        #         }
        #     ]
        # }
        files = {}
        external_data = {}
        for item in self.job.storage["data"]:
            if 'ValidateFileStep' in item.get('step') and item.get("result"):
                files = item.get("result")
                external_data = item.get("external_data")
                print(f"VectorFileHandleStep received input: {external_data}")
                break

        # some fancy logic, e.g. upload of the file to an external service
        base_filename = get_base_filename(files)
        results = upload_to_geoserver(
            layer_name=external_data.get('name'),
            layer_type='VECTOR',
            files=files,
            base_file=base_filename,
            charset='UTF-8',
            overwrite=True,
            workspace=external_data.get('workspace'))
        return results


class RasterFileHandleStep(steps.Step):
    """
    Step handling RASTER files ingestion
    """

    def execute(self, _input=None, *args, **kwargs):
        files = {}
        external_data = {}
        for item in self.job.storage["data"]:
            if 'ValidateFileStep' in item.get('step') and item.get("result"):
                files = item.get("result")
                external_data = item.get("external_data")
                print(f"RasterFileHandleStep received input: {external_data}")
                break

        # some fancy logic, e.g. upload of the file to an external service
        base_filename = get_base_filename(files)
        results = upload_to_geoserver(
            layer_name=external_data.get('name'),
            layer_type='RASTER',
            files=files,
            base_file=base_filename,
            charset='UTF-8',
            overwrite=True,
            workspace=external_data.get('workspace'))
        return results


class FileHandlingCheckStep(steps.Step):
    """
    Step performing check of file handling steps
    """

    def execute(self, _input=None, *args, **kwargs):
        print(_input)
        # check the File handlers actions
        sleep(3)
