import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '20s', target: 10 },
    { duration: '30s', target: 30 },
    { duration: '20s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

const AUTH_URL = __ENV.AUTH_URL || 'http://localhost:8001';
const ACCOUNT_URL = __ENV.ACCOUNT_URL || 'http://localhost:8002';
const TRANSACTION_URL = __ENV.TRANSACTION_URL || 'http://localhost:8003';

export function setup() {
  const email = `k6_${Date.now()}@bank.com`;
  const password = 'SecurePass123!';

  http.post(`${AUTH_URL}/api/v1/auth/register`, JSON.stringify({
    email, password, first_name: 'K6', last_name: 'Load',
  }), { headers: { 'Content-Type': 'application/json' } });

  const loginRes = http.post(`${AUTH_URL}/api/v1/auth/login`, JSON.stringify({
    email, password,
  }), { headers: { 'Content-Type': 'application/json' } });
  const token = loginRes.json('access_token');

  const accountRes = http.post(`${ACCOUNT_URL}/api/v1/accounts`, JSON.stringify({
    account_type: 'checking', currency: 'EUR',
  }), { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` } });
  const accountId = accountRes.json('id');

  return { token, accountId };
}

export default function (data) {
  const res = http.get(
    `${TRANSACTION_URL}/api/v1/transactions?account_id=${data.accountId}`,
    { headers: { Authorization: `Bearer ${data.token}` } }
  );
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(0.5);
}
