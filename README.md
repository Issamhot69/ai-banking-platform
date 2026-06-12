# 🏦 AI Banking Platform

Plateforme bancaire moderne — Microservices FastAPI + Flutter + IA Claude + Infrastructure Cloud

## 🚀 Démarrage rapide
```bash
docker-compose up -d
```

## 📡 Services & Ports

| Service | Port | Tests |
|---------|------|-------|
| API Gateway | 80 | |
| Auth Service | 8001 | ✅ 14/14 |
| Account Service | 8002 | ✅ 13/13 |
| Transaction Service | 8003 | ✅ 14/14 |
| AI Service | 8007 | ✅ 20/20 |
| Notification Service | 8006 | ✅ 17/17 |
| PostgreSQL | 5435 | |
| Redis | 6382 | |
| MongoDB | 27017 | |
| Kafka | 29092 | |
| Prometheus | 9090 | |
| Grafana | 3000 | |
| Vault | 8200 | |

**Total : 78/78 tests passent ✅**

## 🛠️ Stack technique

- **Backend** : FastAPI, SQLAlchemy (async), PostgreSQL, Redis, Kafka, MongoDB
- **IA** : Claude (Anthropic), TensorFlow, scikit-learn
- **Mobile** : Flutter (Riverpod, GoRouter)
- **Infra** : Docker, Kubernetes, Terraform (AWS EKS/RDS/ElastiCache)
- **Sécurité** : JWT + 2FA, HashiCorp Vault, AES-256 encryption
- **Monitoring** : Prometheus + Grafana + Node Exporter
- **CI/CD** : GitHub Actions

## 📖 Documentation

- API : [docs/api/README.md](docs/api/README.md)
- Postman : [docs/postman/collection.json](docs/postman/collection.json)
- OpenAPI : [docs/swagger/openapi.yaml](docs/swagger/openapi.yaml)

## 🗺️ Roadmap

- [x] Étape 1 — Structure + Docker + DB
- [x] Étape 2 — Auth Service (JWT, 2FA, KYC)
- [x] Étape 3 — Account + Transaction Service
- [x] Étape 4 — Mobile Flutter UI
- [x] Étape 5 — AI Layer (Fraud, Credit Score, Recommandations, Chatbot)
- [x] Étape 6 — Notifications (Push/Email/SMS)
- [x] Étape 7 — Tests unitaires (78/78)
- [x] Étape 8 — Documentation API
- [x] Étape 9 — HashiCorp Vault
- [x] Étape 10 — Kubernetes + Terraform AWS
- [ ] Étape 11 — Déploiement AWS production
