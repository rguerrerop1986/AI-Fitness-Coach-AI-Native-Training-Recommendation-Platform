//
//  WebViewCoordinator.swift
//  FitnessCoachWrapper
//
//  WKNavigationDelegate + WKUIDelegate. Handles navigation policy (allowlist / open externally) and loading state.
//

import Foundation
import UIKit
import WebKit

final class WebViewCoordinator: NSObject {
    private weak var viewModel: WebViewModel?

    init(viewModel: WebViewModel) {
        self.viewModel = viewModel
    }

    private func isAllowed(url: URL?) -> Bool {
        guard let url = url, let host = url.host else { return false }
        let port = url.port ?? (url.scheme == "https" ? 443 : 80)
        return host == Constants.allowedHost && port == Constants.allowedPort
    }

    private func openInSafari(url: URL) {
        Task { @MainActor in
            await UIApplication.shared.open(url)
        }
    }
}

// MARK: - WKNavigationDelegate

extension WebViewCoordinator: WKNavigationDelegate {
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url else {
            decisionHandler(.cancel)
            return
        }
        if isAllowed(url: url) {
            decisionHandler(.allow)
            return
        }
        if navigationAction.navigationType == .linkActivated {
            openInSafari(url: url)
        }
        decisionHandler(.cancel)
    }

    func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
        Task { @MainActor in
            viewModel?.setLoading(true)
            viewModel?.setError(nil)
        }
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        Task { @MainActor in
            viewModel?.setLoading(false)
            viewModel?.setError(nil)
            viewModel?.setCurrentURL(webView.url)
            viewModel?.setCanGoBack(webView.canGoBack)
            #if DEBUG
            diagnoseLocalStorage(webView: webView)
            #endif
        }
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        Task { @MainActor in
            viewModel?.setLoading(false)
            viewModel?.setError(error.localizedDescription)
        }
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        Task { @MainActor in
            viewModel?.setLoading(false)
            viewModel?.setError(error.localizedDescription)
        }
    }

    #if DEBUG
    private func diagnoseLocalStorage(webView: WKWebView) {
        let script = "localStorage.getItem('access_token') ? 'token present (length: ' + (localStorage.getItem('access_token').length || 0) + ')' : 'no access_token'"
        webView.evaluateJavaScript(script) { result, error in
            if let error = error {
                print("[FitnessCoach DEBUG] localStorage check failed: \(error.localizedDescription)")
                return
            }
            print("[FitnessCoach DEBUG] localStorage access_token: \(result ?? "nil")")
        }
    }
    #endif
}

// MARK: - WKUIDelegate

extension WebViewCoordinator: WKUIDelegate {
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if navigationAction.targetFrame == nil, let url = navigationAction.request.url {
            if isAllowed(url: url) {
                webView.load(navigationAction.request)
            } else {
                openInSafari(url: url)
            }
        }
        return nil
    }
}
