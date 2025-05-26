from logic.logic_report import get_monthly_report

def fetch_report(period=None):
    cities = get_monthly_report(period)
    return [
        {
          "city": c.city,
          "doctors": [
            {
              "doctor_id": d.doctor_id,
              "doctor_name": d.doctor_name,
              "pct_efficiency": d.pct_efficiency,
              "cnt_pending": d.cnt_pending,
              "cnt_refractory": d.cnt_refractory
            }
            for d in c.doctors
          ]
        }
        for c in cities
    ]
