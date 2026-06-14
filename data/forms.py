from django import forms

from data.models import Organization, Person, Site


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = '__all__'


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = '__all__'
