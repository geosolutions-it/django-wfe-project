from django.shortcuts import HttpResponse
from django.views import View
from django_wfe.models import Job, Workflow
# Create your views here.

from django_wfe import execute_workflow, provide_input


class MyView(View):
    def get(self, request, *args, **kwargs):
        job = execute_workflow(workflow_id=Workflow.objects.first().id)
        return HttpResponse(f"OK: {job}")


class MyOtherView(View):
    def get(self, request, job, *args, **kwargs):
        provide_input(job_id=job, external_data={'some_data': 12})
        return HttpResponse(f"OK")
