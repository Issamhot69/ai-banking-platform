# 🏦 AI Banking Platform

Plateforme bancaire moderne — 13 Microservices FastAPI + Flutter + IA Claude + AWS

## 🚀 Démarrage rapide
```bash
docker-compose up -d
```

## 📡 Services & Tests

| Service | Port | Tests | Description |
|---------|------|-------|-------------|
| Auth Service | 8001 | ✅ 14/14 | JWT, 2FA |
| Account Service | 8002 | ✅ 13/13 | Comptes IBAN |
| Transaction Service | 8003 | ✅ 14/14 | Virements, Fraude |
| Notification Service | 8006 | ✅ 17/17 | Push/Email/SMS |
| AI Service | 8007 | ✅ 20/20 | Claude AI |
| KYC Service | 8008 | ✅ 8/8 | Vérification identité |
| Audit Service | 8009 | ✅ 9/9 | Logs immuables |
| Card Service | 8010 | ✅ 10/10 | Cartes Visa/Mastercard |
| SWIFT Service | 8011 | ✅ 9/9 | Virements MT103 |
| SEPA Service | 8012 | ✅ 8/8 | SCT + SCT Inst |
| Security Service | 8013 | ✅ 10/10 | Rate Limiting, DDoS |
| Loan Service | 8014 | ✅ 12/12 | Crédits/Prêts |
| Crypto Service | 8015 | ✅ 12/12 | BTC/ETH/SOL Wallet |

**Total : 156/156 tests ✅**

## 🗺️ Roadmap

- [x] Étapes 1-10 — Architecture, Docker, Tests, CI/CD
- [x] Étape 11 — AWS EKS Production
- [x] Étape 12 — Admin Dashboard React
- [x] Étapes 13-20 — 8 nouveaux microservices
- [x] Étape 21 — Tests tous services (156/156)
- [ ] Étape 22 — CI/CD mise à jour
- [ ] Étape 23 — Déploiement AWS final
