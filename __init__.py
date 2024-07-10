# -*- coding: utf-8 -*-
# __init__.py  -  Coordinates converter from PL-ETRF2000 to PL-2000 - QGIS plugin in python
#     begin             : 2024-05-10
#     version           : 1.1.2
#.....version date......: 2024-07-10
#     author            : Szymon Kędziora

def classFactory(iface):
    from .konwerterPLETRF2000PL2000Plugin import KonwerterPLETRF2000PL2000Plugin
    return KonwerterPLETRF2000PL2000Plugin(iface)
    