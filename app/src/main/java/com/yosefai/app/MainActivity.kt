package com.yosefai.app

import android.app.Activity
import android.os.Bundle
import android.widget.TextView

class MainActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val textView = TextView(this)
        textView.text = "Yosef AI"
        textView.textSize = 32f
        textView.setPadding(40, 40, 40, 40)

        setContentView(textView)
    }
}
