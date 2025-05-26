from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import requests
from informacion_diagnostica.models import Diagnosis, MonthlyReport, CityMetrics, DoctorMetrics

class Command(BaseCommand):
    help = "Genera o actualiza el reporte mensual precalculado en Mongo via API Rest microservicio Médico"

    def handle(self, *args, **options):
        # 1) Ventana de 3 meses
        now = timezone.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_window = period_start - timedelta(days=90)

        # 2) Consumir API interno de Médico a través de Kong
        url = settings.PATH_API_GATEWAY + "/personal-medico/internal/assignments/"
        params = {"start": start_window.isoformat(), "end": period_start.isoformat()}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        assigns = resp.json()  # [{'doctor_id','doctor_name','city','patient_id'}, ...]

        # 3) Agrupar por médico
        doctor_map = {}
        for a in assigns:
            did = str(a['doctor_id'])
            info = doctor_map.setdefault(did, {
                'doctor_name': a['doctor_name'],
                'city': a['city'],
                'patients': []
            })
            info['patients'].append(a['patient_id'])

        # 4) Leer diagnósticos de Mongo
        all_patient_ids = [pid for info in doctor_map.values() for pid in info['patients']]
        diags = {d.patient_id: d for d in Diagnosis.objects(patient_id__in=all_patient_ids)}

        # 5) Calcular métricas y bucket por ciudad
        city_buckets = {}
        for doc_id, info in doctor_map.items():
            pats = info['patients']
            total = len(pats)
            cnt_pending = cnt_diagnosed = cnt_refractory = 0
            for pid in pats:
                diag = diags.get(pid)
                if not diag or diag.status == 'pending':
                    cnt_pending += 1
                else:
                    cnt_diagnosed += 1
                    if diag.refractory_epilepsy:
                        cnt_refractory += 1
            pct_eff = (100 * cnt_diagnosed / total) if total else 0
            dm = DoctorMetrics(
                doctor_id=doc_id,
                doctor_name=info['doctor_name'],
                pct_efficiency=pct_eff,
                cnt_pending=cnt_pending,
                cnt_refractory=cnt_refractory
            )
            city_buckets.setdefault(info['city'], []).append(dm)

        # 6) Upsert en MonthlyReport
        cities_list = [CityMetrics(city=city, doctors=docs)
                       for city, docs in city_buckets.items()]
        MonthlyReport.objects.update_one(
            {'period_start': period_start},
            {'set__cities': cities_list},
            upsert=True
        )
        self.stdout.write(self.style.SUCCESS(
            f'Reporte para {period_start.date()} generado con {len(cities_list)} ciudades.'
        ))
