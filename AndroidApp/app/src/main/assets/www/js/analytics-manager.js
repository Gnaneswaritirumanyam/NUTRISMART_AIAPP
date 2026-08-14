// =================================================================
// ANALYTICS MANAGER
// Calculates streaks, completion percentages, calories from real feedback
// =================================================================

const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 500,
    animation: false,
    animations: false,
    transitions: {
        active: {
            animation: {
                duration: 0
            }
        },
        resize: {
            animation: {
                duration: 0
            }
        }
    },
    devicePixelRatio: 1,
    interaction: {
        mode: "index",
        intersect: false
    },
    plugins: {
        legend: {
            display: true,
            position: "top",
            labels: {
                color: "#1e293b",
                boxWidth: window.innerWidth <= 480 ? 22 : 32,
                padding: 12,
                font: {
                    family: "Outfit",
                    size: window.innerWidth <= 480 ? 10 : 12
                }
            }
        }
    }
};

let weeklyCaloriesChartInstance = null;
let macronutrientChartInstance = null;
let notificationChartInstance = null;

function destroyChart(chartInstance) {
    if (chartInstance) {
        chartInstance.destroy();
    }
}

class AnalyticsManager {
    constructor() {
        this.feedbacks = [];
    }

    getCurrentUser() {
        return localStorage.getItem("currentUserEmail") || "guest@example.com";
    }

    async loadFeedback() {
        try {
            const res = await apiFetch("/api/plan-feedback");
            if (res.ok) {
                this.feedbacks = await res.json();
                // Merge local pending to be safe
                const local = JSON.parse(localStorage.getItem(`nutriSmartFeedback_${this.getCurrentUser()}`)) || [];
                local.forEach(l => {
                    if (!this.feedbacks.find(f => f.feedbackId === l.feedbackId)) {
                        this.feedbacks.push(l);
                    }
                });
            } else {
                throw new Error("API failed");
            }
        } catch (e) {
            console.warn("Using local storage for analytics");
            this.feedbacks = JSON.parse(localStorage.getItem(`nutriSmartFeedback_${this.getCurrentUser()}`)) || [];
        }
    }

    calculateAnalytics() {
        let completed = 0;
        let notCompleted = 0;
        let skipped = 0;
        let pending = 0;
        let caloriesCompleted = 0;

        let dateGroups = {};
        let mealGroups = { breakfast: { completed:0, total:0 }, lunch: { completed:0, total:0 }, evening: { completed:0, total:0 }, dinner: { completed:0, total:0 } };

        this.feedbacks.forEach(f => {
            if (!dateGroups[f.date]) {
                dateGroups[f.date] = { completed: 0, not_completed: 0, actionable: 0 };
            }

            if (f.status === "completed") {
                completed++;
                caloriesCompleted += (f.calories || 0);
                dateGroups[f.date].completed++;
                dateGroups[f.date].actionable++;
                if (mealGroups[f.mealType]) mealGroups[f.mealType].completed++;
            } else if (f.status === "not_completed") {
                notCompleted++;
                dateGroups[f.date].not_completed++;
                dateGroups[f.date].actionable++;
            } else if (f.status === "skipped") {
                skipped++;
            } else {
                pending++;
            }

            if (f.status !== "pending" && mealGroups[f.mealType]) {
                mealGroups[f.mealType].total++;
            }
        });

        const answeredActionable = completed + notCompleted;
        const completionPercentage = answeredActionable > 0 ? Math.round((completed / answeredActionable) * 100) : 0;

        // Calculate Streaks
        const sortedDates = Object.keys(dateGroups).sort((a,b) => new Date(a) - new Date(b));
        let currentStreak = 0;
        let bestStreak = 0;
        
        for (let date of sortedDates) {
            const day = dateGroups[date];
            if (day.actionable > 0 && day.completed === day.actionable) {
                currentStreak++;
                if (currentStreak > bestStreak) bestStreak = currentStreak;
            } else if (day.not_completed > 0) {
                currentStreak = 0;
            }
        }

        return {
            totalFeedbacks: this.feedbacks.length,
            completed,
            notCompleted,
            skipped,
            pending,
            caloriesCompleted,
            completionPercentage,
            currentStreak,
            bestStreak,
            dateGroups,
            mealGroups
        };
    }

