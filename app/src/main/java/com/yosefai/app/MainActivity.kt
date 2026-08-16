package com.yosefai.app

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient

class MainActivity : Activity() {

    private lateinit var webView: WebView

    private var filePathCallback: ValueCallback<Array<Uri>>? = null

    companion object {
        private const val FILE_CHOOSER_REQUEST = 1001
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)

        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.databaseEnabled = true
        webView.settings.loadsImagesAutomatically = true

        webView.settings.allowFileAccess = true
        webView.settings.allowContentAccess = true

        webView.webViewClient = WebViewClient()

        webView.webChromeClient = object : WebChromeClient() {

            override fun onShowFileChooser(
                webView: WebView?,
                filePath: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {

                filePathCallback?.onReceiveValue(null)

                filePathCallback = filePath

                try {
                    val intent = Intent(Intent.ACTION_GET_CONTENT)

                    intent.addCategory(Intent.CATEGORY_OPENABLE)

                    intent.type = "*/*"

                    intent.putExtra(
                        Intent.EXTRA_ALLOW_MULTIPLE,
                        false
                    )

                    startActivityForResult(
                        Intent.createChooser(
                            intent,
                            "اختار صورة أو ملف"
                        ),
                        FILE_CHOOSER_REQUEST
                    )

                } catch (e: Exception) {

                    filePathCallback = null

                    return false
                }

                return true
            }
        }

        webView.loadUrl(
            "https://yosef-ai-2pzqmuovs4ggxc5wyvz8ce.streamlit.app/"
        )

        setContentView(webView)
    }

    override fun onActivityResult(
        requestCode: Int,
        resultCode: Int,
        data: Intent?
    ) {
        super.onActivityResult(
            requestCode,
            resultCode,
            data
        )

        if (requestCode == FILE_CHOOSER_REQUEST) {

            val callback = filePathCallback

            filePathCallback = null

            if (resultCode == Activity.RESULT_OK && data != null) {

                val results = mutableListOf<Uri>()

                data.data?.let {
                    results.add(it)
                }

                callback?.onReceiveValue(
                    results.toTypedArray()
                )

            } else {

                callback?.onReceiveValue(null)
            }
        }
    }

    override fun onBackPressed() {

        if (webView.canGoBack()) {

            webView.goBack()

        } else {

            super.onBackPressed()
        }
    }
}
