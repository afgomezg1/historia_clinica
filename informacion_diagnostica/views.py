import json
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_POST

from .models import Diagnosis
from .services.services_report import fetch_report

def monthly_report(request):
    # period comes in as “YYYY-MM-DD” or None
    period = request.GET.get("period")  
    data = fetch_report(period)
    return JsonResponse({"period": period, "cities": data}, safe=False)

@require_POST
def bulk_create_diagnoses(request):
    """
    POST /historia-clinica/internal/diagnoses/bulk_create/
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
