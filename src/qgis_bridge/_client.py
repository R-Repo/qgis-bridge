"""
TCP socket client.

Connects to the qgis-bridge QGIS plugin on localhost:PORT,
sends one newline-delimited JSON message, reads one JSON response, closes.

No dependencies beyond stdlib.
"""

DEFAULT_PORT = 45678
