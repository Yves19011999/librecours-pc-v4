package com.librecours.mobile;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.Gravity;
import android.view.View;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.content.SharedPreferences;

public class MainActivity extends Activity {
    private SharedPreferences prefs;
    private WebView webView;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("librecours", MODE_PRIVATE);
        showLauncher();
    }

    private void showLauncher() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(48, 64, 48, 48);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        TextView title = new TextView(this);
        title.setText("LibreCours"); title.setTextSize(30); title.setTextColor(Color.rgb(20, 75, 90));
        TextView help = new TextView(this);
        help.setText("Saisissez l’adresse du serveur Flask LibreCours, puis appuyez sur Ouvrir.");
        help.setTextSize(16); help.setPadding(0, 24, 0, 20);
        EditText url = new EditText(this);
        url.setSingleLine(true); url.setHint("http://192.168.1.10:5000");
        url.setText(prefs.getString("url", "http://10.0.2.2:5000"));
        Button open = new Button(this); open.setText("Ouvrir LibreCours");
        open.setOnClickListener(v -> { String value = url.getText().toString().trim(); if (!value.startsWith("http://") && !value.startsWith("https://")) value = "http://" + value; prefs.edit().putString("url", value).apply(); load(value); });
        root.addView(title); root.addView(help); root.addView(url, new LinearLayout.LayoutParams(-1, -2)); root.addView(open, new LinearLayout.LayoutParams(-1, -2));
        setContentView(root);
    }

    private void load(String url) {
        webView = new WebView(this); webView.setWebViewClient(new WebViewClient()); webView.getSettings().setJavaScriptEnabled(true); webView.getSettings().setDomStorageEnabled(true); webView.loadUrl(url); setContentView(webView);
    }

    @Override public void onBackPressed() { if (webView != null && webView.canGoBack()) webView.goBack(); else showLauncher(); }
}
