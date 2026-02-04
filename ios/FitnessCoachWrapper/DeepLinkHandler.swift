//
//  DeepLinkHandler.swift
//  FitnessCoachWrapper
//
//  Parses custom URL scheme (fitnesscoach://open?path=...) and returns path for navigation.
//

import Foundation

enum DeepLinkHandler {
    /// Parses URL like fitnesscoach://open?path=/clients/123
    /// Returns the path component to append to BASE_URL, or nil if invalid.
    static func path(from url: URL) -> String? {
        guard url.scheme == Constants.appScheme,
              url.host == Constants.deepLinkHost else { return nil }
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let path = components.queryItems?.first(where: { $0.name == Constants.deepLinkPathQueryKey })?.value else {
            return nil
        }
        return path.hasPrefix("/") ? path : "/" + path
    }
}
