# FitnessCoachWrapper — iOS Wrapper (SwiftUI + WKWebView)

## PARAMS

```
BASE_URL="http://192.168.0.115:5174/"
ALLOWED_HOST="192.168.0.115"
ALLOWED_PORT=5174
APP_SCHEME="fitnesscoach"
DEFAULT_PATH="/"
```

---

## Requisitos

- Xcode 14+
- iOS 16+
- Swift 5.7+
- Sin dependencias externas (solo SwiftUI + WebKit)

---

## Paso 1: Crear el proyecto en Xcode

1. Abre **Xcode** → **File** → **New** → **Project**.
2. **iOS** → **App** → Next.
3. Configuración:
   - **Product Name:** `FitnessCoachWrapper`
   - **Team:** tu equipo (necesario para dispositivo y TestFlight).
   - **Organization Identifier:** p. ej. `com.tudominio`
   - **Interface:** SwiftUI
   - **Language:** Swift
   - **Storage:** None
   - Desmarca **Include Tests** si quieres.
4. **Save** en la carpeta `ios/` (junto a este README) para que quede `ios/FitnessCoachWrapper/` con el `.xcodeproj`.

---

## Paso 2: Añadir / reemplazar archivos

1. En el **Project Navigator** (panel izquierdo), dentro del grupo **FitnessCoachWrapper**:
   - Borra el `ContentView.swift` por defecto si Xcode lo creó.
   - Añade los archivos de este repo (o copia su contenido):
     - `Constants.swift`
     - `WebViewModel.swift`
     - `WebView.swift`
     - `WebViewCoordinator.swift`
     - `ContentView.swift`
     - `DeepLinkHandler.swift`
     - `FitnessCoachWrapperApp.swift` (reemplaza el `*App.swift` por defecto)
2. Asegúrate de que **Target Membership** esté marcado en **FitnessCoachWrapper** para todos.

---

## Paso 3: Info.plist — ATS y URL Scheme

### Opción A: Si el proyecto tiene Info.plist propio

1. Abre **Info.plist** del target FitnessCoachWrapper.
2. Añade la excepción ATS para HTTP en tu host:
   - **Key:** `App Transport Security Settings` (Dictionary).
   - Dentro: **Exception Domains** (Dictionary).
   - Dentro: **192.168.0.115** (Dictionary).
   - Dentro de ese dominio:
     - **Allow Insecure HTTP Loads** = YES (Boolean).
     - **Includes Subdomains** = YES (Boolean).
3. Añade el URL Type para el deep link:
   - **Key:** `URL types` (Array).
   - Item 0 (Dictionary):
     - **URL Schemes** = `fitnesscoach` (Array con un string).
     - **URL Identifier** = p. ej. `com.tudominio.fitnesscoach`.
     - **Role** = Editor.

### Opción B: Si usas el Info.plist generado en este repo

1. En Xcode, en el **target** FitnessCoachWrapper → pestaña **Info**.
2. En **Custom iOS Target Properties**:
   - Copia las entradas de **App Transport Security** y **URL Types** del `Info.plist` incluido en este directorio (o pégalas a mano como en Opción A).

Resultado mínimo en plist:

- **NSAppTransportSecurity** → **NSExceptionDomains** → **192.168.0.115**:
  - **NSExceptionAllowsInsecureHTTPLoads** = YES
  - **NSIncludesSubdomains** = YES
- **CFBundleURLTypes** → un item con **CFBundleURLSchemes** = `fitnesscoach`.

---

## Paso 4: Configurar URL Types en el target

1. Selecciona el **proyecto** (icono azul) → **target FitnessCoachWrapper**.
2. Pestaña **Info** → sección **URL Types**.
3. Añade un URL Type:
   - **Identifier:** p. ej. `com.tudominio.fitnesscoach`
   - **URL Schemes:** `fitnesscoach`
   - **Role:** Editor

Así se registra el scheme `fitnesscoach://` para deep links.

---

## Paso 5: Ejecutar en simulador

1. **Product** → **Destination** → elige un iPhone (p. ej. iPhone 15, iOS 17).
2. **Product** → **Run** (⌘R).
3. En la app, debería cargar `http://192.168.0.115:5174/`.  
   En simulador, ese IP suele ser el de tu Mac; asegúrate de que la web esté sirviendo en ese host/puerto y que el Mac y el simulador puedan alcanzarlo (misma red o localhost según tu setup).

---

## Paso 6: Ejecutar en iPhone real

