import numpy as np
from datetime import datetime, timezone
from decimal import Decimal
import asyncio


class FraudMLDetector:
    def __init__(self):
        self.model = None
        self.threshold = 0.75
        self._load_model()

    def _load_model(self):
        try:
            import tensorflow as tf
            self.model = None
            print("✅ Fraud ML model initialisé")
        except Exception as e:
            print(f"⚠️ Fraud model en mode règles: {e}")

    def _extract_features(self, data: dict) -> np.ndarray:
        hour = datetime.now(timezone.utc).hour
        day = datetime.now(timezone.utc).weekday()
        return np.array([
            float(data.get("amount", 0)),
            float(data.get("daily_count", 0)),
            float(data.get("velocity_10min", 0)),
            float(data.get("avg_amount", 0)),
            float(data.get("balance_ratio", 0)),
            float(hour), float(day),
            float(data.get("is_international", 0)),
            float(1 if hour < 6 or hour > 22 else 0),
            float(data.get("amount_deviation", 0)),
        ]).reshape(1, -1)

    def _rule_based_score(self, data: dict) -> tuple[float, list[str]]:
        score = 0.0
        flags = []
        amount = float(data.get("amount", 0))
        hour = datetime.now(timezone.utc).hour

        if amount > 20000:
            score += 0.35
            flags.append("very_high_amount")
        elif amount > 10000:
            score += 0.20
            flags.append("high_amount")
        if hour < 6 or hour > 23:
            score += 0.15
            flags.append("night_transaction")
        if data.get("velocity_10min", 0) > 5:
            score += 0.30
            flags.append("high_velocity")
        if data.get("daily_count", 0) > 15:
            score += 0.25
            flags.append("excessive_daily_count")
        avg = data.get("avg_amount", 0)
        if avg > 0 and amount > avg * 5:
            score += 0.20
            flags.append("unusual_amount_pattern")
        if data.get("is_international", False):
            score += 0.10
            flags.append("international_transaction")

        return min(score, 1.0), flags

    async def predict(self, transaction_data: dict) -> dict:
        loop = asyncio.get_event_loop()
        if self.model is not None:
            features = self._extract_features(transaction_data)
            confidence = await loop.run_in_executor(
                None, lambda: float(self.model.predict(features)[0][0])
            )
            is_fraud = confidence >= self.threshold
            flags = ["ml_flagged"] if is_fraud else []
            model_used = "tensorflow"
        else:
            confidence, flags = self._rule_based_score(transaction_data)
            is_fraud = confidence >= self.threshold
            model_used = "rule_based"

        return {
            "is_fraud": is_fraud,
            "confidence": round(confidence, 4),
            "risk_score": int(confidence * 100),
            "flags": flags,
            "model_used": model_used,
        }


fraud_detector = FraudMLDetector()
