from django.urls import path
from django.shortcuts import HttpResponseRedirect
from django_wfe_integration.views import upload_file, upload_status


urlpatterns = [
    path("", lambda request: HttpResponseRedirect(f"/upload/")),
    path("upload/", upload_file, name="upload_file"),
    path("upload/status/<int:upload_id>", upload_status, name="upload_status"),
]
