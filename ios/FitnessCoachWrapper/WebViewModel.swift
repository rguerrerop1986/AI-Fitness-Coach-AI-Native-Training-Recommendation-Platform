//
//  WebViewModel.swift
//  FitnessCoachWrapper
//
//  Observable state for loading, error, and navigation. Drives ContentView and WebView.
//

import Foundation
import Combine
import WebKit

@MainActor
final class WebViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var currentURL: URL?
    @Published var canGoBack = false

    private(set) var webView: WKWebView?

    func setWebView(_ webView: WKWebView) {
        self.webView = webView
    }

    func setLoading(_ loading: Bool) {
        isLoading = loading
    }

    func setError(_ message: String?) {
        errorMessage = message
    }

    func setCurrentURL(_ url: URL?) {
        currentURL = url
    }

    func setCanGoBack(_ value: Bool) {
        canGoBack = value
    }

    func reload() {
        errorMessage = nil
        webView?.reload()
    }

    func goBack() {
        guard webView?.canGoBack == true else { return }
        webView?.goBack()
    }

    /// Navigate to base URL + path (e.g. for deep links).
    func navigateTo(path: String) {
        errorMessage = nil
        let pathNormalized = path.hasPrefix("/") ? path : "/" + path
        guard let url = URL(string: Constants.baseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/")) + pathNormalized) else { return }
        let request = URLRequest(url: url)
        webView?.load(request)
    }

    /// Load the default base URL (used on first load and retry).
    func loadBaseURL() {
        errorMessage = nil
        guard let url = URL(string: Constants.baseURL) else { return }
        let request = URLRequest(url: url)
        webView?.load(request)
    }
}