1. Conecta el iPhone por USB.
2. **Product** → **Destination** → tu iPhone.
3. Primera vez: **Signing & Capabilities** → **Team** → elige tu Apple ID / equipo.
4. En el iPhone: **Ajustes** → **General** → **Gestión de dispositivos** → confía en tu certificado de desarrollador si lo pide.
5. **Product** → **Run** (⌘R).
6. El iPhone debe estar en la **misma WiFi** que el Mac/servidor donde corre `http://192.168.0.115:5174/`.  
   Si tu servidor está en el Mac, la IP debe ser la del Mac en esa red (p. ej. 192.168.0.115).

---

## Paso 7: Archive y subida a TestFlight

1. **Product** → **Destination** → **Any iOS Device (arm64)**.
2. **Product** → **Archive**.
3. Cuando termine, se abre el **Organizer** (Window → Organizer si no).
4. Selecciona el archive recién creado → **Distribute App**.
5. **App Store Connect** → Next.
6. **Upload** → Next.
7. Opciones por defecto (incluir bitcode si lo pide, etc.) → Next.
8. Revisa y **Upload**.
9. En [App Store Connect](https://appstoreconnect.apple.com) → tu app → **TestFlight** → espera a que procese el build y asígnale un grupo de testers (p. ej. Sandy).

---

## localStorage / JWT

- Se usa **WKWebsiteDataStore.default()** (persistente), así que **localStorage y JWT persisten** entre aperturas de la app.
- En **DEBUG**, en consola de Xcode verás un log tipo:  
  `[FitnessCoach DEBUG] localStorage access_token: token present (length: …)` o `no access_token`.  
  Solo para comprobar que el dato persiste; no se expone el token en la UI.

---

## Deep link

- Formato: `fitnesscoach://open?path=/ruta`
- Ejemplo: `fitnesscoach://open?path=/clients/123` → la app carga `http://192.168.0.115:5174/clients/123`.
- Probar en simulador/dispositivo:  
  Safari o Notes con un enlace `fitnesscoach://open?path=/login`, o desde terminal (simulador):  
  `xcrun simctl openurl booted "fitnesscoach://open?path=/login"`.

---

## Producción (resumen)

- **No** dejar la excepción ATS para HTTP en producción.
- Servir la web por **HTTPS** con un **dominio real**.
- En **Constants.swift** cambiar `baseURL` a esa URL HTTPS.
- Quitar la excepción de **192.168.0.115** del Info.plist y, si aplica, ajustar **ALLOWED_HOST** / **ALLOWED_PORT** en código para el nuevo dominio/puerto.

---

## Troubleshooting

| Problema | Comprobar |
|----------|-----------|
| **Pantalla en blanco** | 1) ATS: excepción para `192.168.0.115` en Info.plist. 2) URL en Constants: `http://192.168.0.115:5174/`. 3) Servidor web levantado y accesible en esa IP/puerto. |
| **iPhone no ve el servidor** | 1) Mismo WiFi (iPhone y servidor). 2) Firewall del Mac: permitir puerto 5174. 3) En backend, CORS permite el origen de la web (no hace falta para la app nativa, pero la web en navegador sí). |
| **localStorage no persiste** | 1) Uso de `WKWebsiteDataStore.default()` (no `.nonPersistent()`). 2) No usar modo privado/incógnito en WKWebView. 3) No borrar datos del sitio desde iOS. |
| **Redirect loops** | 1) Allowlist: solo permitir host `192.168.0.115` y puerto `5174`. 2) Si la web redirige a otro dominio, el wrapper lo abre en Safari (no dentro del WebView). |
| **Links externos no abren** | El coordinator abre en Safari solo cuando el link es a otro host. Comprueba que `openInSafari` usa `UIApplication.shared.open(url)` y que el link no sea del mismo host/puerto. |

---

## Estructura de archivos

```
FitnessCoachWrapper/
├── FitnessCoachWrapperApp.swift   # @main, entrada
├── ContentView.swift              # Loader, error, recargar, atrás, WebView
├── WebView.swift                  # UIViewRepresentable + WKWebView
├── WebViewCoordinator.swift       # WKNavigationDelegate + WKUIDelegate
├── WebViewModel.swift             # Estado (isLoading, error, reload, navigateTo)
├── DeepLinkHandler.swift          # Parsea fitnesscoach://open?path=...
├── Constants.swift                # BASE_URL, ALLOWED_HOST, APP_SCHEME, etc.
├── Info.plist                     # ATS + URL Types (si se usa este plist)
└── Assets.xcassets                # (opcional, creado por Xcode)
```
