from django.urls import path
from .views import monthly_report

urlpatterns = [
    path("api/report/", monthly_report, name="monthly_report"),
]
