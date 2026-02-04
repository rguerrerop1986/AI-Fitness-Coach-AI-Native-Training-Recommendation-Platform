//
//  WebView.swift
//  FitnessCoachWrapper
//
//  UIViewRepresentable wrapping WKWebView. Uses persistent WKWebsiteDataStore for localStorage/JWT persistence.
//

import SwiftUI
import WebKit

struct WebView: UIViewRepresentable {
    @ObservedObject var viewModel: WebViewModel

    func makeCoordinator() -> WebViewCoordinator {
        WebViewCoordinator(viewModel: viewModel)
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.defaultWebpagePreferences.allowsContentJavaScript = true
        config.processPool = WKProcessPool()
        config.websiteDataStore = .default()
        config.preferences.javaScriptEnabled = true

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.allowsBackForwardNavigationGestures = false
        webView.scrollView.bounces = true
        webView.isInspectable = true

        viewModel.setWebView(webView)
        viewModel.loadBaseURL()

        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {}
}
