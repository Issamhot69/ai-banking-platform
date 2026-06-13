# 🏦 AI Banking Platform

Plateforme bancaire moderne — 8 Microservices FastAPI + Flutter + IA Claude + Infrastructure Cloud

## 🚀 Démarrage rapide
\`\`\`bash
docker-compose up -d
\`\`\`

## 📡 Services & Ports

| Service | Port | Tests | Description |
|---------|------|-------|-------------|
| Auth Service | 8001 | ✅ 14/14 | JWT, 2FA, KYC |
| Account Service | 8002 | ✅ 13/13 | Comptes IBAN |
| Transaction Service | 8003 | ✅ 14/14 | Virements, Fraude |
| Notification Service | 8006 | ✅ 17/17 | Push/Email/SMS |
| AI Service | 8007 | ✅ 20/20 | Claude AI, Credit Score |
| KYC Service | 8008 | 🆕 | Vérification identité |
| Audit Service | 8009 | 🆕 | Logs immuables |
| Card Service | 8010 | 🆕 | Cartes virtuelles Visa/Mastercard |
| API Gateway | 80 | | Nginx reverse proxy |
| PostgreSQL | 5435 | | Base de données |
| Redis | 6382 | | Cache & Sessions |
| MongoDB | 27018 | | Documents |
| Kafka | 29092 | | Events |
| Vault | 8200 | | Secrets |
| Prometheus | 9090 | | Métriques |
| Grafana | 3000 | | Monitoring |

**Total tests : 78/78 ✅**

## 🛠️ Stack technique

- **Backend** : FastAPI, SQLAlchemy (async), PostgreSQL, Redis, Kafka, MongoDB
- **IA** : Claude (Anthropic), TensorFlow, scikit-learn
- **Mobile** : Flutter (Riverpod, GoRouter)
- **Admin** : React + Recharts + Tailwind
- **Infra** : Docker, Kubernetes, Terraform (AWS EKS/RDS/ElastiCache)
- **Sécurité** : JWT + 2FA, HashiCorp Vault, AES-256, KYC
- **Monitoring** : Prometheus + Grafana + Node Exporter
- **CI/CD** : GitHub Actions → GHCR

## 🗺️ Roadmap

- [x] Étape 1 — Structure + Docker + DB
- [x] Étape 2 — Auth Service (JWT, 2FA, KYC)
- [x] Étape 3 — Account + Transaction Service
- [x] Étape 4 — Mobile Flutter UI
- [x] Étape 5 — AI Layer (Fraud, Credit Score, Chatbot)
- [x] Étape 6 — Notifications (Push/Email/SMS)
- [x] Étape 7 — Tests unitaires (78/78)
- [x] Étape 8 — Documentation API
- [x] Étape 9 — HashiCorp Vault
- [x] Étape 10 — Kubernetes + Terraform AWS
- [x] Étape 11 — Déploiement AWS EKS (testé + destroy)
- [x] Étape 12 — Admin Dashboard React
- [x] Étape 13 — KYC Service complet
- [x] Étape 14 — Audit Logs Service
- [x] Étape 15 — Cartes Virtuelles Visa/Mastercard
