class RecommendationEngine:
    PRODUCTS = [
        {"id": "savings_plus", "name": "Compte Épargne Plus", "type": "savings", "rate": 3.5, "description": "Taux d'intérêt de 3.5% par an", "min_balance": 1000},
        {"id": "credit_card_gold", "name": "Carte Gold", "type": "credit_card", "cashback": 1.5, "description": "1.5% cashback sur tous vos achats", "annual_fee": 49},
        {"id": "personal_loan", "name": "Prêt Personnel", "type": "loan", "rate": 6.9, "description": "Prêt jusqu'à 50,000 EUR à 6.9%", "max_amount": 50000},
        {"id": "investment_fund", "name": "Fonds d'Investissement", "type": "investment", "expected_return": 7.2, "description": "Rendement moyen de 7.2% par an", "min_investment": 5000},
        {"id": "mortgage", "name": "Crédit Immobilier", "type": "mortgage", "rate": 4.2, "description": "Taux fixe 4.2% sur 20 ans", "max_amount": 500000},
        {"id": "travel_insurance", "name": "Assurance Voyage", "type": "insurance", "price": 9.99, "description": "Couverture mondiale complète"},
    ]

    def recommend(self, user_profile: dict) -> dict:
        recommendations = []
        balance = user_profile.get("avg_balance", 0)
        monthly_income = user_profile.get("monthly_income", 0)
        monthly_spend = user_profile.get("monthly_spend", 0)
        credit_score = user_profile.get("credit_score", 600)
        has_savings = user_profile.get("has_savings_account", False)
        top_categories = user_profile.get("top_spending_categories", [])
        age = user_profile.get("age", 30)

        for product in self.PRODUCTS:
            score = 0.0
            reasons = []
            pid = product["id"]

            if pid == "savings_plus" and balance > 2000 and not has_savings:
                score += 0.8
                reasons.append("Vous avez un solde élevé non optimisé")
            elif pid == "credit_card_gold" and ("shopping" in top_categories or "travel" in top_categories):
                score += 0.7
                reasons.append("Vos dépenses bénéficieraient du cashback")
            elif pid == "personal_loan" and credit_score >= 670 and monthly_income > 2000:
                score += 0.6
                reasons.append("Votre profil est éligible à un prêt avantageux")
            elif pid == "investment_fund" and balance > 10000 and age < 55:
                score += 0.75
                reasons.append("Votre épargne peut générer des rendements plus élevés")
            elif pid == "mortgage" and credit_score >= 700 and monthly_income > 3000 and age >= 25:
                score += 0.65
                reasons.append("Profil idéal pour un crédit immobilier")
            elif pid == "travel_insurance" and "travel" in top_categories:
                score += 0.8
                reasons.append("Vous voyagez souvent — protection recommandée")

            if score > 0.3:
                recommendations.append({**product, "relevance_score": round(score, 2), "reasons": reasons})

        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "user_segment": self._get_segment(user_profile),
            "total_recommendations": len(recommendations),
            "recommendations": recommendations[:4],
            "next_best_action": recommendations[0] if recommendations else None,
        }

    def _get_segment(self, profile: dict) -> str:
        income = profile.get("monthly_income", 0)
        balance = profile.get("avg_balance", 0)
        if income > 5000 or balance > 20000:
            return "premium"
        elif income > 2500 or balance > 5000:
            return "standard"
        return "starter"


recommendation_engine = RecommendationEngine()
