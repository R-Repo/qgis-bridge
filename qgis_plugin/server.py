"""
Qt TCP server — runs on QGIS's existing event loop (no background thread needed).

Listens on localhost:45678 for newline-delimited JSON messages from the Python package.
Loads the specified layer into the current QGIS project and returns a JSON response.
"""

import json

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer
from qgis.PyQt.QtCore import QByteArray
from qgis.PyQt.QtNetwork import QHostAddress, QTcpServer

DEFAULT_PORT = 45678


class BridgeServer:
    def __init__(self, iface, port: int = DEFAULT_PORT):
        self.iface = iface
        self.port = port
        self._server = QTcpServer()
        self._server.newConnection.connect(self._on_connection)

    def start(self):
        if not self._server.listen(QHostAddress.LocalHost, self.port):
            raise RuntimeError(
                f"qgis-bridge: failed to bind to port {self.port}"
            )

    def stop(self):
        self._server.close()

    def _on_connection(self):
        socket = self._server.nextPendingConnection()
        if socket is None:
            return
        socket.waitForReadyRead(5000)
        data = socket.readAll().data().decode("utf-8").strip()
        response = self._handle(data)
        socket.write(QByteArray((json.dumps(response) + "\n").encode("utf-8")))
        socket.flush()
        socket.disconnectFromHost()

    def _handle(self, raw: str) -> dict:
        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            return {"status": "error", "message": f"Invalid JSON: {e}"}

        msg_type = msg.get("type")
        try:
            if msg_type == "vector":
                return self._load_vector(msg)
            elif msg_type == "raster":
                return self._load_raster(msg)
            else:
                return {"status": "error", "message": f"Unknown type: {msg_type!r}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _load_vector(self, msg: dict) -> dict:
        layer_name = msg["layer_name"]
        file_path = msg["file_path"]

        if msg.get("update_existing"):
            self._remove_layers_by_name(layer_name)

        layer = QgsVectorLayer(file_path, layer_name, "ogr")
        if not layer.isValid():
            return {"status": "error", "message": f"Invalid vector layer: {file_path}"}

        qml_path = msg.get("qml_path")
        if qml_path:
            layer.loadNamedStyle(qml_path)

        QgsProject.instance().addMapLayer(layer)
        self.iface.mapCanvas().refresh()
        return {"status": "ok", "layer_id": layer.id()}

    def _load_raster(self, msg: dict) -> dict:
        layer_name = msg["layer_name"]
        gdal_path = msg["gdal_path"]

        if msg.get("update_existing"):
            self._remove_layers_by_name(layer_name)

        layer = QgsRasterLayer(gdal_path, layer_name)
        if not layer.isValid():
            return {"status": "error", "message": f"Invalid raster layer: {gdal_path}"}

        QgsProject.instance().addMapLayer(layer)
        self.iface.mapCanvas().refresh()
        return {"status": "ok", "layer_id": layer.id()}

    def _remove_layers_by_name(self, name: str):
        project = QgsProject.instance()
        for layer in project.mapLayersByName(name):
            project.removeMapLayer(layer.id())
