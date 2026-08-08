# NutriSmart AI — Load Tests

This folder contains **Baseline / Load Testing** tools for the NutriSmart AI backend.

## 📁 Folder Structure

```
load-tests/
│
├── k6/
│   └── baseline-test.js       ← k6 test script (primary)
│
├── locust/
│   └── locustfile.py          ← Locust test script (Python, with Web UI)
│
├── results/                   ← Output folder (auto-created)
│   ├── baseline_stats.csv     ← Locust per-endpoint stats
│   ├── baseline_history.csv   ← Locust time-series data
│   ├── baseline_failures.csv  ← Locust failures
│   ├── k6-result.json         ← k6 raw output
│   └── Load_Test_Report.xlsx  ← Generated Excel report
│
└── generate_report.py         ← Converts Locust CSV → Excel report
```

---

## ⚙️ Test Configuration

| Parameter | Value |
|---|---|
| **Virtual Users** | 100 |
| **Duration** | 60 seconds |
| **Spawn Rate** | 10 users/second |
| **Ramp-up** | 10s (0 → 100 VUs) |
| **Sustained** | 45s (hold 100 VUs) |
| **Ramp-down** | 5s (100 → 0 VUs) |

---

## 📊 What You Will See

### Requests Per Second (RPS)
```
http_reqs .... 8400   140/s
```
> Your API is handling ~140 requests every second across 100 users.

### Response Time
```
http_req_duration ... avg=260ms  min=10ms   max=3000ms
                    p(90)=800ms  p(95)=1500ms
```
| Metric | Example | Meaning |
|---|---|---|
| `avg` | 260ms | Average time for all requests |
| `min` | 10ms | Fastest single request |
| `max` | 3000ms | Slowest single request |
| `p(90)` | 800ms | 90% of requests completed within |
| `p(95)` | 1500ms | 95% of requests completed within |

### Error Rate
```
error_rate .... 0.28%
```
> 0.28% of requests failed (mostly expected 401s on protected endpoints).

---

## 🚀 Option A — k6 (Recommended: Fast, No Browser Needed)

### 1. Install k6
```powershell
# Windows — using winget
winget install k6

# OR using Chocolatey
choco install k6
```

### 2. Run the Baseline Test
```powershell
# From the project root
k6 run load-tests/k6/baseline-test.js
```

### 3. Run with JSON Output
```powershell
k6 run --out json=load-tests/results/k6-result.json load-tests/k6/baseline-test.js
```

### Expected k6 Terminal Output
```
          /\      |‾‾| /‾‾/   /‾‾/   
     /\  /  \     |  |/  /   /  /    
    /  \/    \    |     (   /   ‾‾\  
   /          \   |  |\  \ |  (‾)  | 
  / __________ \  |__| \__\ \_____/ .io

  execution: local
     script: load-tests/k6/baseline-test.js
     output: -

  scenarios: (100.00%) 1 scenario, 100 max VUs, 1m30s max duration
           * default: Up to 100 looping VUs for 1m0s

     ✓ Homepage returns 200
     ✓ Login endpoint responds
     ✓ Recipe suggest responds

     checks.........................: 98.20%  ✓ 24550  ✗ 450
     data_received..................: 45 MB   750 kB/s
     data_sent......................: 3.2 MB  53 kB/s
     error_rate.....................: 0.28%   ✓ threshold
     http_req_blocked...............: avg=12ms   min=1ms    max=450ms
     http_req_duration..............: avg=260ms  min=10ms   max=3100ms
       { expected_response:true }...: avg=220ms  min=10ms   max=1800ms
     http_req_failed................: 0.28%   ✓ threshold
     http_reqs......................: 8400    140/s
     login_response_time............: avg=280ms  min=50ms   max=1500ms
     recipe_suggest_response_time...: avg=820ms  min=200ms  max=3000ms
     vus............................: 100     min=0      max=100
     vus_max........................: 100     min=100    max=100

     running (1m00.0s), 000/100 VUs, 8400 complete and 0 interrupted iterations
     default ✓ [======================================] 100 VUs  1m0s
```

---

## 🐍 Option B — Locust (Python, with Live Web Dashboard)

### 1. Install Locust
```powershell
pip install locust
```

### 2. Run with Web UI (Real-time Charts)
```powershell
locust -f load-tests/locust/locustfile.py --host=http://127.0.0.1:8000
```
Then open: **http://localhost:8089**

Enter:
- **Number of users**: `100`
- **Spawn rate**: `10`
- **Duration**: `1m`

Click **Start Swarming** and watch the live dashboard!

### 3. Run Headless (Terminal only, saves CSV)
```powershell
locust -f load-tests/locust/locustfile.py `
    --host=http://127.0.0.1:8000 `
    --users=100 `
    --spawn-rate=10 `
    --run-time=1m `
    --headless `
    --csv=load-tests/results/baseline
```

### 4. Generate Excel Report
```powershell
python load-tests/generate_report.py
```
Opens `load-tests/results/Load_Test_Report.xlsx` with 5 formatted sheets.

---

## ✅ SLA Thresholds (Pass/Fail Criteria)

| Threshold | Target | Description |
|---|---|---|
| `p(95)` all requests | < 2000ms | 95% of all requests under 2 seconds |
| `avg` all requests | < 500ms | Average response time under 500ms |
| Error rate | < 5% | Less than 5% of requests fail |
| Login `p(95)` | < 1500ms | Login endpoint 95th percentile |
| Recipe engine `p(95)` | < 3000ms | Recipe suggestion 95th percentile |

---

## 📈 Response Time Benchmarks

| Range | Experience |
|---|---|
| < 100ms | Instant |
| 100–300ms | Fast |
| 300–500ms | Acceptable |
| 500–1000ms | Slow |
| 1000–2000ms | Very Slow |
| > 2000ms | Unacceptable |
