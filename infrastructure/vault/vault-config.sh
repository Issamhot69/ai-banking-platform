#!/bin/bash
# Script pour lire les secrets depuis Vault

export VAULT_ADDR='http://bank_vault:8200'
export VAULT_TOKEN='bank-root-token'

echo "🔐 Lecture des secrets depuis Vault..."

# Database
export POSTGRES_PASSWORD=$(vault kv get -field=postgres_password bank/database)
export REDIS_PASSWORD=$(vault kv get -field=redis_password bank/database)
export MONGO_PASSWORD=$(vault kv get -field=mongo_password bank/database)

# Security
export SECRET_KEY=$(vault kv get -field=secret_key bank/security)
export ENCRYPTION_KEY=$(vault kv get -field=encryption_key bank/security)

# External APIs
export ANTHROPIC_API_KEY=$(vault kv get -field=anthropic_api_key bank/external)
export SENDGRID_API_KEY=$(vault kv get -field=sendgrid_api_key bank/external)
export TWILIO_ACCOUNT_SID=$(vault kv get -field=twilio_account_sid bank/external)
export TWILIO_AUTH_TOKEN=$(vault kv get -field=twilio_auth_token bank/external)

echo "✅ Secrets chargés avec succès!"
