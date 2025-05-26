from mongoengine import (
    Document, EmbeddedDocument,
    StringField, DateTimeField, BooleanField,
    FloatField, IntField, ListField, EmbeddedDocumentField
)

class Diagnosis(Document):
    patient_id          = StringField(primary_key=True, required=True)
    status              = StringField(
        choices=("pending", "diagnosed"), required=True
    )
    diagnosed_at        = DateTimeField()
    refractory_epilepsy = BooleanField()

    meta = {
        "collection": "diagnoses",
        "indexes": ["patient_id"],
    }

class DoctorMetrics(EmbeddedDocument):
    doctor_id      = StringField(required=True)
    doctor_name    = StringField(required=True)
    pct_efficiency = FloatField(required=True)
    cnt_pending    = IntField(required=True)
    cnt_refractory = IntField(required=True)

class CityMetrics(EmbeddedDocument):
    city    = StringField(required=True)
    doctors = ListField(EmbeddedDocumentField(DoctorMetrics))

class MonthlyReport(Document):
    period_start = DateTimeField(primary_key=True, required=True)
    cities       = ListField(EmbeddedDocumentField(CityMetrics))

    meta = {
        "collection": "monthly_reports",
        "indexes": ["period_start"],
    }
