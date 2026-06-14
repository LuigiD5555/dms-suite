from django.core.files.storage import default_storage
from django.http import FileResponse, HttpResponseNotFound
from django.views import View
from django.views.generic import TemplateView
from dal import autocomplete

from data.forms import PersonForm
from data.models import Organization, Person, ZipCode


class ServeFileView(View):
    def get(self, request, file_url):
        file_path = default_storage.path(file_url)
        try:
            return FileResponse(open(file_path, 'rb'))
        except FileNotFoundError:
            return HttpResponseNotFound('File not found')


class OrganizationsView(TemplateView):
    template_name = 'customer/customers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_register_enabled'] = self.request.user.is_authenticated
        return context


class PeopleView(TemplateView):
    template_name = 'personal/personal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_register_enabled'] = self.request.user.is_authenticated
        context['form'] = PersonForm(self.request.POST or None)
        return context


class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Organization.objects.all()
        if self.q:
            qs = qs.filter(trade_name__istartswith=self.q) | qs.filter(legal_name__istartswith=self.q)
        return qs


class ZipCodeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ZipCode.objects.all()
        if self.q:
            qs = qs.filter(zip_code__istartswith=self.q) | qs.filter(normalized_settlement__icontains=self.q)
        return qs


class PersonAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Person.objects.select_related('organization').all()
        if self.q:
            qs = qs.filter(first_name__icontains=self.q) | qs.filter(last_name__icontains=self.q) | qs.filter(external_id__icontains=self.q)
        return qs


# Backward-compatible view names used by legacy templates/urls.
CustomersView = OrganizationsView
PersonalView = PeopleView
ClienteAutocomplete = OrganizationAutocomplete
CodigoPostalAutocomplete = ZipCodeAutocomplete