    async renderNutriAnalytics() {
        await this.loadFeedback();
        const stats = this.calculateAnalytics();

        // Update basic DOM elements
        const caloriesEl = document.getElementById("caloriesValue");
        const adherenceEl = document.getElementById("adherenceValue");

        if (stats.totalFeedbacks === 0) {
            if (caloriesEl) caloriesEl.textContent = "0 kcal";
            if (adherenceEl) adherenceEl.textContent = "0%";
            // Do NOT return early. Render empty charts!
        } else {
            if (caloriesEl) caloriesEl.textContent = `${stats.caloriesCompleted} kcal`;
            if (adherenceEl) adherenceEl.textContent = `${stats.completionPercentage}%`;
        }

        // Create Charts
        if (window.Chart) {
            this.renderCharts(stats);
        }
    }

    renderCharts(stats) {
        // Prepare data for Weekly Calorie Chart
        const last7Days = [];
        for (let i = 6; i >= 0; i--) {
            let d = new Date();
            d.setDate(d.getDate() - i);
            last7Days.push(d.toISOString().split("T")[0]);
        }
        const weeklyDataPoints = last7Days.map(date => {
            const feedbacksOnDate = this.feedbacks.filter(f => f.date === date && f.status === "completed");
            return feedbacksOnDate.reduce((sum, f) => sum + (f.calories || 0), 0);
        });
        
        // Prepare data for Macro Pie Chart
        const hasData = stats.caloriesCompleted > 0;
        const carbs = hasData ? 50 : 0;
        const protein = hasData ? 30 : 0;
        const fat = hasData ? 20 : 0;

        // Render specific charts directly without timeouts
        this.renderWeeklyCaloriesChart(last7Days, weeklyDataPoints);
        this.renderMacronutrientChart(carbs, protein, fat);
        this.renderNotificationChart(stats.completed, stats.notCompleted, stats.skipped, stats.pending);
    }

