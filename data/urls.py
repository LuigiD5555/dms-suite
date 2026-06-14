from django.urls import path
from data import views

urlpatterns = [
    path('organizations/', views.OrganizationsView.as_view(), name='organizations'),
    path('people/',        views.PeopleView.as_view(),        name='people'),
    path('customers/',     views.OrganizationsView.as_view(), name='customers'),
    path('personal/',      views.PeopleView.as_view(),        name='personal'),
    path('employees/',     views.PeopleView.as_view(),        name='employees'),
    path('candidates/',    views.PeopleView.as_view(),        name='candidates'),
    path('autocomplete/organizations/', views.OrganizationAutocomplete.as_view(), name='organization-autocomplete'),
    path('autocomplete/zip-codes/',     views.ZipCodeAutocomplete.as_view(),      name='zipcode-autocomplete'),
    path('autocomplete/people/',        views.PersonAutocomplete.as_view(),        name='person-autocomplete'),
    path('media/<path:file_url>/',      views.ServeFileView.as_view(),             name='serve-file'),
]
