package com.simats.nutrismartai

import android.annotation.SuppressLint
import android.Manifest
import android.os.Build
import androidx.core.app.ActivityCompat
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import android.net.Uri
import android.webkit.ValueCallback
import android.os.Bundle
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.activity.compose.BackHandler
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import com.simats.nutrismartai.ui.theme.NutrismartAITheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.POST_NOTIFICATIONS), 101)
            }
        }
        setContent {
            NutrismartAITheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { _ ->
                    NativeWebView(modifier = Modifier.fillMaxSize())
                }
            }
        }
    }
}

@SuppressLint("SetJavaScriptEnabled")
@androidx.compose.runtime.Composable
fun NativeWebView(modifier: Modifier = Modifier) {
    var webViewRef by remember { mutableStateOf<WebView?>(null) }
    var canGoBack by remember { mutableStateOf(false) }
    var fileChooserCallback by remember { mutableStateOf<ValueCallback<Array<Uri>>?>(null) }

    val launcher = androidx.activity.compose.rememberLauncherForActivityResult(
        contract = androidx.activity.result.contract.ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            fileChooserCallback?.onReceiveValue(arrayOf(uri))
        } else {
            fileChooserCallback?.onReceiveValue(null)
        }
        fileChooserCallback = null
    }


    BackHandler(enabled = canGoBack) {
        webViewRef?.goBack()
    }

    AndroidView(
        modifier = modifier.fillMaxSize(),
        factory = { context ->
            WebView(context).apply {
                settings.apply {
                    javaScriptEnabled = true
                    domStorageEnabled = true
                    allowFileAccess = true
                    allowContentAccess = true
                    allowFileAccessFromFileURLs = true
                    allowUniversalAccessFromFileURLs = true
                    mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                }
                webViewClient = object : WebViewClient() {
                    override fun shouldInterceptRequest(
                        view: WebView,
                        request: android.webkit.WebResourceRequest
                    ): android.webkit.WebResourceResponse? {
                        val url = request.url
                        if (url.scheme == "http" && url.host == "localhost") {
                            var path = url.path ?: ""
                            if (path.startsWith("/")) {
                                path = path.substring(1)
                            }
                            try {
                                val mimeType = when {
                                    path.endsWith(".html") -> "text/html"
                                    path.endsWith(".js") -> "application/javascript"
                                    path.endsWith(".css") -> "text/css"
                                    path.endsWith(".png") -> "image/png"
                                    path.endsWith(".jpg") || path.endsWith(".jpeg") -> "image/jpeg"
                                    path.endsWith(".svg") -> "image/svg+xml"
                                    path.endsWith(".mp4") -> "video/mp4"
                                    path.endsWith(".json") -> "application/json"
                                    else -> "application/octet-stream"
                                }
                                val inputStream = context.assets.open(path)
                                return android.webkit.WebResourceResponse(mimeType, "UTF-8", inputStream)
                            } catch (e: Exception) {
                                e.printStackTrace()
                            }
                        }
                        return super.shouldInterceptRequest(view, request)
                    }

                    override fun onPageFinished(view: WebView?, url: String?) {
                        super.onPageFinished(view, url)
                        canGoBack = view?.canGoBack() == true
                    }

                    override fun doUpdateVisitedHistory(view: WebView?, url: String?, isReload: Boolean) {
                        super.doUpdateVisitedHistory(view, url, isReload)
                        canGoBack = view?.canGoBack() == true
                    }
                }
                
                webChromeClient = object : WebChromeClient() {
                    override fun onShowFileChooser(
                        webView: WebView?,
                        filePathCallback: ValueCallback<Array<Uri>>?,
                        fileChooserParams: FileChooserParams?
                    ): Boolean {
                        fileChooserCallback = filePathCallback
                        launcher.launch("image/*")
                        return true
                    }
                }
                addJavascriptInterface(WebAppInterface(context), "Android")

                
                // Load the login page from the local server we just created
                loadUrl("http://localhost/www/login.html")
                webViewRef = this
            }
        },
        update = { webView ->
            // Update logic if needed
        }
    )
}