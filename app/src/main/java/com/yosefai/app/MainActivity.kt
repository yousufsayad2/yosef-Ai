package com.yosefai.app

import android.app.Activity
import android.os.Bundle
import android.content.Intent
import android.net.Uri

class MainActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val url = "https://yosef-ai-2pzqmuovs4ggxc5wyvz8ce.streamlit.app/"

        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
        startActivity(intent)

        finish()
    }
}
