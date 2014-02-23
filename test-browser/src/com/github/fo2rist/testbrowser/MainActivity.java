package com.github.fo2rist.testbrowser;

import android.net.Uri;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.Window;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.GeolocationPermissions.Callback;
import android.widget.Toast;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;

public class MainActivity extends Activity {

	private WebView webView_;

	@SuppressLint("SetJavaScriptEnabled")
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		getWindow().requestFeature(Window.FEATURE_PROGRESS);
		setContentView(R.layout.activity_main);
		
		webView_ = (WebView) findViewById(R.id.web_view);
		webView_.setKeepScreenOn(true);
		webView_.getSettings().setJavaScriptEnabled(true);
		webView_.setWebChromeClient(new WebChromeClient() {
			public void onProgressChanged(WebView view, int progress) {
				// Activities and WebViews measure progress with different scales.
				// The progress meter will automatically disappear when we reach 100%
				setProgress(progress * 100);
			}
			@Override
			public void onGeolocationPermissionsShowPrompt(String origin, Callback callback) {
				callback.invoke(origin, true, false);
			}
		});
		webView_.setWebViewClient(new WebViewClient() {
			@Override
			public boolean shouldOverrideUrlLoading(WebView view, String url) {
				view.loadUrl(url); //Always handle redirections and links opening inside same web-view
				return false;
			}
			
			@Override
			public void onPageStarted(WebView view, String url, Bitmap favicon) {
				super.onPageStarted(view, url, favicon);
				setTitle(url);
			}
			
			@Override
			public void onPageFinished(WebView view, String url) {
				super.onPageFinished(view, url);
			}
			
			@Override
			public void onReceivedError(WebView view,
					int errorCode,
					String description,
					String failingUrl) {
				super.onReceivedError(view, errorCode, description, failingUrl);
				Toast.makeText(MainActivity.this, "Error: " + description, Toast.LENGTH_SHORT).show();
			}
		});
		
		openUrlFromExtras(getIntent());
	}
	
	@Override
	protected void onNewIntent(Intent intent) {
		openUrlFromExtras(intent);
	}
	
	@Override
	public boolean onKeyDown(int keyCode, KeyEvent event) {
	    // Check if the key event was the Back button and if there's history
	    if ((keyCode == KeyEvent.KEYCODE_BACK) && webView_.canGoBack()) {
	    	webView_.goBack();
	        return true;
	    }
	    // If it wasn't the Back key or there's no web page history, bubble up to the default
	    // system behavior (probably exit the activity)
	    return super.onKeyDown(keyCode, event);
	}
	
	private void openUrlFromExtras(Intent intent) {
		String scheme = intent.getScheme();
		if (!"http".equals(scheme) && ! "https".equals(scheme)) {
			return;
		}
		
		Uri uri = intent.getData();
		webView_.loadUrl(uri.toString());
	}
}
