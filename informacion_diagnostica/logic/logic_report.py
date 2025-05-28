from datetime import datetime
from django.utils import timezone
from informacion_diagnostica.models import MonthlyReport

def get_monthly_report(period=None):
    if period:
        period_start = datetime.fromisoformat(period)
    else:
        now = timezone.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    report = MonthlyReport.objects(period_start=period_start).first()
    return report.cities if report else []
