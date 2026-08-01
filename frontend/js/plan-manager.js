// =================================================================
// PLAN MANAGER
// Handles the single active plan state, migration, and UI locks
// =================================================================

const ACTIVE_PLAN_KEY = "nutriSmartActivePlan";

class PlanManager {
    constructor() {
        this.pageMapping = {
            "health": { page: "health.html", displayName: "Health Plan" },
            "loss": { page: "loss.html", displayName: "Weight Loss Plan" },
            "gain": { page: "gain.html", displayName: "Weight Gain Plan" },
            "fitness": { page: "fitness.html", displayName: "Fitness Plan" },
            "meal": { page: "meal.html", displayName: "Weekly Meal Plan" },
            "budget": { page: "budgetbased.html", displayName: "Budget Plan" }
        };
    }

    getCurrentUser() {
        return localStorage.getItem("currentUserEmail") || "guest@example.com";
    }

    getStorageKey() {
        const email = this.getCurrentUser();
        return `${ACTIVE_PLAN_KEY}_${email}`;
    }

    getActivePlan() {
        try {
            const data = localStorage.getItem(this.getStorageKey());
            if (data) {
                const plan = JSON.parse(data);
                if (plan && plan.status === "active") {
                    return plan;
                }
            }
        } catch (e) {
            console.error("Error reading active plan", e);
        }
        return null;
    }

    async activatePlan(planData) {
        planData.status = "active";
        planData.activatedAt = new Date().toISOString();
        localStorage.setItem(this.getStorageKey(), JSON.stringify(planData));

        try {
            await apiFetch("/api/active-plan/activate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(planData)
            });
        } catch (e) {
            console.warn("Could not sync active plan to backend (offline mode fallback)", e);
        }

        if (planData.notificationsEnabled && window.notificationManager) {
            await window.notificationManager.schedulePlanNotifications(planData);
        }
    }

    async requestPlanSwitch(newPlanType, newPlanData) {
        const activePlan = this.getActivePlan();
        
        if (activePlan && activePlan.planType !== newPlanType) {
            const oldPlanName = activePlan.planName || this.pageMapping[activePlan.planType].displayName;
            const newPlanName = this.pageMapping[newPlanType].displayName;
            
            const confirmSwitch = confirm(`${oldPlanName} is currently active. Activating ${newPlanName} will disable ${oldPlanName} notifications and cancel its pending reminders. Previous feedback will remain in analytics. Do you want to switch?`);
            
            if (!confirmSwitch) {
                return false;
            }

            if (window.notificationManager) {
                await window.notificationManager.cancelPlanNotifications(activePlan.planId);
            }
        }

        const dateStr = new Date().toISOString().split("T")[0];
        const planId = `${newPlanType}-${dateStr}-${Date.now()}`;
        
        const planObj = {
            userId: this.getCurrentUser(),
            planType: newPlanType,
            planName: this.pageMapping[newPlanType].displayName,
            sourcePage: this.pageMapping[newPlanType].page,
            planId: planId,
            activatedAt: new Date().toISOString(),
            notificationsEnabled: true,
            notificationTimes: newPlanData.notificationTimes || {
                "breakfast": "08:00",
                "lunch": "13:00",
                "evening": "17:00",
                "dinner": "20:00"
            },
            status: "active",
            planData: newPlanData.planData
        };

        await this.activatePlan(planObj);
        
        // Show a small non-intrusive toast or console instead of an alert that blocks the UI
        console.log(`${this.pageMapping[newPlanType].displayName} activated successfully.`);
        
        return true;
    }

    async disableActivePlan() {
        const activePlan = this.getActivePlan();
        if (!activePlan) return;

        const confirmDisable = confirm(`Disabling the ${activePlan.planName} will cancel all upcoming meal and feedback notifications. Previous feedback and analytics will be preserved. Do you want to continue?`);
        
        if (!confirmDisable) return;

        if (window.notificationManager) {
            await window.notificationManager.cancelPlanNotifications(activePlan.planId);
        }

        activePlan.status = "inactive";
        activePlan.notificationsEnabled = false;
        localStorage.setItem(this.getStorageKey(), JSON.stringify(activePlan));

        try {
            await apiFetch("/api/active-plan/disable", {
                method: "POST"
            });
        } catch (e) {
            console.warn("Could not sync disable to backend", e);
        }

        alert(`${activePlan.planName} has been disabled. All other plan features are now available.`);
        window.location.reload();
    }

    applyPlanPageState(currentPageType) {
        const activePlan = this.getActivePlan();
        if (!activePlan) return; // No active plan, all unlocked
        
        // If the active plan is THIS page, we don't lock it
        if (activePlan.planType === currentPageType) {
            return;
        }

        // Lock all inputs, selects, textareas, and generate buttons
        const elementsToDisable = document.querySelectorAll('input:not([id*="Time"]), select, textarea, button[id*="generate"]');
        elementsToDisable.forEach(el => {
            el.disabled = true;
            el.style.opacity = "0.5";
            el.style.cursor = "not-allowed";
        });

        // Inject banner warning above the generator
        const generatorPanel = document.querySelector('.panel.generator, .generator-container, .form-container');
        if (generatorPanel) {
            const oldPlanName = activePlan.planName || this.pageMapping[activePlan.planType].displayName;
            const banner = document.createElement('div');
            banner.innerHTML = `
                <div style="background: #fff3cd; color: #856404; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ffeeba; text-align: center;">
                    <strong>🔒 Form Locked</strong><br>
                    You currently have the <strong>${oldPlanName}</strong> active. Please disable notifications for that plan to generate a new one here.
                </div>
            `;
            generatorPanel.insertBefore(banner, generatorPanel.firstChild);
        }
    }

    migrateOldPlans() {
        if (this.getActivePlan()) return;
        const keysToCheck = ["healthPlan", "weightLossPlan", "weightGainPlan", "gymPlan", "weeklyMealPlan", "budgetPlan", "nutriSmartCurrentPlan"];
        let foundOld = false;
        keysToCheck.forEach(key => {
            if (localStorage.getItem(key)) foundOld = true;
        });
        if (foundOld) {
            console.log("Old plan data found. Awaiting user to activate a new centralized plan.");
        }
    }
}

window.planManager = new PlanManager();
document.addEventListener("DOMContentLoaded", () => {
    window.planManager.migrateOldPlans();
});
