"""
QGIS plugin entry point.

Starts the TCP server when the plugin loads and stops it when unloaded.
"""

from qgis.PyQt.QtWidgets import QAction, QMessageBox


class QGISBridgePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.server = None
        self._action = None

    def initGui(self):
        from .server import BridgeServer

        self.server = BridgeServer(self.iface)
        self.server.start()

        self._action = QAction("qgis-bridge Status", self.iface.mainWindow())
        self._action.triggered.connect(self._show_status)
        self.iface.addPluginToMenu("qgis-bridge", self._action)

    def unload(self):
        if self._action:
            self.iface.removePluginMenu("qgis-bridge", self._action)
            self._action = None
        if self.server:
            self.server.stop()
            self.server = None

    def _show_status(self):
        listening = self.server is not None and self.server._server.isListening()
        port = self.server.port if self.server else "N/A"
        status = "Listening" if listening else "Not running"
        QMessageBox.information(
            self.iface.mainWindow(),
            "qgis-bridge",
            f"Status: {status}\nPort: {port}",
        )
