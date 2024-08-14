# -*- coding: utf-8 -*-
# __init__.py  -  Coordinates converter from PL-ETRF2000 to PL-2000 - QGIS plugin in python
#     begin             : 2024-04-22
#     version           : 1.1.4
#.....version date......: 2024-08-15
#     author            : Szymon Kędziora

def classFactory(iface):
    from .konwerterPLETRF2000PL2000Plugin import KonwerterPLETRF2000PL2000Plugin
    return KonwerterPLETRF2000PL2000Plugin(iface)
    