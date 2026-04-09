"""
QGIS plugin entry point.

Starts the TCP server when the plugin loads and stops it when unloaded.
"""


class QGISBridgePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.server = None

    def initGui(self):
        from .server import BridgeServer
        self.server = BridgeServer(self.iface)
        self.server.start()

    def unload(self):
        if self.server:
            self.server.stop()
            self.server = None
