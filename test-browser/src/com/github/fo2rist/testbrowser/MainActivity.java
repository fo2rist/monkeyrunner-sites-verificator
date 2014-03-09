package com.github.fo2rist.testbrowser;

import android.net.Uri;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.View;
import android.view.Window;
import android.view.inputmethod.EditorInfo;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.GeolocationPermissions.Callback;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.TextView.OnEditorActionListener;
import android.widget.Toast;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;

public class MainActivity extends Activity {

	private WebView webView_;
	private EditText addressLine_;
	
	/**
	 * Current loading state.
	 */
	private boolean isLoading_ = false;


	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		getWindow().requestFeature(Window.FEATURE_PROGRESS);
		setContentView(R.layout.activity_main);

		setupActionBar();

		setupWebView();

		openUrlFromExtras(getIntent());
	}
	
	@Override
	protected void onNewIntent(Intent intent) {
		openUrlFromExtras(intent);
	}
	
	@Override
	public boolean onCreateOptionsMenu(Menu menu) {
		MenuInflater inflater = getMenuInflater();
	    inflater.inflate(R.menu.main_activity_actions, menu);
	    return super.onCreateOptionsMenu(menu);
	}
	
	@Override
	public boolean onPrepareOptionsMenu(Menu menu) {
		String currentUrl = webView_.getUrl();
		if (!TextUtils.isEmpty(currentUrl)) {
			MenuItem itemRefresh= menu.findItem(R.id.action_reload);
			MenuItem itemStop= menu.findItem(R.id.action_stop);
			itemRefresh.setVisible(!isLoading_);
			itemStop.setVisible(isLoading_);
		}
	    super.onPrepareOptionsMenu(menu);
	    return true;
	}
	
	@Override
	public boolean onOptionsItemSelected(MenuItem item) {
		switch (item.getItemId()) {
		case R.id.action_reload:
			webView_.reload();
			break;
		case R.id.action_stop:
			webView_.stopLoading();
			break;
		default:
			return super.onOptionsItemSelected(item);				
		}
		return true;
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
	
	@Override
	public void setTitle(CharSequence title) {
		super.setTitle(title);
		if (addressLine_ != null) {
			addressLine_.setText(title);
		}
	}
	
	@Override
	public void setTitle(int titleId) {
		super.setTitle(titleId);
		if (addressLine_ != null) {
			addressLine_.setText(titleId);
		}
	}

	@SuppressLint("SetJavaScriptEnabled")
	private void setupWebView() {
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
				isLoading_ = true;
				invalidateOptionsMenu();
			}
			
			@Override
			public void onPageFinished(WebView view, String url) {
				super.onPageFinished(view, url);
				isLoading_ = false;
				invalidateOptionsMenu();
			}
			
			@Override
			public void onReceivedError(WebView view,
					int errorCode,
					String description,
					String failingUrl) {
				super.onReceivedError(view, errorCode, description, failingUrl);
				isLoading_ = false;
				invalidateOptionsMenu();
				Toast.makeText(MainActivity.this, "Error: " + description, Toast.LENGTH_SHORT).show();
			}
		});
	}

	private void setupActionBar() {
		this.getActionBar().setDisplayShowCustomEnabled(true);
		this.getActionBar().setDisplayShowTitleEnabled(false);

		LayoutInflater inflator = (LayoutInflater)this.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
		View titleView = inflator.inflate(R.layout.title_view, null);

		addressLine_ = ((EditText)titleView.findViewById(R.id.address_line));
		addressLine_.setOnEditorActionListener(new OnEditorActionListener() {
			@Override
			public boolean onEditorAction(TextView sender, int actionId, KeyEvent event) {
				if (actionId == EditorInfo.IME_ACTION_GO) {
					String url = sender.getText().toString().trim();
					if (!url.startsWith("http://") && !url.startsWith("https://")) {
						url = "http://" + url;
					}
					webView_.loadUrl(url);
					return true;
				} else {
					return false;
				}
			}
		});
		//assign the view to the actionbar
		getActionBar().setCustomView(titleView);
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
