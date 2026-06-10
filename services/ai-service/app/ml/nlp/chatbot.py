from anthropic import AsyncAnthropic
from app.core.config import settings
from typing import Optional
import json
import re


SYSTEM_PROMPT = """Tu es un assistant bancaire intelligent et professionnel pour AI Banking Platform.

Tu aides les clients avec:
- Informations sur leurs comptes et soldes
- Conseils sur les transferts et paiements
- Explications sur les produits bancaires (épargne, crédits, cartes)
- Conseils financiers personnalisés
- Support pour les problèmes courants

Règles importantes:
- Réponds toujours en français (ou dans la langue du client)
- Ne jamais divulguer d'informations sensibles
- Redirige vers un conseiller humain pour les cas complexes
- Sois concis, clair et professionnel

Contexte client disponible: {context}
"""


class BankingChatbot:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    async def chat(self, message: str, conversation_history: list[dict], user_context: Optional[dict] = None) -> dict:
        context_str = json.dumps(user_context or {}, ensure_ascii=False)
        system = SYSTEM_PROMPT.format(context=context_str)

        messages = []
        for turn in conversation_history[-10:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": message})

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=messages,
        )

        return {
            "reply": response.content[0].text,
            "intent": self._detect_intent(message),
            "model": self.model,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
        }

    def _detect_intent(self, message: str) -> str:
        message_lower = message.lower()
        intents = {
            "balance_inquiry": ["solde", "balance", "combien", "argent"],
            "transfer": ["virement", "transfert", "envoyer", "payer"],
            "card_management": ["carte", "bloquer", "débloquer", "limite"],
            "loan_inquiry": ["prêt", "crédit", "emprunt", "financement"],
            "fraud_report": ["fraude", "vol", "suspect", "inconnu"],
            "account_info": ["compte", "iban", "numéro", "relevé"],
            "complaint": ["problème", "erreur", "plainte", "réclamation"],
        }
        for intent, keywords in intents.items():
            if any(kw in message_lower for kw in keywords):
                return intent
        return "general_inquiry"

    async def analyze_spending(self, transactions: list[dict]) -> dict:
        if not transactions:
            return {"insights": [], "summary": "Aucune transaction à analyser"}

        tx_summary = []
        for tx in transactions[:20]:
            tx_summary.append(f"- {tx.get('description', 'N/A')}: {tx.get('amount', 0)} {tx.get('currency', 'EUR')}")

        prompt = f"""Analyse ces transactions bancaires et donne des insights financiers concis:

{chr(10).join(tx_summary)}

Fournis:
1. Les catégories de dépenses principales
2. Les tendances remarquables
3. 2-3 conseils d'économies personnalisés
4. Un score de santé financière sur 100

Réponds en JSON avec les clés: categories, trends, tips, health_score"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass

        return {"raw_analysis": response.content[0].text}


chatbot = BankingChatbot()
