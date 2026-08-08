// =================================================================
// NOTIFICATION MANAGER
// Handles Capacitor local notifications and feedback scheduling
// =================================================================

class NotificationManager {
    constructor() {
        this.isCapacitor = !!window.Capacitor;
        
        if (this.isCapacitor) {
            this.LocalNotifications = window.Capacitor.Plugins.LocalNotifications;
            this.setupListeners();
        }
    }

    async setupListeners() {
        if (!this.isCapacitor) return;
        
        try {
            await this.LocalNotifications.registerActionTypes({
                types: [
                    {
                        id: 'FEEDBACK_ACTIONS',
                        actions: [
                            { id: 'yes', title: '✅ Ate it' },
                            { id: 'no', title: '❌ Not Completed' },
                            { id: 'skipped', title: '⏭️ Skipped' }
                        ]
                    }
                ]
            });
        } catch(e) {
            console.warn("Could not register action types", e);
        }
        
        await this.LocalNotifications.addListener('localNotificationActionPerformed', (notificationAction) => {
            const data = notificationAction.notification.extra;
            const actionId = notificationAction.actionId;
            
            if (data && data.type === 'feedback') {
                if (window.feedbackManager) {
                    if (['yes', 'no', 'skipped'].includes(actionId)) {
                        window.feedbackManager.currentFeedbackData = data;
                        window.feedbackManager.submitFeedback(actionId);
                    } else {
                        window.feedbackManager.openFeedbackDialog(data.feedbackId, data);
                    }
                }
            }
        });
    }

    async requestPermission() {
        if (this.isCapacitor) {
            const { display } = await this.LocalNotifications.requestPermissions();
            return display === 'granted';
        } else if ("Notification" in window) {
            const permission = await Notification.requestPermission();
            return permission === "granted";
        }
        return false;
    }

    async schedulePlanNotifications(plan) {
        const hasPermission = await this.requestPermission();
        if (!hasPermission) return;

        // Cancel previous notifications for this plan if any
        await this.cancelPlanNotifications(plan.planId);

        const mealTimes = plan.notificationTimes || {};
        const registryKey = `nutriSmartNotificationRegistry_${plan.userId}`;
        let registry = JSON.parse(localStorage.getItem(registryKey)) || { planId: plan.planId, notificationIds: [] };
        
        if (registry.planId !== plan.planId) {
            registry = { planId: plan.planId, notificationIds: [] };
        }

        const scheduledNotifications = [];
        const today = new Date();
        const dateStr = today.toISOString().split('T')[0];

        // Ensure planData exists
        const planData = plan.planData || [];

        // Simple scheduling logic for today based on times
        Object.entries(mealTimes).forEach(([mealType, timeStr]) => {
            if (!timeStr) return;
            const [hours, minutes] = timeStr.split(':').map(Number);
            
            // Notification exactly at meal time
            let mealDate = new Date();
            mealDate.setHours(hours, minutes, 0, 0);

            if (mealDate.getTime() > Date.now()) {
                const mealNotifId = this.generateId(`${plan.userId}-${plan.planId}-${dateStr}-${mealType}-meal`);
                scheduledNotifications.push({
                    id: mealNotifId,
                    title: `${mealType.charAt(0).toUpperCase() + mealType.slice(1)} Reminder`,
                    body: `Your ${plan.planName} ${mealType} is ready. Open NutriSmart to view your meal.`,
                    schedule: { at: mealDate },
                    extra: {
                        type: 'meal',
                        planId: plan.planId,
                        mealType: mealType,
                        date: dateStr
                    }
                });

                registry.notificationIds.push({ id: mealNotifId, type: "meal", mealType, scheduledAt: mealDate.toISOString() });

                // Feedback notification EXACTLY 1 hour later
                let feedbackDate = new Date(mealDate.getTime() + 60 * 60 * 1000);
                const feedbackId = `${plan.planId}-${dateStr}-${mealType}-feedback`;
                const fbNotifId = this.generateId(`${plan.userId}-${feedbackId}`);

                // Find specific item name and calories if available
                let itemName = `${mealType} meal`;
                let calories = 0;
                let cost = 0;
                
                // Very basic extraction, can be enhanced
                if (Array.isArray(planData)) {
                    const mealItem = planData.find(item => item && (item.day_number === 1 || item.day === "Monday") && item.meal_type && item.meal_type.toLowerCase() === mealType.toLowerCase());
                    if (mealItem) {
                        itemName = mealItem.recipe_name || mealItem.meal_name || itemName;
                        calories = mealItem.calories || 0;
                        cost = mealItem.cost || 0;
                    }
                }

                scheduledNotifications.push({
                    id: fbNotifId,
                    title: `How was your ${mealType}?`,
                    body: `Did you complete the ${mealType} from your ${plan.planName}?`,
                    schedule: { at: feedbackDate },
                    actionTypeId: 'FEEDBACK_ACTIONS',
                    extra: {
                        type: 'feedback',
                        feedbackId: feedbackId,
                        planId: plan.planId,
                        planType: plan.planType,
                        planName: plan.planName,
                        mealType: mealType,
                        itemName: itemName,
                        calories: calories,
                        cost: cost,
                        date: dateStr,
                        notificationScheduledAt: mealDate.toISOString(),
                        feedbackScheduledAt: feedbackDate.toISOString()
                    }
                });

                registry.notificationIds.push({ id: fbNotifId, type: "feedback", mealType, scheduledAt: feedbackDate.toISOString() });
            }
        });

        if (this.isCapacitor && scheduledNotifications.length > 0) {
            await this.LocalNotifications.schedule({ notifications: scheduledNotifications });
        } else if (!this.isCapacitor && scheduledNotifications.length > 0) {
            console.log("Browser Mode: Scheduled following notifications:", scheduledNotifications);
            // Fallback for browser testing using setTimeout
            scheduledNotifications.forEach(n => {
                const delay = n.schedule.at.getTime() - Date.now();
                if (delay > 0) {
                    setTimeout(() => {
                        new Notification(n.title, { body: n.body });
                        if (n.extra.type === 'feedback' && window.feedbackManager) {
                            window.feedbackManager.openFeedbackDialog(n.extra.feedbackId, n.extra);
                        }
                    }, delay);
                }
            });
        }

        localStorage.setItem(registryKey, JSON.stringify(registry));
    }

    async cancelPlanNotifications(planId) {
        const email = localStorage.getItem("currentUserEmail") || "guest@example.com";
        const registryKey = `nutriSmartNotificationRegistry_${email}`;
        const registry = JSON.parse(localStorage.getItem(registryKey));

        if (registry && registry.planId === planId) {
            if (this.isCapacitor) {
                const ids = registry.notificationIds.map(n => ({ id: n.id }));
                if (ids.length > 0) {
                    await this.LocalNotifications.cancel({ notifications: ids });
                }
            }
            localStorage.removeItem(registryKey);
        }
    }

    generateId(str) {
        // Simple hash to integer
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash);
    }
}

window.notificationManager = new NotificationManager();
