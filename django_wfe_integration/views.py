from django.shortcuts import HttpResponse
from django.views import View
from django_wfe.models import Job, Workflow
# Create your views here.

from django_wfe import order_workflow_execution


class MyView(View):
    def get(self, request, *args, **kwargs):
        order_workflow_execution(workflow_id=Workflow.objects.first().id)
        return HttpResponse("OK")
