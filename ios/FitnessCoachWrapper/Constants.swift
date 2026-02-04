//
//  Constants.swift
//  FitnessCoachWrapper
//
//  Central configuration for web app URL, allowlist, and deep link scheme.
//

import Foundation

enum Constants {
    // MARK: - Web App (DEV/LAN)
    /// Base URL of the web app. For production: use HTTPS and a real domain.
    static let baseURL = "http://192.168.0.115:5174/"
    static let defaultPath = "/"

    // MARK: - Allowlist (navigation only within app)
    static let allowedHost = "192.168.0.115"
    static let allowedPort = 5174

    // MARK: - Deep Link
    static let appScheme = "fitnesscoach"
    /// Example: fitnesscoach://open?path=/clients/123
    static let deepLinkHost = "open"
    static let deepLinkPathQueryKey = "path"
}
