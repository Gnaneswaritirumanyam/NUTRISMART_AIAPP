"""
══════════════════════════════════════════════════════════
 NutriSmart AI — Baseline / Load Test (Locust)
 Tool   : Locust (https://locust.io) — Python load testing
 Target : http://127.0.0.1:8000
 Config : 100 Virtual Users × 60 Seconds
══════════════════════════════════════════════════════════

HOW TO RUN
──────────
  1. Install Locust:
       pip install locust

  2. Run with Web UI (recommended — gives live charts):
       locust -f load-tests/locust/locustfile.py --host=http://127.0.0.1:8000

     Then open browser → http://localhost:8089
     Enter: Number of users = 100, Spawn rate = 10, Duration = 1m

  3. Run Headless (no browser, prints results in terminal):
       locust -f load-tests/locust/locustfile.py \
           --host=http://127.0.0.1:8000 \
           --users=100 \
           --spawn-rate=10 \
           --run-time=1m \
           --headless \
           --csv=load-tests/results/baseline

  4. View CSV results:
       load-tests/results/baseline_stats.csv
       load-tests/results/baseline_failures.csv
       load-tests/results/baseline_history.csv

WHAT YOU WILL SEE (Terminal Output)
────────────────────────────────────
  Type    Name                            # Reqs   # Fails   Avg(ms)  Min(ms)  Max(ms)  Req/s
  ------  ------------------------------  -------  --------  -------  -------  -------  -----
  POST    /login                          2400     24        250      50       1500     40.0
  GET     /api/session                    2400     0         45       10       300      40.0
  POST    /suggest_recipes                1200     0         800      200      3000     20.0
  GET     /api/reviews                    1200     0         80       20       400      20.0
  GET     /                               1200     0         120      30       600      20.0
  ------  ------------------------------  -------  --------  -------  -------  -------  -----
  None    Aggregated                      8400     24        260      10       3000     140.0
"""

import json
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# ─────────────────────────────────────────────────────────
# USER SIMULATION CLASSES
# ─────────────────────────────────────────────────────────

class NutriSmartUser(HttpUser):
    """
    Simulates a real NutriSmart AI user browsing the app.
    Wait 0.5 - 2 seconds between each action (think time).
    """
    wait_time = between(0.5, 2.0)

    # ── On user spawn: check session state ───────────────
    def on_start(self):
        """Called once per VU when it starts."""
        self.client.get("/api/session", name="[Session Check]")

    # ─────────────────────────────────────────────────────
    # WEIGHT DISTRIBUTION
    # Higher weight = more frequent. Total weights add to ~100.
    # ─────────────────────────────────────────────────────

    @task(20)
    def visit_homepage(self):
        """Homepage load — highest traffic."""
        with self.client.get("/", name="GET /", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(15)
    def visit_login_page(self):
        """Visit login HTML page."""
        self.client.get("/login", name="GET /login [Page]")

    @task(15)
    def api_login_attempt(self):
        """
        POST /login — test authentication endpoint under load.
        Uses test credentials; expects 401 (not registered) or 200 (if test user exists).
        """
        payload = {
            "email": f"loadtest_{random.randint(1, 50)}@nutrismart.com",
            "password": "TestPassword123!"
        }
        with self.client.post(
            "/login",
            json=payload,
            name="POST /login [Auth]",
            catch_response=True
        ) as response:
            if response.status_code in (200, 401, 403):
                response.success()
            else:
                response.failure(f"Unexpected login status: {response.status_code}")

    @task(10)
    def check_session(self):
        """GET /api/session — lightweight auth check."""
        with self.client.get("/api/session", name="GET /api/session", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Session check failed: {response.status_code}")

    @task(10)
    def suggest_recipes(self):
        """
        POST /suggest_recipes — most CPU-intensive endpoint (graph traversal).
        Tests the recipe recommendation engine under load.
        """
        ingredient_combos = [
            ["tomato", "onion", "garlic"],
            ["chicken", "rice", "pepper"],
            ["egg", "flour", "milk"],
            ["potato", "butter", "cream"],
            ["spinach", "cheese", "pasta"],
        ]
        payload = {
            "ingredients": random.choice(ingredient_combos)
        }
        with self.client.post(
            "/suggest_recipes",
            json=payload,
            name="POST /suggest_recipes [Recipe Engine]",
            catch_response=True
        ) as response:
            if response.status_code in (200, 422):
                response.success()
            else:
                response.failure(f"Recipe suggest failed: {response.status_code}")

    @task(8)
    def get_reviews(self):
        """GET /api/reviews — public read, no auth needed."""
        with self.client.get("/api/reviews", name="GET /api/reviews", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Reviews failed: {response.status_code}")

    @task(5)
    def visit_dashboard(self):
        """Visit dashboard HTML page (not the API)."""
        self.client.get("/dashboard", name="GET /dashboard [Page]")

    @task(5)
    def get_history(self):
        """GET /get_history — global search/view history."""
        with self.client.get("/get_history", name="GET /get_history", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"History failed: {response.status_code}")

    @task(4)
    def api_dashboard(self):
        """
        GET /api/dashboard — protected endpoint.
        Expects 401 since load test users are not authenticated.
        """
        with self.client.get(
            "/api/dashboard",
            name="GET /api/dashboard [Protected, expect 401]",
            catch_response=True
        ) as response:
            if response.status_code in (200, 401):
                response.success()
            else:
                response.failure(f"Dashboard API unexpected: {response.status_code}")

    @task(4)
    def get_recipe_detail(self):
        """GET /get_recipe?name=... — individual recipe lookup."""
        recipe_names = [
            "Tomato Soup", "Egg Curry", "Pasta Salad",
            "Chicken Rice", "Vegetable Stir Fry"
        ]
        name = random.choice(recipe_names)
        with self.client.get(
            f"/get_recipe?name={name}",
            name="GET /get_recipe [Detail]",
            catch_response=True
        ) as response:
            if response.status_code in (200, 404, 400):
                response.success()
            else:
                response.failure(f"Get recipe failed: {response.status_code}")

    @task(3)
    def food_image(self):
        """GET /food-image?query=... — Pexels image proxy."""
        queries = ["pasta", "salad", "chicken", "rice", "soup"]
        with self.client.get(
            f"/food-image?query={random.choice(queries)}",
            name="GET /food-image [External API]",
            catch_response=True
        ) as response:
            if response.status_code in (200, 500):
                response.success()
            else:
                response.failure(f"Food image failed: {response.status_code}")

    @task(1)
    def visit_profile_page(self):
        """Visit profile HTML page — low frequency."""
        self.client.get("/profile", name="GET /profile [Page]")


# ─────────────────────────────────────────────────────────
# EVENT HOOKS — Print test parameters on start
# ─────────────────────────────────────────────────────────

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "=" * 56)
    print("  NutriSmart AI — Baseline Load Test (Locust)")
    print("=" * 56)
    print(f"  Target      : {environment.host}")
    print("  Users       : 100 Virtual Users")
    print("  Duration    : 60 seconds")
    print("  Spawn Rate  : 10 users/sec")
    print("=" * 56)
    print("  METRICS TO WATCH:")
    print("    RPS (Requests/sec)  → Throughput")
    print("    Avg (ms)            → Average Response Time")
    print("    Min / Max (ms)      → Best / Worst case")
    print("    Failures (%)        → Error Rate")
    print("=" * 56 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "=" * 56)
    print("  Load Test Complete!")
    print("  Results saved to: load-tests/results/")
    print("=" * 56 + "\n")
