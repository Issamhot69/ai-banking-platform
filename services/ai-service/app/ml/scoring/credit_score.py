class CreditScorer:
    SCORE_RANGES = {
        (800, 850): ("Exceptionnel", "AAA", 0.02),
        (740, 799): ("Très bien", "AA", 0.04),
        (670, 739): ("Bien", "A", 0.07),
        (580, 669): ("Passable", "BBB", 0.12),
        (300, 579): ("Mauvais", "C", 0.20),
    }

    def calculate(self, user_data: dict) -> dict:
        base_score = 300
        base_score += int(user_data.get("payment_history_score", 0.8) * 192)
        credit_util = user_data.get("credit_utilization", 0.3)
        base_score += int(max(0, 1 - credit_util * 1.5) * 165)
        months_open = user_data.get("months_account_open", 12)
        base_score += int(min(1.0, months_open / 84) * 82)
        recent_inquiries = user_data.get("recent_inquiries", 0)
        base_score += int(max(0, 1 - recent_inquiries * 0.15) * 55)
        base_score += int(user_data.get("credit_mix_score", 0.5) * 55)

        final_score = min(850, max(300, base_score))
        label, grade, rate = self._get_category(final_score)
        monthly_income = user_data.get("monthly_income", 3000)

        return {
            "score": final_score,
            "label": label,
            "grade": grade,
            "interest_rate": rate,
            "max_loan_amount": self._calculate_max_loan(final_score, monthly_income),
            "factors": {
                "payment_history": round(user_data.get("payment_history_score", 0.8) * 100, 1),
                "credit_utilization": round(credit_util * 100, 1),
                "account_age_months": months_open,
                "recent_inquiries": recent_inquiries,
                "credit_mix": round(user_data.get("credit_mix_score", 0.5) * 100, 1),
            },
            "recommendations": self._get_recommendations(user_data, final_score),
        }

    def _get_category(self, score: int) -> tuple:
        for (low, high), vals in self.SCORE_RANGES.items():
            if low <= score <= high:
                return vals
        return "Inconnu", "N/A", 0.20

    def _calculate_max_loan(self, score: int, monthly_income: float) -> float:
        for score_range, mult in {range(800, 851): 60, range(740, 800): 48, range(670, 740): 36, range(580, 670): 24, range(300, 580): 12}.items():
            if score in score_range:
                return round(monthly_income * mult, 2)
        return 0.0

    def _get_recommendations(self, data: dict, score: int) -> list[str]:
        recs = []
        if data.get("credit_utilization", 0) > 0.3:
            recs.append("Réduire l'utilisation du crédit en dessous de 30%")
        if data.get("payment_history_score", 1) < 0.9:
            recs.append("Améliorer l'historique de paiement")
        if data.get("months_account_open", 0) < 24:
            recs.append("Maintenir vos comptes actifs pour améliorer l'ancienneté")
        if data.get("recent_inquiries", 0) > 3:
            recs.append("Éviter de nouvelles demandes de crédit pendant 6 mois")
        if score >= 740:
            recs.append("Excellent profil ! Vous êtes éligible aux meilleurs taux")
        return recs


credit_scorer = CreditScorer()
