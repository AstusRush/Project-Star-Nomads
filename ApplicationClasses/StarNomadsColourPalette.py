from AGeLib import * #QtCore, QtGui, QtWidgets, pyqtSignal, pyqtProperty
try:
    import typing
except:
    pass
from packaging.version import parse as versionParser #CRITICAL: This is not a build-in module! Use the new function from _AGeFunctions instead!

def loadQPalette(l):
    # type: (typing.List[typing.Tuple[QtGui.QBrush,int,int]]) -> QtGui.QPalette
    # Takes list of tuples with (QtGui.QBrush, ColorRole, ColorGroup)
    Palette = QtGui.QPalette()
    for i in l:
        if i[1] == 20:
            if versionParser(QtCore.qVersion())>=versionParser("5.12"):
                Palette.setBrush(i[2],QtGui.QPalette.PlaceholderText,i[0])
        else:
            Palette.setBrush(i[2],i[1],i[0])
    return Palette


SNDark = {
    "Star Nomads" : {
            "Team -1" : QtGui.QBrush(QtGui.QColor(255,255,255,255),QtCore.Qt.SolidPattern) ,
            "Team 0" : QtGui.QBrush(QtGui.QColor(209,255,203,255),QtCore.Qt.SolidPattern) ,
            "Team 1" : QtGui.QBrush(QtGui.QColor(81,0,255,255),QtCore.Qt.SolidPattern) ,
            "Team 2" : QtGui.QBrush(QtGui.QColor(255,0,0,255),QtCore.Qt.SolidPattern) ,
            "Team 3" : QtGui.QBrush(QtGui.QColor(255,0,234,255),QtCore.Qt.SolidPattern) ,
            "Team 4" : QtGui.QBrush(QtGui.QColor(0,255,0,255),QtCore.Qt.SolidPattern) ,
            "Team 5" : QtGui.QBrush(QtGui.QColor(255,255,0,255),QtCore.Qt.SolidPattern) ,
            "Shield 100" : QtGui.QBrush(QtGui.QColor(0,255,0,255),QtCore.Qt.SolidPattern) ,
            "Shield 50" : QtGui.QBrush(QtGui.QColor(255,119,0,255),QtCore.Qt.SolidPattern) ,
            "Shield 25" : QtGui.QBrush(QtGui.QColor(255,0,0,255),QtCore.Qt.SolidPattern) ,
            "HEX_COLOUR_NORMAL" : QtGui.QBrush(QtGui.QColor(55,55,255,255),QtCore.Qt.SolidPattern) , #"Blue"
            "HEX_COLOUR_RESOURCES" : QtGui.QBrush(QtGui.QColor(155,55,55,255),QtCore.Qt.SolidPattern) ,
            "HEX_COLOUR_SELECT" : QtGui.QBrush(QtGui.QColor(255,255,0,255),QtCore.Qt.SolidPattern) , #"Yellow"
            "HEX_COLOUR_SELECT_FACE" : QtGui.QBrush(QtGui.QColor(0,170,255,255),QtCore.Qt.SolidPattern) , #"Light Blue"
            "HEX_COLOUR_HIGHLIGHT" : QtGui.QBrush(QtGui.QColor(0,170,255,255),QtCore.Qt.SolidPattern) , #"Light Blue"
            "HEX_COLOUR_REACHABLE" : QtGui.QBrush(QtGui.QColor(0,255,0,255),QtCore.Qt.SolidPattern) , #"Green"
            "HEX_COLOUR_ATTACKABLE" : QtGui.QBrush(QtGui.QColor(255,0,0,255),QtCore.Qt.SolidPattern) , #"Red"
            "HEX_COLOUR_ATTACKABLE_FACE" : QtGui.QBrush(QtGui.QColor(255,0,0,255),QtCore.Qt.SolidPattern) , #"Red"
        } ,
}


#    "Pen Colours" : {
#            "Red" : QtGui.QBrush(QtGui.QColor(255,0,0,255),QtCore.Qt.SolidPattern) ,
#            "Green" : QtGui.QBrush(QtGui.QColor(0,255,0,255),QtCore.Qt.SolidPattern) ,
#            "Blue" : QtGui.QBrush(QtGui.QColor(55,55,255,255),QtCore.Qt.SolidPattern) ,
#            "Yellow" : QtGui.QBrush(QtGui.QColor(255,255,0,255),QtCore.Qt.SolidPattern) ,
#            "Cyan" : QtGui.QBrush(QtGui.QColor(0,255,234,255),QtCore.Qt.SolidPattern) ,
#            "Magenta" : QtGui.QBrush(QtGui.QColor(255,0,234,255),QtCore.Qt.SolidPattern) ,
#            "Orange" : QtGui.QBrush(QtGui.QColor(255,119,0,255),QtCore.Qt.SolidPattern) ,
#            "Light Blue" : QtGui.QBrush(QtGui.QColor(0,170,255,255),QtCore.Qt.SolidPattern) ,
#            "White" : QtGui.QBrush(QtGui.QColor(255,255,255,255),QtCore.Qt.SolidPattern) ,
#            "Black" : QtGui.QBrush(QtGui.QColor(0,0,0,255),QtCore.Qt.SolidPattern) ,
#        } ,
#    "Misc Colours" : {
#            "Friendly" : QtGui.QBrush(QtGui.QColor(0,255,21,255),QtCore.Qt.SolidPattern) ,
#            "Hostile" : QtGui.QBrush(QtGui.QColor(255,0,0,255),QtCore.Qt.SolidPattern) ,
#            "Neutral" : QtGui.QBrush(QtGui.QColor(209,255,203,255),QtCore.Qt.SolidPattern) ,
#            "Ally" : QtGui.QBrush(QtGui.QColor(0,136,255,255),QtCore.Qt.SolidPattern) ,
#            "Self" : QtGui.QBrush(QtGui.QColor(81,0,255,255),QtCore.Qt.SolidPattern) ,
#            "Common" : QtGui.QBrush(QtGui.QColor(255,255,255,255),QtCore.Qt.SolidPattern) ,
#            "Uncommon" : QtGui.QBrush(QtGui.QColor(148,144,255,255),QtCore.Qt.SolidPattern) ,
#            "Rare" : QtGui.QBrush(QtGui.QColor(17,255,0,255),QtCore.Qt.SolidPattern) ,
#            "Legendary" : QtGui.QBrush(QtGui.QColor(115,0,255,255),QtCore.Qt.SolidPattern) ,
#            "Mythical" : QtGui.QBrush(QtGui.QColor(255,42,227,255),QtCore.Qt.SolidPattern) ,
#            "Artefact" : QtGui.QBrush(QtGui.QColor(255,255,0,255),QtCore.Qt.SolidPattern) ,
#            "Broken" : QtGui.QBrush(QtGui.QColor(181,181,181,255),QtCore.Qt.SolidPattern) ,
#            "Magical" : QtGui.QBrush(QtGui.QColor(255,46,49,255),QtCore.Qt.SolidPattern) ,
#            "Important" : QtGui.QBrush(QtGui.QColor(255,183,0,255),QtCore.Qt.SolidPattern) ,
#            "Gradient1" : QtGui.QBrush(QtGui.QColor(0,0,0,255),QtCore.Qt.SolidPattern) ,
#            "Gradient2" : QtGui.QBrush(QtGui.QColor(0,0,127,255),QtCore.Qt.SolidPattern) ,
#            "Gradient3" : QtGui.QBrush(QtGui.QColor(127,0,255,255),QtCore.Qt.SolidPattern) ,
#        } ,