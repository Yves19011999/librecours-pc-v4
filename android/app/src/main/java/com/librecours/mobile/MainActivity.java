package com.librecours.mobile;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.Gravity;
import android.view.View;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
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
        help.setText("Saisissez l’adresse du serveur Flask LibreCours sur votre réseau, puis appuyez sur Ouvrir. Exemple : http://192.168.1.10:5000");
        help.setTextSize(16); help.setPadding(0, 24, 0, 20);
        EditText url = new EditText(this);
        url.setSingleLine(true); url.setHint("http://192.168.1.10:5000");
        url.setText(prefs.getString("url", ""));
        Button open = new Button(this); open.setText("Ouvrir LibreCours");
        open.setOnClickListener(v -> { String value = url.getText().toString().trim(); if (!value.startsWith("http://") && !value.startsWith("https://")) value = "http://" + value; prefs.edit().putString("url", value).apply(); load(value); });
        root.addView(title); root.addView(help); root.addView(url, new LinearLayout.LayoutParams(-1, -2)); root.addView(open, new LinearLayout.LayoutParams(-1, -2));
        setContentView(root);
    }

    private void load(String url) {
        webView = new WebView(this);
        webView.setWebViewClient(new WebViewClient() {
            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) showConnectionError(url, error.getDescription().toString());
            }
        });
        webView.getSettings().setJavaScriptEnabled(true); webView.getSettings().setDomStorageEnabled(true); webView.loadUrl(url); setContentView(webView);
    }

    private void showConnectionError(String url, String reason) {
        LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(40, 60, 40, 40); root.setGravity(Gravity.CENTER_HORIZONTAL);
        TextView title = new TextView(this); title.setText("Serveur inaccessible"); title.setTextSize(26); title.setTextColor(Color.rgb(160, 45, 45));
        TextView message = new TextView(this); message.setText("LibreCours n’a pas pu joindre :\\n" + url + "\\n\\nVérifiez que Flask est démarré avec python app.py et que le téléphone est sur le même réseau Wi‑Fi.\\n\\nDétail : " + reason); message.setTextSize(16); message.setPadding(0, 24, 0, 24);
        Button retry = new Button(this); retry.setText("Réessayer"); retry.setOnClickListener(v -> load(url)); Button config = new Button(this); config.setText("Modifier l’adresse"); config.setOnClickListener(v -> showLauncher());
        root.addView(title); root.addView(message, new LinearLayout.LayoutParams(-1, -2)); root.addView(retry, new LinearLayout.LayoutParams(-1, -2)); root.addView(config, new LinearLayout.LayoutParams(-1, -2)); setContentView(root);
    }

    @Override public void onBackPressed() { if (webView != null && webView.canGoBack()) webView.goBack(); else showLauncher(); }
}
