"""UI package initialization."""
try:
    from ui.main_window import MainWindow, ModernMainWindow
    __all__ = ["MainWindow", "ModernMainWindow"]
except ImportError:
    MainWindow = None
    ModernMainWindow = None
    __all__ = []
