"""
predict_flight.py - Arquitetura de Previsão

Carrega o modelo treinado (prediction_model.joblib) e expõe uma classe simples
para prever custo, duração e CO2 de um ou vários voos.

Uso:
    from predict_flight import EcoFusionPredictor

    predictor = EcoFusionPredictor("prediction_model.joblib")

    resultado = predictor.predict_flight({
        "AIRLINE_CODE": "AA",
        "ORIGIN": "JFK",
        "DEST": "LAX",
        ...
    })
    # resultado = {"cost": 210.4, "duration": 312.1, "co2": 41832.0}

    resultados = predictor.predict_flights([voo1, voo2, voo3])
    # resultados = [{"cost":..., "duration":..., "co2":...}, ...]
"""

import joblib
import pandas as pd

# Colunas exigidas pelo modelo
REQUIRED_COLUMNS = [
    "AIRLINE_CODE", "ORIGIN", "DEST", "Season",
    "haversine_distance", "route_nonlinearity",
    "Month", "DayofWeek", "DayofMonth", "Quarter",
    "IsWeekend", "IsNightFlight",
    "CRS_ELAPSED_TIME", "DEP_HOUR", "Rolling_DEP_DELAY",
    "ORIGIN_LAT", "ORIGIN_LON", "DEST_LAT", "DEST_LON",
    "jet_fuel_price_usd", "carbon_price_usd",
    "load_factor_prev_month", "hist_route_price", "is_holiday",
    "temp_origin_c", "temp_dest_c",
    "precip_origin_mm", "precip_dest_mm",
    "wind_origin_kmh", "wind_dest_kmh",
    "extreme_temp_origin", "extreme_temp_dest",
    "heavy_rain_origin", "heavy_rain_dest",
    "strong_wind_origin", "strong_wind_dest",
]


class EcoFusionPredictor:
    """
    Previsão da arquitetura EcoFusion 

    Carrega o modelo uma única vez na criação do objeto e expõe métodos
    simples para prever custo (USD), duração (min) e CO2 (kg) de voos
    domésticos EUA.
    """

    def __init__(self, model_path: str = "prediction_model.joblib"):
        self.model_path = model_path
        self.model = joblib.load(model_path)

    def _validate(self, df: pd.DataFrame):
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Faltam {len(missing)} colunas obrigatórias no input: {missing}"
            )

    def predict_flight(self, flight_data: dict) -> dict:
        """
        Prevê custo, duração e CO2 para um único voo.

        Parameters
        ----------
        flight_data : dict
            Dicionário com todas as colunas listadas em REQUIRED_COLUMNS.

        Returns
        -------
        dict
            {"cost": float (USD), "duration": float (min), "co2": float (kg)}
        """
        df = pd.DataFrame([flight_data])
        self._validate(df)

        result = self.model.predict(df)

        return {
            "cost": float(result["cost"][0]),
            "duration": float(result["duration"][0]),
            "co2": float(result["co2"][0]),
        }

    def predict_flights(self, flights_data: list) -> list:
        """
        Prevê custo, duração e CO2 para vários voos de uma vez (mais eficiente
        que chamar predict_flight em loop, porque os modelos correm em batch).

        Parameters
        ----------
        flights_data : list[dict]
            Lista de dicionários, cada um com as colunas de REQUIRED_COLUMNS.

        Returns
        -------
        list[dict]
            Uma lista de dicts {"cost", "duration", "co2"}, na mesma ordem do input.
        """
        df = pd.DataFrame(flights_data)
        self._validate(df)

        result = self.model.predict(df)

        return [
            {
                "cost": float(result["cost"][i]),
                "duration": float(result["duration"][i]),
                "co2": float(result["co2"][i]),
            }
            for i in range(len(df))
        ]


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Uso: python predict_flight.py <ficheiro.json>")
        print("O ficheiro deve conter um dict (1 voo) ou uma lista de dicts (vários voos).")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    predictor = EcoFusionPredictor("prediction_model.joblib")

    if isinstance(data, list):
        resultado = predictor.predict_flights(data)
    else:
        resultado = predictor.predict_flight(data)

    print(json.dumps(resultado, indent=2, ensure_ascii=False))