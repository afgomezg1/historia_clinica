from django.http import JsonResponse
from django.conf import settings
from .services.services_report import fetch_report

def monthly_report(request):
    period = request.GET.get("period")
    data = fetch_report(period)
    return JsonResponse({"period": period, "cities": data}, safe=False)
