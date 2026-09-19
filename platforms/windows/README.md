# Windows placeholder

A tervezett Windows-integráció külön WinUI 3 vagy WPF alkalmazásból és File Explorer shell-adapterből állna.

Tervezett hivatalos belépési pont:

- kezdetben statikus File Explorer shell verb a mappa jobbklikkes menüjében
- később szükség esetén `IExplorerCommand`
- aktuális mappaútvonal átadása a TODO-alkalmazásnak
- WebView2 vagy natív WinUI felület
- MSIX vagy Sparse Package alapú telepítés

Ebben a verzióban még nincs Windows implementáció, Visual Studio-projekt vagy telepítő. A File Explorerbe dokkolt TODO-panel nem része a vállalt célfelületnek; külön alkalmazásablak az elsődleges irány.
