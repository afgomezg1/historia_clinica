from django.core.management.base import BaseCommand
from django.conf import settings
from faker import Faker
from informacion_diagnostica.models import Diagnosis
import random
import requests
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = "Popula MongoDB con diagnósticos para los pacientes asignados en Postgres"

    def handle(self, *args, **options):
        fake = Faker()
        # 1) Obtener todos los patient_id desde el microservicio Médico
        url = settings.PATH_API_GATEWAY + "/personal-medico/internal/assignments/"
        # Sin filtros para obtener TODO el historial
        resp = requests.get(url)
        resp.raise_for_status()
        assignments = resp.json()  # lista de dicts con 'patient_id'
        patient_ids = {a['patient_id'] for a in assignments}

        # 2) Limpiar la colección y crear diagnósticos
        Diagnosis.drop_collection()
        now = datetime.utcnow()
        docs = []
        for pid in patient_ids:
            status = random.choice(["pending", "diagnosed"])
            diagnosed_at = None
            refractory = None
            if status == "diagnosed":
                # fecha aleatoria dentro de los últimos 12 meses
                days_offset = random.randint(0, 365)
                diagnosed_at = now - timedelta(days=days_offset)
                refractory = random.choice([True, False])
            docs.append(
                Diagnosis(
                    patient_id=pid,
                    status=status,
                    diagnosed_at=diagnosed_at,
                    refractory_epilepsy=refractory
                )
            )
        Diagnosis.objects.insert(docs, load_bulk=False)
        self.stdout.write(self.style.SUCCESS(
            f'Insertados {len(docs)} diagnósticos en MongoDB.'
        ))