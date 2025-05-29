import json

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Diagnosis
from .services.services_report import fetch_report

def monthly_report(request):
    """
    Render the monthly report page, supplying:
      - periods: last 12 months as 'YYYY-MM-01'
      - period: selected period (default = most recent)
      - cities: report data for that period
    """
    now = timezone.now()

    # 1) Build last 12 period labels without external deps
    periods = []
    year, month = now.year, now.month
    for _ in range(12):
        periods.append(f"{year}-{month:02d}-01")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    periods.reverse()  # oldest first, newest last

    # 2) Determine the selected period
    sel = request.GET.get("period")
    period = sel if sel in periods else periods[-1]

    # 3) Fetch the report data
    cities = fetch_report(period)

    # 4) Render the template
    return render(
        request,
        'informacion_diagnostica/report.html',
        {
            "periods": periods,
            "period": period,
            "cities": cities,
        }
    )

@require_POST
@csrf_exempt
def bulk_create_diagnoses(request):
    """
    POST /historia-clinica/internal/diagnoses/bulk_create/
    Accepts a JSON list of Diagnosis fields and inserts them all.
    """
    try:
        payload = json.loads(request.body)
        # Validate payload is a list of dicts:
        if not isinstance(payload, list):
            return HttpResponseBadRequest("Expected a JSON list")
        docs = [ Diagnosis(**d) for d in payload ]
        Diagnosis.objects.insert(docs, load_bulk=False)
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    return JsonResponse({"inserted": len(docs)})
