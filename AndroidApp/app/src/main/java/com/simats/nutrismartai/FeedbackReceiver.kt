package com.simats.nutrismartai

import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

class FeedbackReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val actionType = intent.getStringExtra("action_type")
        val email = intent.getStringExtra("email") ?: return
        val planType = intent.getStringExtra("planType") ?: return
        val mealName = intent.getStringExtra("mealName") ?: "Meal"
        
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        when (actionType) {
            "trigger_feedback_notification" -> {
                // This was triggered 1 hour after the meal. Show the feedback notification.
                showFeedbackNotification(context, notificationManager, email, planType, mealName)
            }
            "action_ate" -> {
                // User clicked "Ate"
                val notifId = intent.getIntExtra("notif_id", 0)
                notificationManager.cancel(notifId)
                sendLogToBackend(email, planType, mealName, "Ate")
            }
            "action_missed" -> {
                // User clicked "Missed"
                val notifId = intent.getIntExtra("notif_id", 0)
                notificationManager.cancel(notifId)
                sendLogToBackend(email, planType, mealName, "Missed")
            }
        }
    }

    private fun showFeedbackNotification(
        context: Context,
        notificationManager: NotificationManager,
        email: String,
        planType: String,
        mealName: String
    ) {
        val notificationId = (planType + mealName + "feedback_prompt").hashCode()

        // Intent for "Ate"
        val ateIntent = Intent(context, FeedbackReceiver::class.java).apply {
            putExtra("action_type", "action_ate")
            putExtra("email", email)
            putExtra("planType", planType)
            putExtra("mealName", mealName)
            putExtra("notif_id", notificationId)
        }
        val atePendingIntent = PendingIntent.getBroadcast(
            context,
            (notificationId.toString() + "ate").hashCode(),
            ateIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Intent for "Missed"
        val missedIntent = Intent(context, FeedbackReceiver::class.java).apply {
            putExtra("action_type", "action_missed")
            putExtra("email", email)
            putExtra("planType", planType)
            putExtra("mealName", mealName)
            putExtra("notif_id", notificationId)
        }
        val missedPendingIntent = PendingIntent.getBroadcast(
            context,
            (notificationId.toString() + "miss").hashCode(),
            missedIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val builder = NotificationCompat.Builder(context, NotificationHelper.MEAL_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Feedback: $mealName")
            .setContentText("Did you eat your $planType meal?")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .addAction(android.R.drawable.checkbox_on_background, "Ate It", atePendingIntent)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel, "Missed It", missedPendingIntent)

        notificationManager.notify(notificationId, builder.build())
    }

    private fun sendLogToBackend(email: String, planType: String, mealName: String, status: String) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                // Same base URL as RetrofitClient
                val url = URL("http://10.113.224.191:8000/api/log_feedback")
                val connection = url.openConnection() as HttpURLConnection
                connection.requestMethod = "POST"
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded")

                val postData = "email=" + URLEncoder.encode(email, "UTF-8") +
                        "&plan_type=" + URLEncoder.encode(planType, "UTF-8") +
                        "&meal_name=" + URLEncoder.encode(mealName, "UTF-8") +
                        "&status=" + URLEncoder.encode(status, "UTF-8")

                val out = OutputStreamWriter(connection.outputStream)
                out.write(postData)
                out.flush()
                out.close()

                val responseCode = connection.responseCode
                println("Feedback sent. Response Code: $responseCode")
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
}
