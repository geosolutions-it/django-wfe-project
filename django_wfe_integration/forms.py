from django import forms


class UploadFileForm(forms.Form):
    name = forms.CharField(max_length=255)
    workspace = forms.CharField(max_length=255)
    file = forms.FileField()
