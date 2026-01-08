import csv
import requests

API_URL = "http://localhost:8000"
CSV_PATH = "alimentos.csv"

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=1):
        # Normaliza números
        row["kcal_100g"] = float(row["kcal_100g"])
        row["proteina_100g"] = float(row["proteina_100g"])
        row["hidratos_100g"] = float(row["hidratos_100g"])
        row["grasas_100g"] = float(row["grasas_100g"])

        # Enviar a API
        resp = requests.post(f"{API_URL}/alimentos", json=row)
        if resp.status_code != 200:
            print(f"❌ Error en fila {i}: {resp.text}")
        else:
            print(f"✅ Fila {i} importada")

print("Importación finalizada.")
