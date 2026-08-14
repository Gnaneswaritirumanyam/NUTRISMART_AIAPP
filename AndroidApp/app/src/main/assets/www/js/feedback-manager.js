// =================================================================
// FEEDBACK MANAGER
// Handles user responses to meal notifications and syncs with backend
// =================================================================

class FeedbackManager {
    constructor() {
        this.injectFeedbackModal();
    }

    getCurrentUser() {
        return localStorage.getItem("currentUserEmail") || "guest@example.com";
    }

    getStorageKey() {
        const email = this.getCurrentUser();
        return `nutriSmartFeedback_${email}`;
    }

    injectFeedbackModal() {
        const modalHtml = `
        <div id="centralFeedbackModal" class="modal-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:9999; justify-content:center; align-items:center;">
            <div class="modal-box" style="background:#fffaf3; padding:25px; border-radius:20px; text-align:center; max-width:400px; width:90%;">
                <h3 style="color:#ff6f3c;">🍽️ Meal Feedback</h3>
                <p id="centralFeedbackText" style="color:#333; margin:15px 0;">Did you follow and complete this meal?</p>
                <div style="display:flex; flex-direction:column; gap:10px; margin-top:20px;">
                    <button class="btn btn-success" onclick="window.feedbackManager.submitFeedback('yes')" style="border-radius:15px; padding:10px;">✅ Yes, Completed</button>
                    <button class="btn btn-danger" onclick="window.feedbackManager.submitFeedback('no')" style="border-radius:15px; padding:10px;">❌ No, Not Completed</button>
                    <button class="btn btn-warning" onclick="window.feedbackManager.submitFeedback('skipped')" style="border-radius:15px; padding:10px; color:white;">⏭️ Skip</button>
                    <button class="btn btn-secondary" onclick="window.feedbackManager.submitFeedback('remind')" style="border-radius:15px; padding:10px;">⏰ Remind Me Later</button>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    openFeedbackDialog(feedbackId, extraData) {
        this.currentFeedbackData = extraData;
        const modal = document.getElementById("centralFeedbackModal");
        if (modal) {
            document.getElementById("centralFeedbackText").innerHTML = `
                <strong>${extraData.planName}</strong><br>
                ${extraData.mealType.charAt(0).toUpperCase() + extraData.mealType.slice(1)}: ${extraData.itemName}<br><br>
                Did you follow and complete this meal?
            `;
            modal.style.display = "flex";
        }
    }

    closeFeedbackDialog() {
        const modal = document.getElementById("centralFeedbackModal");
        if (modal) modal.style.display = "none";
        this.currentFeedbackData = null;
    }

    async submitFeedback(response) {
        if (!this.currentFeedbackData) return;
        const data = this.currentFeedbackData;

        // Ensure we haven't already answered this
        const existing = this.getFeedback(data.feedbackId);
        if (existing && existing.status !== "pending" && response !== 'remind') {
            alert("Feedback already recorded.");
            this.closeFeedbackDialog();
            return;
        }

        if (response === 'remind') {
            // Remind me later logic
            if (window.notificationManager) {
                // max 1 reminder
                const remindedKey = `reminded_${data.feedbackId}`;
                if (localStorage.getItem(remindedKey)) {
                    alert("Only one reminder allowed.");
                    return;
                }
                localStorage.setItem(remindedKey, "true");
                const remindDate = new Date(Date.now() + 30 * 60 * 1000); // 30 mins
                if (window.notificationManager.isCapacitor) {
                    const newId = window.notificationManager.generateId(`${data.feedbackId}_remind`);
                    window.notificationManager.LocalNotifications.schedule({
                        notifications: [{
                            id: newId,
                            title: `Reminder: How was your ${data.mealType}?`,
                            body: `Did you complete the ${data.mealType} from your ${data.planName}?`,
                            schedule: { at: remindDate },
                            extra: data
                        }]
                    });
                }
                alert("We will remind you in 30 minutes.");
            }
            this.closeFeedbackDialog();
            return;
        }

        // Map response to status
        let status = "pending";
        if (response === "yes") status = "completed";
        if (response === "no") status = "not_completed";
        if (response === "skipped") status = "skipped";

        const feedbackRecord = {
            feedbackId: data.feedbackId,
            planId: data.planId,
            planType: data.planType,
            planName: data.planName,
            date: data.date,
            mealType: data.mealType,
            itemName: data.itemName,
            notificationScheduledAt: data.notificationScheduledAt,
            feedbackScheduledAt: data.feedbackScheduledAt,
            feedbackAnsweredAt: new Date().toISOString(),
            status: status,
            response: response,
            calories: data.calories,
            cost: data.cost,
            sourcePage: window.location.pathname.split("/").pop(),
            syncStatus: "pending"
        };

        // Save locally
        let feedbacks = JSON.parse(localStorage.getItem(this.getStorageKey())) || [];
        feedbacks = feedbacks.filter(f => f.feedbackId !== data.feedbackId);
        feedbacks.push(feedbackRecord);
        localStorage.setItem(this.getStorageKey(), JSON.stringify(feedbacks));

        // Sync to backend
        try {
            await apiFetch("/api/plan-feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(feedbackRecord)
            });
            // Mark as synced
            feedbacks = JSON.parse(localStorage.getItem(this.getStorageKey())) || [];
            const idx = feedbacks.findIndex(f => f.feedbackId === data.feedbackId);
            if (idx > -1) {
                feedbacks[idx].syncStatus = "synced";
                localStorage.setItem(this.getStorageKey(), JSON.stringify(feedbacks));
            }
        } catch (e) {
            console.warn("Could not sync feedback to backend", e);
        }

        this.closeFeedbackDialog();
        alert("Feedback submitted successfully!");
    }

    getFeedback(feedbackId) {
        const feedbacks = JSON.parse(localStorage.getItem(this.getStorageKey())) || [];
        return feedbacks.find(f => f.feedbackId === feedbackId);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.feedbackManager = new FeedbackManager();
});
