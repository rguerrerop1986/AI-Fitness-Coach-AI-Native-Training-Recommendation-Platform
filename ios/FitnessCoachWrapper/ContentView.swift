//
//  ContentView.swift
//  FitnessCoachWrapper
//
//  Main container: loader, error + retry, reload, back, and WebView.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = WebViewModel()

    var body: some View {
        ZStack {
            WebView(viewModel: viewModel)
                .ignoresSafeArea(.all, edges: .bottom)

            if viewModel.isLoading {
                Color(UIColor.systemBackground)
                    .opacity(0.8)
                    .ignoresSafeArea()
                ProgressView("Cargando…")
                    .progressViewStyle(CircularProgressViewStyle(tint: .accentColor))
                    .scaleEffect(1.2)
            }

            if let error = viewModel.errorMessage {
                errorOverlay(message: error)
            }
        }
        .overlay(alignment: .topTrailing) {
            topBar
        }
        .animation(.easeInOut(duration: 0.2), value: viewModel.isLoading)
        .animation(.easeInOut(duration: 0.2), value: viewModel.errorMessage != nil)
        .onOpenURL { url in
            if let path = DeepLinkHandler.path(from: url) {
                viewModel.navigateTo(path: path)
            }
        }
    }

    private var topBar: some View {
        HStack(spacing: 12) {
            if viewModel.canGoBack {
                Button {
                    viewModel.goBack()
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.body.weight(.semibold))
                        .frame(width: 44, height: 44)
                }
            }
            Button {
                viewModel.reload()
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.body.weight(.semibold))
                    .frame(width: 44, height: 44)
            }
        }
        .padding(.top, 8)
        .padding(.trailing, 8)
    }

    private func errorOverlay(message: String) -> some View {
        VStack(spacing: 20) {
            Image(systemName: "wifi.exclamationmark")
                .font(.system(size: 50))
                .foregroundColor(.secondary)
            Text("Error de conexión")
                .font(.headline)
            Text(message)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            Button("Reintentar") {
                viewModel.setError(nil)
                viewModel.loadBaseURL()
            }
            .buttonStyle(.borderedProminent)
            .padding(.top, 8)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(UIColor.systemBackground))
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
