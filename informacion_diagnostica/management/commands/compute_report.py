from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import requests
from informacion_diagnostica.models import Diagnosis, MonthlyReport, CityMetrics, DoctorMetrics

class Command(BaseCommand):
    help = "Compute and upsert the 3-month MonthlyReport document in Mongo"

    def handle(self, *args, **options):
        # 1) define window
        now = timezone.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_window = period_start - timedelta(days=90)

        # 2) fetch assignments from Médico via Kong
        resp = requests.get(
            settings.PERSONAL_MEDICO_INTERNAL,
            params={
               "start": start_window.isoformat(),
               "end":   period_start.isoformat()
            },
            timeout=60
        )
        resp.raise_for_status()
        assigns = resp.json()  # list of {doctor_id, doctor_name, city, patient_id}

        # 3) aggregate by doctor
        doctor_map = {}
        for a in assigns:
            did = str(a["doctor_id"])
            info = doctor_map.setdefault(did, {
                "doctor_name": a["doctor_name"],
                "city":        a["city"],
                "patients":    []
            })
            info["patients"].append(a["patient_id"])

        # 4) load diagnoses in one query
        all_pids = [pid for v in doctor_map.values() for pid in v["patients"]]
        diags = {d.patient_id: d for d in Diagnosis.objects(patient_id__in=all_pids)}

        # 5) compute metrics, bucket by city
        city_buckets = {}
        for doc_id, info in doctor_map.items():
            pats = info["patients"]
            total = len(pats)
            cnt_pending = cnt_diag = cnt_refr = 0
            for pid in pats:
                d = diags.get(pid)
                if not d or d.status == "pending":
                    cnt_pending += 1
                else:
                    cnt_diag += 1
                    if d.refractory_epilepsy:
                        cnt_refr += 1
            pct = 100 * cnt_diag / total if total else 0
            dm = DoctorMetrics(
                doctor_id=doc_id,
                doctor_name=info["doctor_name"],
                pct_efficiency=pct,
                cnt_pending=cnt_pending,
                cnt_refractory=cnt_refr
            )
            city_buckets.setdefault(info["city"], []).append(dm)

        # 6) upsert the single MonthlyReport doc
        cities_list = [
            CityMetrics(city=cty, doctors=dlist)
            for cty, dlist in city_buckets.items()
        ]
        MonthlyReport.objects.update_one(
            {"period_start": period_start},
            {"set__cities": cities_list},
            upsert=True
        )
        self.stdout.write(self.style.SUCCESS(
            f"MonthlyReport for {period_start.date()} upserted ({len(cities_list)} cities)."
        ))
