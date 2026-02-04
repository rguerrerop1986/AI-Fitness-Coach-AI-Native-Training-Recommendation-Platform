//
//  FitnessCoachWrapperApp.swift
//  FitnessCoachWrapper
//
//  App entry point. Deep links (fitnesscoach://open?path=...) are handled in ContentView via .onOpenURL.
//

import SwiftUI

@main
struct FitnessCoachWrapperApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
