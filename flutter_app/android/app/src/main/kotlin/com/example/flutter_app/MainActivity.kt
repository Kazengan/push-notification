package com.example.flutter_app

import io.flutter.embedding.android.FlutterActivity
import android.content.Intent

class MainActivity: FlutterActivity() {
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        // Don't auto-open when notification is tapped
        if (intent.action == "android.intent.action.MAIN") {
            // Don't bring app to foreground automatically
            return
        }
    }
    
    override fun onResume() {
        super.onResume()
        // Prevent unwanted auto-opening behavior
    }
}
