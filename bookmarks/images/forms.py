from django import forms
from .models import Image
from django.core.files.base import ContentFile
from django.utils.text import slugify
import requests


class ImageCreateForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ['title', 'url', 'description']
        widgets = {
            'url': forms.HiddenInput,
        }

    def save(self,
             force_insert=False,
             force_update=False,
             commit=True):
        image = super().save(commit=False)
        image_url = self.cleaned_data['url']
        extension = image_url.split('.')[-1].lower()
        name = slugify(image.title)
        image_name = f'{name}.{extension}'
        response = requests.get(image_url)
        image.image.save(image_name, ContentFile(response.content), save=False)

        if commit:
            image.save()

        return image

    def clean_url(self):
        url = self.cleaned_data['url']
        extension = url.rsplit('.')[-1].lower()
        if extension in {'jpg', 'png', 'jpeg'}:
            return url
        raise forms.ValidationError('The given url doesn\'t '
                                    'match valid extension')