    renderWeeklyCaloriesChart(labels, values) {
        const canvas = document.getElementById("calorieChart");
        if (!canvas) return;

        const existingChart = Chart.getChart(canvas);
        if (existingChart && existingChart !== weeklyCaloriesChartInstance) {
            existingChart.destroy();
        }

        const numericValues = values.map(value => Number(value) || 0);
        const hasData = numericValues.some(value => value > 0);

        if (weeklyCaloriesChartInstance) {
            weeklyCaloriesChartInstance.data.labels = labels;
            weeklyCaloriesChartInstance.data.datasets[0].data = numericValues;
            weeklyCaloriesChartInstance.options.scales.y.max = hasData ? undefined : 100;
            weeklyCaloriesChartInstance.options.scales.y.ticks.stepSize = hasData ? undefined : 20;
            weeklyCaloriesChartInstance.update("none");
        } else {
            weeklyCaloriesChartInstance = new Chart(canvas.getContext("2d"), {
                type: "line",
                data: {
                    labels,
                    datasets: [
                        {
                            label: "Calories Completed",
                            data: numericValues,
                            borderColor: "#ea580c",
                            backgroundColor: "rgba(234, 88, 12, 0.2)",
                            borderWidth: 3,
                            pointRadius: 4,
                            pointHoverRadius: 5,
                            tension: 0.3,
                            fill: true
                        }
                    ]
                },
                options: {
                    ...commonChartOptions,
                    scales: {
                        x: {
                            grid: {
                                display: true,
                                color: "rgba(0, 0, 0, 0.05)"
                            },
                            ticks: {
                                color: "#475569",
                                autoSkip: true,
                                maxTicksLimit: window.innerWidth <= 480 ? 4 : 7,
                                maxRotation: 0,
                                minRotation: 0,
                                font: {
                                    family: "Outfit",
                                    size: window.innerWidth <= 480 ? 9 : 12
                                }
                            }
                        },
                        y: {
                            grid: {
                                color: "rgba(0, 0, 0, 0.05)"
                            },
                            beginAtZero: true,
                            min: 0,
                            max: hasData ? undefined : 100,
                            ticks: {
                                color: "#475569",
                                stepSize: hasData ? undefined : 20,
                                precision: 0,
                                font: {
                                    family: "Outfit",
                                    size: window.innerWidth <= 480 ? 9 : 12
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    renderMacronutrientChart(carbs, protein, fat) {
        const canvas = document.getElementById("macroChart");
        if (!canvas) return;

        const existingChart = Chart.getChart(canvas);
        if (existingChart && existingChart !== macronutrientChartInstance) {
            existingChart.destroy();
        }

        const macroDisplayValues =
            carbs + protein + fat > 0
                ? [carbs, protein, fat]
                : [1];

        const macroDisplayLabels =
            carbs + protein + fat > 0
                ? [
                    `Carbs (${carbs}%)`,
                    `Protein (${protein}%)`,
                    `Fat (${fat}%)`
                  ]
                : ["No nutrition data"];

        if (macronutrientChartInstance) {
            macronutrientChartInstance.data.datasets[0].data = macroDisplayValues;
            macronutrientChartInstance.data.labels = macroDisplayLabels;
            macronutrientChartInstance.data.datasets[0].backgroundColor =
                carbs + protein + fat > 0
                    ? ["#ea580c", "#f97316", "#fb923c"]
                    : ["rgba(0, 0, 0, 0.05)"];
            macronutrientChartInstance.update("none");
        } else {
            macronutrientChartInstance = new Chart(canvas.getContext("2d"), {
                type: "doughnut",
                data: {
                    labels: macroDisplayLabels,
                    datasets: [
                        {
                            data: macroDisplayValues,
                            backgroundColor:
                                carbs + protein + fat > 0
                                    ? ["#ea580c", "#f97316", "#fb923c"]
                                    : ["rgba(0, 0, 0, 0.05)"],
                            borderWidth: 0,
                            hoverOffset: 4
                        }
                    ]
                },
                options: {
                    ...commonChartOptions,
                    cutout: "60%",
                    plugins: {
                        ...commonChartOptions.plugins,
                        legend: {
                            display: true,
                            position: "top",
                            labels: {
                                boxWidth: window.innerWidth <= 480 ? 18 : 28,
                                padding: 10,
                                font: {
                                    size: window.innerWidth <= 480 ? 9 : 12
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    renderNotificationChart(completed, missed, skipped, pending) {
        const canvas = document.getElementById("notificationChart");
        if (!canvas) return;

        const existingChart = Chart.getChart(canvas);
        if (existingChart && existingChart !== notificationChartInstance) {
            existingChart.destroy();
        }

        const values = [
            Number(completed) || 0,
            Number(missed) || 0,
            Number(skipped) || 0,
            Number(pending) || 0
        ];

        const hasData = values.some(value => value > 0);

        if (notificationChartInstance) {
            notificationChartInstance.data.datasets[0].data = values;
            notificationChartInstance.options.scales.y.max = hasData ? undefined : 5;
            notificationChartInstance.update("none");
        } else {
            notificationChartInstance = new Chart(canvas.getContext("2d"), {
                type: "bar",
                data: {
                    labels: ["Completed", "Missed", "Skipped", "Pending"],
                    datasets: [
                        {
                            label: "Responses",
                            data: values,
                            backgroundColor: "#ea580c",
                            borderRadius: 6,
                            maxBarThickness: 55
                        }
                    ]
                },
                options: {
                    ...commonChartOptions,
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: "#475569",
                                autoSkip: false,
                                maxRotation: 0,
                                minRotation: 0,
                                font: {
                                    family: "Outfit",
                                    size: window.innerWidth <= 480 ? 9 : 12
                                }
                            }
                        },
                        y: {
                            grid: {
                                color: "rgba(0, 0, 0, 0.05)"
                            },
                            beginAtZero: true,
                            min: 0,
                            max: hasData ? undefined : 5,
                            ticks: {
                                color: "#475569",
                                stepSize: 1,
                                precision: 0,
                                font: {
                                    family: "Outfit",
                                    size: window.innerWidth <= 480 ? 9 : 12
                                }
                            }
                        }
                    }
                }
            });
        }
    }
}

// Removed manual resize listener to prevent layout thrashing on Android

function initializeNutriAnalytics() {
    if (window.__nutriAnalyticsInitialized) {
        return;
    }

    window.__nutriAnalyticsInitialized = true;

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            window.analyticsManager = new AnalyticsManager();
            window.analyticsManager.renderNutriAnalytics();
        });
    });
}

if (document.readyState === "complete") {
    initializeNutriAnalytics();
} else {
    window.addEventListener("load", initializeNutriAnalytics, {
        once: true
    });
}
