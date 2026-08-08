"""
══════════════════════════════════════════════════════════
 NutriSmart AI — Baseline / Load Test (Locust)
 Tool   : Locust (https://locust.io) — Python load testing
 Target : http://127.0.0.1:8000
 Config : 100 Virtual Users × 60 Seconds
══════════════════════════════════════════════════════════
"""

import json
import random
import os
import subprocess
from locust import HttpUser, task, between, events

import sys

# ─────────────────────────────────────────────────────────
# PRE-GENERATE AUTH TOKEN TO BYPASS RATE LIMITING
# ─────────────────────────────────────────────────────────
TOKEN = None
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gen_script = os.path.join(os.path.dirname(script_dir), "generate_test_token.py")
    TOKEN = subprocess.check_output([sys.executable, gen_script]).decode().strip()
    print(f"Generated test token successfully.")
except Exception as e:
    print(f"Warning: Could not generate test token. {e}")
    TOKEN = "fake_token"


class NutriSmartUser(HttpUser):
    """
    Simulates a real NutriSmart AI user browsing the app.
    Wait 0.5 - 2 seconds between each action (think time).
    """
    wait_time = between(0.5, 2.0)

    def on_start(self):
        """Called once per VU when it starts."""
        if TOKEN:
            self.client.cookies.set("access_token", TOKEN)
        
        # Health check
        with self.client.get("/api/session", name="[Setup] Session Check", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Backend unreachable or auth failed: {response.status_code}")

    # ─────────────────────────────────────────────────────
    # WEIGHT DISTRIBUTION
    # ─────────────────────────────────────────────────────

    @task(20)
    def visit_homepage(self):
        with self.client.get("/index.html", name="GET /index.html", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def visit_login_page(self):
        with self.client.get("/login.html", name="GET /login.html", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(10)
    def check_session(self):
        with self.client.get("/api/session", name="GET /api/session", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Session check failed: {response.status_code}")

    @task(10)
    def suggest_recipes(self):
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
        with self.client.get("/api/reviews", name="GET /api/reviews", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Reviews failed: {response.status_code}")

    @task(5)
    def visit_dashboard(self):
        with self.client.get("/dashboard.html", name="GET /dashboard.html", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def get_history(self):
        with self.client.get("/get_history", name="GET /get_history", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"History failed: {response.status_code}")

    @task(4)
    def api_dashboard(self):
        with self.client.get(
            "/api/dashboard",
            name="GET /api/dashboard [Protected]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard API unexpected: {response.status_code}")

    @task(4)
    def get_recipe_detail(self):
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
        queries = ["pasta", "salad", "chicken", "rice", "soup"]
        with self.client.get(
            f"/food-image?query={random.choice(queries)}",
            name="GET /food-image [External API]",
            catch_response=True
        ) as response:
            if response.status_code in (200, 500, 401, 403):
                response.success()
            else:
                response.failure(f"Food image failed: {response.status_code}")

    @task(1)
    def visit_profile_page(self):
        with self.client.get("/profile.html", name="GET /profile.html", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "=" * 56)
    print("  NutriSmart AI — Baseline Load Test (Locust)")
    print("=" * 56)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "=" * 56)
    print("  Load Test Complete!")
    print("=" * 56 + "\n")
