import os
from django.conf import settings
from django.shortcuts import render, HttpResponseRedirect
from django_wfe.models import Job, Workflow, JobState

from django_wfe import execute_workflow_sync, provide_input


from .forms import UploadFileForm


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # save the file in the filesystem
            file_path = os.path.join(settings.UPLOADED_FILE_PATH, request.POST['name'])
            with open(file_path, 'wb+') as dest_file:
                for chunk in request.FILES['file']:
                    dest_file.write(chunk)

            # start synchronous django-wfe workflow execution
            # Job will stop at the first user defined step (ValidateFileStep) waiting for external input
            workflow = Workflow.objects.get(path='django_wfe_integration.workflows.ExampleWorkflow')
            job_id = execute_workflow_sync(workflow.id)

            # check job status - should be waiting for input on ValidateFileStep
            job = Job.objects.get(pk=job_id)
            if job.state != JobState.INPUT_REQUIRED or job.current_step != 'django_wfe_integration.example_workflow_steps.ValidateFileStep':
                # job's state is not the expected one
                return HttpResponseRedirect(f'/upload/status/{job_id}')

            # proceed with background workflow execution
            # (external_data dict should correspond to step's UserInputSchema structure)
            provide_input(job_id, {'file': file_path})

            return HttpResponseRedirect(f'/upload/status/{job_id}')
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})


def upload_status(reqest, upload_id):
    job = Job.objects.get(pk=upload_id)
    return render(reqest, 'upload_status.html', {'job_id': job.id, 'status': job.state, 'step': job.current_step, 'logfile': job.logfile})
