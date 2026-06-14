# 🏦 AI Banking Platform

Plateforme bancaire moderne — 13 Microservices FastAPI + Flutter + IA Claude + Infrastructure Cloud

## 🚀 Démarrage rapide
```bash
docker-compose up -d
```

## 📡 Services & Ports

| Service | Port | Description |
|---------|------|-------------|
| Auth Service | 8001 | JWT, 2FA, KYC |
| Account Service | 8002 | Comptes IBAN |
| Transaction Service | 8003 | Virements locaux, Fraude |
| Notification Service | 8006 | Push/Email/SMS |
| AI Service | 8007 | Claude AI, Credit Score |
| KYC Service | 8008 | Vérification identité |
| Audit Service | 8009 | Logs immuables |
| Card Service | 8010 | Cartes Visa/Mastercard |
| SWIFT Service | 8011 | Virements internationaux MT103 |
| SEPA Service | 8012 | SCT + SCT Inst (37 pays) |
| Security Service | 8013 | Rate Limiting, IP Blocking |
| Loan Service | 8014 | Crédits/Prêts |
| Crypto Service | 8015 | BTC/ETH/SOL/BNB Wallet |

**Tests : 78/78 ✅ — 13 services UP ✅**

## 🗺️ Roadmap

- [x] Étape 1-10 — Architecture, Docker, Tests, CI/CD, AWS
- [x] Étape 11 — AWS EKS Production
- [x] Étape 12 — Admin Dashboard React
- [x] Étape 13 — KYC Service
- [x] Étape 14 — Audit Logs
- [x] Étape 15 — Cartes Virtuelles
- [x] Étape 16 — SWIFT (MT103)
- [x] Étape 17 — SEPA (SCT + SCT Inst)
- [x] Étape 18 — Security (Rate Limiting, IP Blocking)
- [x] Étape 19 — Loan Service (Crédits/Prêts)
- [x] Étape 20 — Crypto Wallet (BTC/ETH/SOL)
- [ ] Étape 21 — Tests nouveaux services
- [ ] Étape 22 — CI/CD mise à jour
- [ ] Étape 23 — Déploiement AWS final
