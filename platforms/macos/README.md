# macOS placeholder

A tervezett macOS-integráció külön SwiftUI/AppKit alkalmazásból és Finder Sync Extensionből állna.

Tervezett hivatalos belépési pont:

- Finder Sync Extension a mappa kontextusmenüjéhez és toolbar-gombjához
- aktuális mappa URL-jének átadása a külön Nemo TODO alkalmazásnak
- WKWebView vagy natív SwiftUI felület
- SQLite-adatbázis a macOS alkalmazás-adatkönyvtárában

Ebben a verzióban még nincs macOS implementáció, Xcode-projekt vagy telepítő. A Finderbe dokkolt TODO-panel nem része a vállalt célfelületnek; külön alkalmazásablak az elsődleges irány.
