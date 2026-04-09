def classFactory(iface):
    from .plugin import QGISBridgePlugin
    return QGISBridgePlugin(iface)
