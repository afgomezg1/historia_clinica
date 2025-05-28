from django.urls import path
from .views import monthly_report, bulk_create_diagnoses

urlpatterns = [
    # Public report endpoint
    path('api/report/', monthly_report, name='monthly_report'),

    # Internal bulk‐create for seeding
    path(
      'internal/diagnoses/bulk_create/',
      bulk_create_diagnoses,
      name='bulk_create_diagnoses'
    ),
]
