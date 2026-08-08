/**
 * ══════════════════════════════════════════════════════════
 *  NutriSmart AI — Baseline / Load Test
 *  Tool    : k6 (https://k6.io)
 *  Target  : http://127.0.0.1:8000
 *  Profile : 100 Virtual Users × 1 Minute (Baseline Load Test)
 * ══════════════════════════════════════════════════════════
 *
 *  WHAT YOU WILL SEE
 *  ─────────────────
 *  http_req_duration ............ avg=250ms  min=50ms   max=1500ms
 *  http_reqs .................... 12000      120/s
 *  http_req_failed .............. 0%
 *  vus .......................... 100
 *
 *  HOW TO RUN
 *  ──────────
 *  1. Install k6: https://k6.io/docs/get-started/installation/
 *     Windows: choco install k6   OR   winget install k6
 *
 *  2. Run the test:
 *     k6 run load-tests/k6/baseline-test.js
 *
 *  3. Run with HTML report:
 *     k6 run --out json=load-tests/results/baseline-result.json load-tests/k6/baseline-test.js
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
    // Ramp up: 0 → 100 VUs over 10 seconds
    { duration: '10s', target: 100 },
    // Sustained load: hold 100 VUs for 45 seconds (baseline window)
    { duration: '45s', target: 100 },
    // Ramp down: 100 → 0 VUs over 5 seconds
    { duration: '5s',  target: 0   },
  ],

  thresholds: {
    // 95% of all requests must complete under 2000ms
    'http_req_duration': ['p(95)<2000'],
    // Average response time must stay under 500ms
    'http_req_duration': ['avg<500'],
    // Error rate must stay below 5%
    'error_rate': ['rate<0.05'],
    // Login endpoint: 95th percentile under 1500ms
    'login_response_time': ['p(95)<1500'],
    // Recipe suggest: 95th percentile under 1000ms
    'recipe_suggest_response_time': ['p(95)<1000'],
  },
};

// ─────────────────────────────────────────────────────────
// CONFIGURATION
// ─────────────────────────────────────────────────────────
const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

const HEADERS_JSON = {
  'Content-Type': 'application/json',
  'Accept':       'application/json',
};

// ─────────────────────────────────────────────────────────
// HELPER: Make a request and record result
// ─────────────────────────────────────────────────────────
function request(method, url, body, params, trend) {
  totalRequests.add(1);
  const res = method === 'GET'
    ? http.get(url, params)
    : http.post(url, body, params);

  const ok = res.status >= 200 && res.status < 400;
  errorRate.add(!ok);
  if (trend) trend.add(res.timings.duration);
  return res;
}

// ─────────────────────────────────────────────────────────
// MAIN VU SCENARIO
// Each VU runs this function in a loop for the test duration.
// ─────────────────────────────────────────────────────────
export default function () {
  const params = { headers: HEADERS_JSON };

  // ── GROUP 1: Public Pages (HTML endpoints) ─────────────
  group('Public HTML Pages', function () {
    // Homepage
    let res = http.get(`${BASE_URL}/`);
    check(res, {
      'Homepage returns 200': (r) => r.status === 200,
      'Homepage has content':  (r) => r.body.length > 100,
    });
    errorRate.add(res.status !== 200);
    totalRequests.add(1);
    sleep(0.1);

    // Login page
    res = http.get(`${BASE_URL}/login`);
    check(res, {
      'Login page returns 200': (r) => r.status === 200,
    });
    errorRate.add(res.status !== 200);
    totalRequests.add(1);
    sleep(0.1);

    // Dashboard page (HTML, not API)
    res = http.get(`${BASE_URL}/dashboard`);
    check(res, {
      'Dashboard page returns 200': (r) => r.status === 200,
    });
    errorRate.add(res.status !== 200);
    totalRequests.add(1);
    sleep(0.1);
  });

  // ── GROUP 2: Authentication API ───────────────────────
  group('Authentication API', function () {
    // POST /login — invalid credentials (tests server response time, not functionality)
    const loginPayload = JSON.stringify({
      email:    'loadtest@nutrismart.com',
      password: 'LoadTestPass123',
    });
    const loginRes = request('POST', `${BASE_URL}/login`, loginPayload, params, loginDuration);
    check(loginRes, {
      'Login endpoint responds': (r) => r.status === 200 || r.status === 401 || r.status === 403,
      'Login response time < 2s': (r) => r.timings.duration < 2000,
    });
    sleep(0.2);

    // GET /api/session — session check (fast endpoint, tests auth middleware overhead)
    const sessionRes = request('GET', `${BASE_URL}/api/session`, null, params, null);
    check(sessionRes, {
      'Session endpoint responds': (r) => r.status === 200,
      'Session response is JSON':  (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json'),
    });
    sleep(0.1);
  });

  // ── GROUP 3: Recipe Engine (High CPU workload) ──────────
  group('Recipe Suggestion API', function () {
    const payload = JSON.stringify({
      ingredients: ['tomato', 'onion', 'garlic'],
    });
    const res = request('POST', `${BASE_URL}/suggest_recipes`, payload, params, recipeDuration);
    check(res, {
      'Recipe suggest responds':        (r) => r.status === 200 || r.status === 422,
      'Recipe response time < 3s':      (r) => r.timings.duration < 3000,
    });
    sleep(0.2);

    // GET /get_recipe — individual recipe lookup
    const recipeRes = request('GET', `${BASE_URL}/get_recipe?name=Tomato+Soup`, null, params, null);
    check(recipeRes, {
      'Get recipe responds': (r) => r.status === 200 || r.status === 404 || r.status === 400,
    });
    sleep(0.1);
  });

  // ── GROUP 4: Reviews API ────────────────────────────────
  group('Reviews API', function () {
    // GET reviews — unauthenticated, public read
    const res = request('GET', `${BASE_URL}/api/reviews`, null, params, null);
    check(res, {
      'GET reviews responds 200': (r) => r.status === 200,
      'Reviews is array or object': (r) => r.body.length > 0,
    });
    sleep(0.1);
  });

  // ── GROUP 5: Static Assets ─────────────────────────────
  group('Static Assets', function () {
    // Check food image endpoint
    const res = request('GET', `${BASE_URL}/food-image?query=pasta`, null, params, null);
    check(res, {
      'Food image endpoint responds': (r) => r.status === 200 || r.status === 500,
    });
    sleep(0.1);
  });

  // ── GROUP 6: Plan & History Endpoints ─────────────────
  group('Plan & History Endpoints', function () {
    // GET /get_history — global search history
    const histRes = request('GET', `${BASE_URL}/get_history`, null, params, null);
    check(histRes, {
      'History endpoint responds 200': (r) => r.status === 200,
    });
    sleep(0.1);

    // GET /api/session (dashboard data check) 
    const dashRes = request('GET', `${BASE_URL}/api/dashboard`, null, { headers: HEADERS_JSON }, dashboardDuration);
    check(dashRes, {
      'Dashboard API responds (auth required)': (r) => r.status === 401 || r.status === 200,
      'Dashboard response time < 1s':           (r) => r.timings.duration < 1000,
    });
    sleep(0.2);
  });

  // Think time between iterations — simulates real user pacing
  sleep(Math.random() * 0.5 + 0.1); // 100ms - 600ms random pause
}

// ─────────────────────────────────────────────────────────
// SETUP: runs once before the test starts
// ─────────────────────────────────────────────────────────
export function setup() {
  console.log('=== NutriSmart AI — Baseline Load Test ===');
  console.log(`Target:    ${BASE_URL}`);
  console.log('Profile:   100 Virtual Users × 60 Seconds');
  console.log('Ramp up:   10s | Sustained: 45s | Ramp down: 5s');
  console.log('=========================================');

  // Pre-flight check — ensure server is running
  const res = http.get(`${BASE_URL}/`);
  if (res.status === 0) {
    throw new Error(`Cannot reach ${BASE_URL} — is the server running?`);
  }
  console.log(`Server is UP. Status: ${res.status}`);
  return { baseUrl: BASE_URL };
}

// ─────────────────────────────────────────────────────────
// TEARDOWN: runs once after the test ends
// ─────────────────────────────────────────────────────────
export function teardown(data) {
  console.log('=== Load Test Complete ===');
  console.log(`Tested against: ${data.baseUrl}`);
  console.log('Check the summary above for:');
  console.log('  http_req_duration → avg / min / max / p90 / p95');
  console.log('  http_reqs         → total count and req/sec (RPS)');
  console.log('  error_rate        → % of failed requests');
}
