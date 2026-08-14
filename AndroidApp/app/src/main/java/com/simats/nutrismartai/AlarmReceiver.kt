package com.simats.nutrismartai

import android.app.AlarmManager
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import java.util.Calendar

class AlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val email = intent.getStringExtra("email") ?: return
        val planType = intent.getStringExtra("planType") ?: return
        val mealName = intent.getStringExtra("mealName") ?: "Meal"

        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        
        // Ensure channel is created
        NotificationHelper.createNotificationChannel(context)

        // Show the initial meal notification
        val builder = NotificationCompat.Builder(context, NotificationHelper.MEAL_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info) // Fallback icon, ideally use your app icon
            .setContentTitle("🍽️ Time for $mealName!")
            .setContentText("It is time for your $planType meal. Eat your planned meal \ud83d\udcaa")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)

        val notificationId = (planType + mealName + "meal").hashCode()
        notificationManager.notify(notificationId, builder.build())

        // Now, schedule the Feedback Notification for exactly 1 hour from now
        scheduleFeedbackAlarm(context, email, planType, mealName)
    }

    private fun scheduleFeedbackAlarm(context: Context, email: String, planType: String, mealName: String) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val intent = Intent(context, FeedbackReceiver::class.java).apply {
            putExtra("email", email)
            putExtra("planType", planType)
            putExtra("mealName", mealName)
            putExtra("action_type", "trigger_feedback_notification")
        }

        val requestCode = (planType + mealName + "feedback").hashCode()
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            requestCode,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Schedule for 1 hour from now
        val calendar = Calendar.getInstance().apply {
            timeInMillis = System.currentTimeMillis()
            add(Calendar.HOUR_OF_DAY, 1)
            // Note: During testing you might want to change this to add(Calendar.MINUTE, 1) instead of 1 hour
        }

        // We use setAndAllowWhileIdle so it triggers even if device is dozing
        try {
            alarmManager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP,
                calendar.timeInMillis,
                pendingIntent
            )
        } catch (e: SecurityException) {
            e.printStackTrace()
        }
    }
}
