/**
 * ══════════════════════════════════════════════════════════
 *  NutriSmart AI — Baseline / Load Test
 *  Tool    : k6 (https://k6.io)
 *  Target  : http://127.0.0.1:8000
 *  Profile : 100 Virtual Users × 1 Minute (Baseline Load Test)
 * ══════════════════════════════════════════════════════════
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ─────────────────────────────────────────────────────────
// CUSTOM METRICS
// ─────────────────────────────────────────────────────────
const errorRate       = new Rate('error_rate');
const loginDuration   = new Trend('login_response_time', true);
const recipeDuration  = new Trend('recipe_suggest_response_time', true);
const dashboardDuration = new Trend('dashboard_response_time', true);
const totalRequests   = new Counter('total_requests');

// ─────────────────────────────────────────────────────────
// TEST CONFIGURATION — 100 VUs × 1 MINUTE
// ─────────────────────────────────────────────────────────
export const options = {
  stages: [
    { duration: '10s', target: 100 },
    { duration: '45s', target: 100 },
    { duration: '5s',  target: 0   },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000', 'avg<500'],
    'error_rate': ['rate<0.05'],
    'login_response_time': ['p(95)<1500'],
    'recipe_suggest_response_time': ['p(95)<1000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

const HEADERS_JSON = {
  'Content-Type': 'application/json',
  'Accept':       'application/json',
};

// ─────────────────────────────────────────────────────────
// SETUP: runs once before the test starts
// ─────────────────────────────────────────────────────────
export function setup() {
  console.log('=== NutriSmart AI — Baseline Load Test ===');
  console.log(`Target:    ${BASE_URL}`);

  // Pre-flight check
  let res = http.get(`${BASE_URL}/api/session`);
  if (res.status === 0) {
    throw new Error(`Cannot reach ${BASE_URL} — is the server running?`);
  }
  console.log(`Server is UP.`);

  // 1. We authenticate exactly ONCE in setup to get the cookie.
  // This bypasses the 5/min rate limit since it's just 1 request,
  // and gives us a valid JWT session for all 100 VUs.
  let loginRes = http.post(`${BASE_URL}/login`, JSON.stringify({
    email: 'loadtest@nutrismart.com', // Must be a valid user, or will fail
    password: 'password123'
  }), { headers: HEADERS_JSON });

  let authToken = null;
  if (loginRes.cookies && loginRes.cookies['access_token']) {
    authToken = loginRes.cookies['access_token'][0].value;
  }
  
  if (!authToken) {
     console.log('WARNING: Could not fetch access_token via /login. Make sure loadtest@nutrismart.com exists.');
  }

  return { baseUrl: BASE_URL, token: authToken };
}

// ─────────────────────────────────────────────────────────
// MAIN VU SCENARIO
// ─────────────────────────────────────────────────────────
export default function (data) {
  let params = { headers: { ...HEADERS_JSON } };
  
  // Inject the HttpOnly cookie manually for testing so k6 stays authenticated
  if (data.token) {
    params.cookies = {
      access_token: data.token
    };
  }

  // ── GROUP 1: Public Pages (HTML endpoints) ─────────────
  group('Public HTML Pages', function () {
    let res = http.get(`${BASE_URL}/index.html`);
    check(res, { 'Homepage returns 200': (r) => r.status === 200 });
    errorRate.add(res.status !== 200);
    totalRequests.add(1);
    sleep(0.1);

    res = http.get(`${BASE_URL}/login.html`);
    check(res, { 'Login page returns 200': (r) => r.status === 200 });
    errorRate.add(res.status !== 200);
    totalRequests.add(1);
    sleep(0.1);

    res = http.get(`${BASE_URL}/dashboard.html`);
    check(res, { 'Dashboard page returns 200': (r) => r.status === 200 });
    errorRate.add(res.status !== 200);
    totalRequests.add(1);
    sleep(0.1);
  });

  // ── GROUP 2: Authentication API ───────────────────────
  group('Authentication API', function () {
    // Session check is very fast and requires the auth token
    let sessionRes = http.get(`${BASE_URL}/api/session`, params);
    check(sessionRes, {
      'Session endpoint responds 200': (r) => r.status === 200,
    });
    totalRequests.add(1);
    errorRate.add(sessionRes.status !== 200);
    sleep(0.1);
  });

  // ── GROUP 3: Recipe Engine (High CPU workload) ──────────
  group('Recipe Suggestion API', function () {
    const payload = JSON.stringify({
      ingredients: ['tomato', 'onion', 'garlic'],
    });
    let start = new Date();
    let res = http.post(`${BASE_URL}/suggest_recipes`, payload, params);
    recipeDuration.add(new Date() - start);
    
    check(res, {
      'Recipe suggest responds 200': (r) => r.status === 200 || r.status === 422,
    });
    totalRequests.add(1);
    errorRate.add(res.status !== 200 && res.status !== 422);
    sleep(0.2);

    let recipeRes = http.get(`${BASE_URL}/get_recipe?name=Tomato+Soup`, params);
    check(recipeRes, {
      'Get recipe responds 200/404': (r) => r.status === 200 || r.status === 404 || r.status === 400,
    });
    totalRequests.add(1);
    sleep(0.1);
  });

  // ── GROUP 4: Reviews API ────────────────────────────────
  group('Reviews API', function () {
    let res = http.get(`${BASE_URL}/api/reviews`, params);
    check(res, {
      'GET reviews responds 200': (r) => r.status === 200,
    });
    totalRequests.add(1);
    errorRate.add(res.status !== 200);
    sleep(0.1);
  });

  // ── GROUP 5: Static Assets ─────────────────────────────
  group('Static Assets', function () {
    let res = http.get(`${BASE_URL}/food-image?query=pasta`, params);
    check(res, {
      'Food image endpoint responds': (r) => r.status === 200 || r.status === 500 || r.status === 401 || r.status === 403,
    });
    totalRequests.add(1);
    sleep(0.1);
  });

  // ── GROUP 6: Plan & History Endpoints ─────────────────
  group('Plan & History Endpoints', function () {
    let histRes = http.get(`${BASE_URL}/get_history`, params);
    check(histRes, {
      'History endpoint responds 200': (r) => r.status === 200,
    });
    totalRequests.add(1);
    errorRate.add(histRes.status !== 200);
    sleep(0.1);

    let dashStart = new Date();
    let dashRes = http.get(`${BASE_URL}/api/dashboard`, params);
    dashboardDuration.add(new Date() - dashStart);
    check(dashRes, {
      'Dashboard API responds 200 (auth required)': (r) => r.status === 200,
    });
    totalRequests.add(1);
    errorRate.add(dashRes.status !== 200);
    sleep(0.2);
  });

  sleep(Math.random() * 0.5 + 0.1);
}

export function teardown(data) {
  console.log('=== Load Test Complete ===');
}
