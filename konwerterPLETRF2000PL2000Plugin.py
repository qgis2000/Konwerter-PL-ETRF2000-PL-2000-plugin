# -*- coding: utf-8 -*-
# konwerterPLETRF2000PL2000Plugin.py       : The module converts coordinates from PL-ETRF2000 to PL-2000 - QGIS plugin in python
#     begin             : 2024-04-22
#     version           : 1.1.0
#.....version date......: 2024-06-20
#     author            : Szymon Kędziora

import re, os

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsPointXY,
    QgsCoordinateFormatter,
    QgsApplication
)

from qgis.PyQt.QtCore    import Qt, QLocale, pyqtSignal, QSettings, QRegExp

from qgis.PyQt.QtGui     import (
    QRegExpValidator,
    QFontMetrics,
    QValidator,
    QPalette,
    QKeySequence
)

from qgis.PyQt.QtWidgets import (
    QFrame,
    QDockWidget,
    QWidget,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QMessageBox,
    QTabWidget,
    QSizePolicy,
    QComboBox,
    QCheckBox,
    QMenuBar,
    QApplication
)

class MyLineEdit(QLineEdit):
    
    sigSelectAll=pyqtSignal()
    sigDelete=pyqtSignal()
    sigMoveCursorDown=pyqtSignal(int)
    sigMoveCursorUp=pyqtSignal(int)
    sigFocusIn=pyqtSignal(Qt.FocusReason)
    sigFocusOut=pyqtSignal(Qt.FocusReason)
    sigPaste=pyqtSignal()
    sigCopy=pyqtSignal()
    sigCut=pyqtSignal()
    sigKey_T=pyqtSignal()
    sigAlt_o=pyqtSignal()
    
    def __init__(self, parent):
        super(MyLineEdit,self).__init__(parent)
        
        self.lastCursorPosition=None
        self.cursorPositionChanged.connect(self.updateCursorPosition)
       
    def updateCursorPosition(self):
        self.lastCursorPosition=self.cursorPosition()
        
    def keyPressEvent(self,event):
        
        if not event.modifiers():
            if event.key()==Qt.Key_T:
                self.sigKey_T.emit()
                return
            
            if event.key()==Qt.Key_Down:
                self.sigMoveCursorDown.emit(self.cursorPosition())
                return
                
            if event.key()==Qt.Key_Up:
                self.sigMoveCursorUp.emit(self.cursorPosition())
                return
            
            if event.key()==Qt.Key_Delete or event.key()==Qt.Key_Backspace:
                super(MyLineEdit, self).keyPressEvent(event)
                self.sigDelete.emit()
                return
            
        if event.matches(QKeySequence.SelectAll):
            self.sigSelectAll.emit()
            return
            
        if event.matches(QKeySequence.Paste):
            self.sigPaste.emit()
            return
            
        if event.matches(QKeySequence.Copy):
            self.sigCopy.emit()
            return
            
        if event.matches(QKeySequence.Cut):
            self.sigCut.emit()
            return
            
        super(MyLineEdit, self).keyPressEvent(event)
        
    def focusInEvent(self,event):
        super(MyLineEdit, self).focusInEvent(event)
        self.sigFocusIn.emit(event.reason())
        
    def focusOutEvent(self,event):
        super(MyLineEdit, self).focusOutEvent(event)
        self.sigFocusOut.emit(event.reason())
        

class TwoLineEdit(QFrame):
    
    editingFinished=pyqtSignal()
    textChanged=pyqtSignal()
        
    def __init__(self, parent):
        super(TwoLineEdit,self).__init__(parent)

        self.readOnly=False

        self.separator=" "
        self.pattern="([\S]+)"
        self.format_wkt=False

        self.le1=MyLineEdit(self) 
        self.le2=MyLineEdit(self) 

        self.le1.setAlignment(Qt.AlignRight)
        self.le2.setAlignment(Qt.AlignRight)
        
        self.le1.setFrame(False)
        self.le2.setFrame(False)
        self.setFrameStyle(QFrame.Box)
        
        self.editingFinishedOnTab=False

        layout=QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        layout.addWidget(self.le1)
        layout.addWidget(self.le2)
        
        self.le1.sigSelectAll.connect(self.le1_sigSelectAll)
        self.le2.sigSelectAll.connect(self.le2_sigSelectAll)
        self.le1.sigDelete.connect(self.le1_sigDelete)
        self.le2.sigDelete.connect(self.le2_sigDelete)
        self.le1.sigMoveCursorDown.connect(self.le1_sigMoveCursorDown)
        self.le2.sigMoveCursorUp.connect(self.le2_sigMoveCursorUp)
        self.le1.sigFocusIn.connect(self.le1_sigFocusIn)
        self.le1.sigFocusOut.connect(self.le1_sigFocusOut)
        self.le2.sigFocusIn.connect(self.le2_sigFocusIn)
        self.le2.sigFocusOut.connect(self.le2_sigFocusOut)
        self.le1.sigPaste.connect(self.le1_sigPaste)
        self.le2.sigPaste.connect(self.le2_sigPaste)
        self.le1.sigCopy.connect(self.le1_sigCopy)
        self.le2.sigCopy.connect(self.le2_sigCopy)
        self.le1.sigCut.connect(self.le1_sigCut)
        self.le2.sigCut.connect(self.le2_sigCut)
        
        self.le1.setContextMenuPolicy(Qt.CustomContextMenu)
        self.le1.customContextMenuRequested.connect(self.le1_customContextMenuRequested)
        
        self.le2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.le2.customContextMenuRequested.connect(self.le2_customContextMenuRequested)
        
        self.le1.selectionChanged.connect(self.le1_selectionChanged)
        self.le2.selectionChanged.connect(self.le2_selectionChanged)
        
        self.le1.editingFinished.connect(self.le1_editingFinished)
        self.le2.editingFinished.connect(self.le2_editingFinished)
        
        self.le1.textChanged.connect(self.le1_textChanged)
        self.le2.textChanged.connect(self.le2_textChanged)
        
    def le1_customContextMenuRequested(self):
        menu=self.le1.createStandardContextMenu()
        for a in menu.actions():
            if "Ctrl+X" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le1_sigCut)
            if "Ctrl+C" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le1_sigCopy)
            if "Ctrl+V" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le1_sigPaste)
            if "Delete" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le1_sigDelete)
            if "Ctrl+A" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le1_sigSelectAll)
        menu.exec_(QCursor.pos())
        
    def le2_customContextMenuRequested(self):
        menu=self.le2.createStandardContextMenu()
        for a in menu.actions():
            if "Ctrl+X" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le2_sigCut)
            if "Ctrl+C" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le2_sigCopy)
            if "Ctrl+V" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le2_sigPaste)
            if "Delete" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le2_sigDelete)
            if "Ctrl+A" in a.text():
                a.triggered.disconnect()
                a.triggered.connect(self.le2_sigSelectAll)
        menu.exec_(QCursor.pos())
    
    def le1_sigCut(self):
        self.le1_sigCopy()
        self.le1.keyPressEvent(QKeyEvent(QEvent.KeyPress,Qt.Key_Delete,Qt.NoModifier))
        
    def le2_sigCut(self):
        if not self.readOnly:
            self.le2_sigCopy()
            self.le2.keyPressEvent(QKeyEvent(QEvent.KeyPress,Qt.Key_Delete,Qt.NoModifier))
    
    def le1_sigCopy(self):
        clipboard = QApplication.clipboard()
        clipboard.clear()
        if self.le2.hasSelectedText():
            if self.le1.hasSelectedText():
                text = self.le1.selectedText()+self.separator+self.le2.selectedText()
                clipboard.setText(text)
            else:
                self.le2.copy()
        else:
            self.le1.copy()
            
    def le2_sigCopy(self):
        clipboard = QApplication.clipboard()
        clipboard.clear()
        if self.le1.hasSelectedText():
            if self.le2.hasSelectedText():
                text = self.le1.selectedText()+self.separator+self.le2.selectedText()
                clipboard.setText(text)
            else:
                self.le1.copy()
        else:
            self.le2.copy()
    
    def le1_sigPaste(self):
        if not self.readOnly:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                m=re.fullmatch(self.pattern+self.separator+self.pattern,text)
                if m:
                    if self.le2.hasSelectedText():
                        self.le1.insert(m.group(1))
                        self.le2.insert(m.group(2))
                else:
                    self.le1.paste()
                
    def le2_sigPaste(self):
        if not self.readOnly:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                m=re.fullmatch(self.pattern+self.separator+self.pattern,text)
                if m:
                    if self.le1.hasSelectedText():
                        self.le1.insert(m.group(1))
                        self.le2.insert(m.group(2))
                else:
                    self.le2.paste()
    
    def le1_sigFocusIn(self,reason):
        pal=self.palette()
        color = pal.color(QPalette.Active, QPalette.Highlight)
        pal.setColor(QPalette.Foreground,color)
        self.setPalette(pal)
        if reason==Qt.TabFocusReason:
            if self.le1.inputMask():
                self.le1.selectAll()
            if self.le2.displayText():
                self.le2.selectAll()
    
    def le2_sigFocusIn(self,reason):
        pal=self.palette()
        color = pal.color(QPalette.Active, QPalette.Highlight)
        pal.setColor(QPalette.Foreground,color)
        self.setPalette(pal)
        if reason==Qt.BacktabFocusReason:
            if self.le2.inputMask():
                self.le2.selectAll()
            if self.le1.displayText():
                self.le1.selectAll()
    
    def le1_sigFocusOut(self,reason):
        self.setPalette(QFrame().palette())
        if not self.le2.hasFocus() and self.editingFinishedOnTab:
            if self.le2.text() and reason!=Qt.ActiveWindowFocusReason: 
                self.editingFinished.emit()
                self.editingFinishedOnTab=False
            
    def le2_sigFocusOut(self,reason):
        self.setPalette(QFrame().palette())
        if not self.le1.hasFocus() and self.editingFinishedOnTab:
            if self.le1.text() and reason!=Qt.ActiveWindowFocusReason: 
                self.editingFinished.emit()
                self.editingFinishedOnTab=False
            
    def le1_sigMoveCursorDown(self,pos):
        if self.le2.displayText():
            if self.le1.alignment()==Qt.AlignRight and self.le2.alignment()==Qt.AlignRight:
                self.le2.setFocus()
                le1_cursorPositionFromRight=len(self.le1.displayText())-self.le1.cursorPosition()
                if le1_cursorPositionFromRight>=len(self.le2.displayText()):
                    self.le2.setCursorPosition(0)
                else:
                    self.le2.setCursorPosition(len(self.le2.displayText())-le1_cursorPositionFromRight)
        else:
            self.le2.setFocus()
                
    def le2_sigMoveCursorUp(self,pos):
        if self.le1.displayText():
            if self.le1.alignment()==Qt.AlignRight and self.le2.alignment()==Qt.AlignRight:
                self.le1.setFocus()
                le2_cursorPositionFromRight=len(self.le2.displayText())-self.le2.cursorPosition()
                if le2_cursorPositionFromRight>=len(self.le1.displayText()):
                    self.le1.setCursorPosition(0)
                else:
                    self.le1.setCursorPosition(len(self.le1.displayText())-le2_cursorPositionFromRight)
        else:
            self.le1.setFocus()
    
    def le1_sigDelete(self):
        if self.le2.hasSelectedText():
            self.le2.del_()

    def le2_sigDelete(self):
        if self.le1.hasSelectedText():
            self.le1.del_()
            self.le1.setFocus()

    def focusNextPrevChild(self,next):
        if self.le1.hasFocus():
            if next:
                self.le2.setFocus(Qt.TabFocusReason)
        if self.le2.hasFocus():
            if not next:
                self.le1.setFocus(Qt.BacktabFocusReason)
        return super(TwoLineEdit,self).focusNextPrevChild(next)

    def le1_sigSelectAll(self):
        if self.le2.displayText():
            self.le2.selectAll()
        if self.le1.displayText():
            self.le1.selectAll()
    
    def le2_sigSelectAll(self):
        self.le1.setFocus()
        if self.le2.displayText():
            self.le2.selectAll()
        if self.le1.displayText():
            self.le1.selectAll()
        
    def le1_selectionChanged(self):
        if self.le1.displayText() and not self.le1.hasSelectedText():
            if self.le2.hasSelectedText():
                self.le2.blockSignals(True)
                self.le2.deselect()
                self.le2.blockSignals(False)
            
    def le2_selectionChanged(self):
        if self.le2.displayText() and not self.le2.hasSelectedText():
            if self.le1.hasSelectedText():
                self.le1.blockSignals(True)
                self.le1.deselect()
                self.le1.blockSignals(False)
        
    def le1_editingFinished(self):
        if self.le1.hasFocus(): 
            self.editingFinished.emit()
            self.editingFinishedOnTab=False
        else:
            self.editingFinishedOnTab=True
            
    def le2_editingFinished(self):
        if self.le2.hasFocus(): 
            self.editingFinished.emit()
            self.editingFinishedOnTab=False
        else:
            self.editingFinishedOnTab=True
            
    def le1_textChanged(self,str):
        if self.le2.hasSelectedText():
            self.le2.del_()
        self.textChanged.emit()
            
    def le2_textChanged(self,str):
        if self.le1.hasSelectedText():
            self.le1.del_()
        self.textChanged.emit()

    def setReadOnly(self,bool):
        self.le1.setReadOnly(bool)
        self.le2.setReadOnly(bool)
        self.readOnly=bool
    
    def setInputMask(self,str):
        self.le1.setInputMask(str)
        self.le2.setInputMask(str)
        
    def setValidator(self,validator):
        self.le1.setValidator(validator)
        self.le2.setValidator(validator)
        
    def setMaxLength(self,int):
        self.le1.setMaxLength(int)
        self.le2.setMaxLength(int)
       
    def setText(self,str1,str2):
        self.le1.setText(str1)
        self.le2.setText(str2)
            
    def clear(self):
        if self.le1.displayText():
            self.le1.clear()
        if self.le2.displayText():
            self.le2.clear()
    def hasFocus(self):
        return (self.le1.hasFocus() or self.le2.hasFocus())
    
class MyRegExpValidator(QRegExpValidator):
        def __init__(self):
            super().__init__()
            
        def validate(self,str,p):
            
            if self.locale().decimalPoint()==',':
                str=str.replace(".",",")
            if self.locale().decimalPoint()=='.':
                str=str.replace(",",".")
                
            return super().validate(str,p)

class PlEtrf2000_2LE(TwoLineEdit):
    
    def __init__(self,parent,locale):
        
        super(PlEtrf2000_2LE,self).__init__(parent)
        
        self.LOWER_DEG_DECI=8
        self.UPPER_DEG_DECI=10
        self.DEG_DMS_DIF=3
        
        self.LOWER_DMS_DECI=5
        self.UPPER_DMS_DECI=7
        self.DMS_DEG_DIF=4
        
        self.format_wkt=False
        self.reverse_order=False
        self._locale=locale
        
        
        self.format="deg"
        self.b_deg_text=None
        self.l_deg_text=None
        self.b_dms_text=None
        self.l_dms_text=None
        
        self.deg_validator=MyRegExpValidator()
        self.deg_validator.setLocale(self._locale)
        rx = QRegExp(f"\\d{{0,2}}[,.]?\\d{{0,{self.UPPER_DEG_DECI+1}}}")
        self.deg_validator.setRegExp(rx)
        self.setValidator(self.deg_validator)
        
        self.dms_validator=MyRegExpValidator()
        self.dms_validator.setLocale(self._locale)
        rx = QRegExp(f"\\d{{0,2}}[ °]?" \
                     f"\\d{{0,2}}[ ′']?" \
                     f"\\d{{0,2}}[,.]?\\d{{0,{self.UPPER_DMS_DECI}}}(″|'')?")
        self.dms_validator.setRegExp(rx)
        
        self.le1.sigCopy.disconnect()
        self.le2.sigCopy.disconnect()
        self.le1.sigCopy.connect(self.le1_sigCopy)
        self.le2.sigCopy.connect(self.le2_sigCopy)
        self.le1.sigPaste.disconnect()
        self.le2.sigPaste.disconnect()
        self.le1.sigPaste.connect(self.le1_sigPaste)
        self.le2.sigPaste.connect(self.le2_sigPaste)
        self.textChanged.connect(self.text_changed)
        self.le1.sigKey_T.connect(self.toggle_format)
        self.le2.sigKey_T.connect(self.toggle_format)
        
    def le1_sigCopy(self):
        clipboard = QApplication.clipboard()
        clipboard.clear()
        if self.le2.hasSelectedText():
            if self.le1.hasSelectedText():
                if self.reverse_order:
                    text = self.le2.selectedText()+self.separator+self.le1.selectedText()
                else:
                    text = self.le1.selectedText()+self.separator+self.le2.selectedText()
                clipboard.setText(text)
            else:
                self.le2.copy()
        else:
            self.le1.copy()
    
    def le2_sigCopy(self):
        self.le1_sigCopy()
    
    def le1_sigPaste(self):
         if not self.readOnly:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                if self.format=="deg":
                    m=re.match(self.pattern+self.separator+self.pattern,text)
                if self.format=="dms":
                    d_pattern="\d{1,2}[° ]"
                    m_pattern="(?:\d{1,2}[′' ])"   
                    s_pattern=f"(?:\d{{0,2}}[{self._locale.decimalPoint()}.,](?=\d)\d*|\d{{1,2}})(?:″|'')?"
                    pattern=f"({d_pattern}{m_pattern}{s_pattern})"
                    m=re.match(pattern+self.separator+pattern,text)
                if m:
                    if not self.le1.text() and not self.le2.text() \
                       or self.le1.hasSelectedText() and self.le2.hasSelectedText():
                        if self.reverse_order:
                            self.le1.insert(m.group(2))
                            self.le2.insert(m.group(1))
                        else:
                            self.le1.insert(m.group(1))
                            self.le2.insert(m.group(2))
                else:
                    self.le1.paste()
            
    def le2_sigPaste(self):
        if not self.readOnly:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                if self.format=="deg":
                    m=re.match(self.pattern+self.separator+self.pattern,text)
                if self.format=="dms":
                    d_pattern="\d{1,2}[° ]"
                    m_pattern="(?:\d{1,2}[′' ])"   
                    s_pattern=f"(?:\d{{0,2}}[{self._locale.decimalPoint()}.,](?=\d)\d*|\d{{1,2}})(?:″|'')?"
                    pattern=f"({d_pattern}{m_pattern}{s_pattern})"
                    m=re.match(pattern+self.separator+pattern,text)
                if m:
                    if not self.le1.text() and not self.le2.text() \
                       or self.le1.hasSelectedText() and self.le2.hasSelectedText():
                        if self.reverse_order:
                            self.le1.insert(m.group(2))
                            self.le2.insert(m.group(1))
                        else:
                            self.le1.insert(m.group(1))
                            self.le2.insert(m.group(2))
                else:
                    self.le2.paste()
        
    
    def text_changed(self):
        if self.format=="deg":
            self.b_deg_text=self.le1.text()
            self.l_deg_text=self.le2.text()
            self.b_dms_text=None
            self.l_dms_text=None
        if self.format=="dms":
            self.b_deg_text=None
            self.l_deg_text=None
            self.b_dms_text=self.le1.text()
            self.l_dms_text=self.le2.text()
                
    def toggle_format(self):
        if not self.le1.text() and self.le2.text() or \
               self.le1.text() and not self.le2.text():
            dlg=QMessageBox(self)
            dlg.setWindowTitle("Uwaga przed przełączeniem formatu")
            text=f"Należy podać obie współrzędne."
            dlg.setText(text)
            dlg.show()
            return
            
        if self.format=="dms":
            self.blockSignals(True)
            self.toggle_to_deg()
            self.blockSignals(False)
            if self.format=="dms":
                dlg=QMessageBox(self)
                dlg.setWindowTitle("Uwaga przed przełączeniem formatu na deg")
                text=f"Należy podać dwie cyfry stopni, minuty " \
                     f"oraz sekundy z {self.LOWER_DMS_DECI}-{self.UPPER_DMS_DECI} miejscami dziesiętnymi. " \
                     f"Stopnie, minuty i sekundy muszą być rozdzielone spacją albo odpowiednim " \
                     f"znakiem jednostek."
                dlg.setText(text)
                dlg.show()
            return
        if self.format=="deg":
            self.blockSignals(True)
            self.toggle_to_dms()
            self.blockSignals(False)
            if self.format=="deg":
                dlg=QMessageBox(self)
                dlg.setWindowTitle("Uwaga przed przełączeniem formatu na dms")
                text=f"Należy podać liczbę formatu dwie cyfry" \
                     f" z {self.LOWER_DEG_DECI}-{self.UPPER_DEG_DECI} miejscami dziesiętnymi."
                dlg.setText(text)
                dlg.show()
            
    def setLocale(self,locale):
        
        decimal_point=self._locale.decimalPoint()
        self._locale=locale
        self.deg_validator.setLocale(locale)
        self.dms_validator.setLocale(locale)
        
        if decimal_point!=locale.decimalPoint():
            
            self.blockSignals(True)
            
            if self.b_deg_text:
                self.b_deg_text=self.b_deg_text.replace(decimal_point,locale.decimalPoint())
            if self.l_deg_text:
                self.l_deg_text=self.l_deg_text.replace(decimal_point,locale.decimalPoint())
            if self.b_dms_text:
                self.b_dms_text=self.b_dms_text.replace(decimal_point,locale.decimalPoint())
            if self.l_dms_text:
                self.l_dms_text=self.l_dms_text.replace(decimal_point,locale.decimalPoint())
            if self.le1.text():
                text=self.le1.text().replace(decimal_point,locale.decimalPoint())
                self.le1.setText(text)
            if self.le2.text():
                text=self.le2.text().replace(decimal_point,locale.decimalPoint())
                self.le2.setText(text)
                
            self.blockSignals(False)
    
    def deg_text_to_deg(self,deg_text):
        decimalPoint=self._locale.decimalPoint()
        if deg_text:
            if self.b_dms_text or self.l_dms_text:
                pattern=f"\\d{{2}}[{decimalPoint}.,]" \
                        f"\\d{{{self.LOWER_DEG_DECI},{self.UPPER_DEG_DECI+1}}}"
            else:
                pattern=f"\\d{{2}}[{decimalPoint}.,]" \
                        f"\\d{{{self.LOWER_DEG_DECI},{self.UPPER_DEG_DECI}}}"
            m=re.fullmatch(pattern,deg_text)
            if m:
                deg=self._locale.toDouble(deg_text)[0]
                return deg
            else:
                return None
        else:
            return None
            
    def dms_text_to_parts(self,dms_text):
        decimalPoint=self._locale.decimalPoint()
        
        
        
        
        d_pattern="((\d{2})[° ])"
        m_pattern="((\d{1,2})[′' ])"
        s_pattern=f"(\d{{0,2}}[{decimalPoint}.,]\\d{{{self.LOWER_DMS_DECI},{self.UPPER_DMS_DECI}}})(″|'')?"
        pattern=f"{d_pattern}{m_pattern}{s_pattern}"
        
        m=re.fullmatch(pattern,dms_text)
            
        if m:
            d_text,m_text,s_text=m.group(2),m.group(4),m.group(5)
            return (d_text,m_text,s_text)
        else:
            return None
    
    def dms_parts_to_dms(self,dms_parts):
        d_text,m_text,s_text=dms_parts
        
        if d_text: d=float(d_text)
        else: d=0.0
        
        if m_text: m=float(m_text)
        else: m=0.0
        
        if s_text: s=self._locale.toDouble(s_text)[0]
        else: s=0.0
        
        return (d,m,s)
    
    def dms_to_deg(self,dms):
        d,m,s=dms
        deg=d+m/60+s/(60*60)
        return deg
    
    def dms_text_to_deg(self,dms_text):
        dms_parts=self.dms_text_to_parts(dms_text)
        if dms_parts:
            dms=self.dms_parts_to_dms(dms_parts)
            deg=self.dms_to_deg(dms)
            return deg
        else:
            return None
        
    def deg_b_to_dms_text(self,b,precision):
        dms_text=QgsCoordinateFormatter().formatY(
            b,
            QgsCoordinateFormatter().FormatDegreesMinutesSeconds,
            precision,
            QgsCoordinateFormatter().FlagDegreesPadMinutesSeconds
        )
        return dms_text
    
    def deg_l_to_dms_text(self,l,precision):
        dms_text=QgsCoordinateFormatter().formatX(
            l,
            QgsCoordinateFormatter().FormatDegreesMinutesSeconds,
            precision,
            QgsCoordinateFormatter().FlagDegreesPadMinutesSeconds
        )
        return dms_text
    

    def wyznacz_kod_strefy(self,lon,lat):
        if 14.14<=lon<=16.50:
            if 50.26<=lat<=55.35: return ("EPSG:2176",None)
            else: return (None,"Szerokość φ poza zakresem strefy 5.\nZakres 50,26-55,35.")
        if 16.50<lon<=19.50:
            if 49.39<=lat<=55.93: return ("EPSG:2177",None)
            else: return (None,"Szerokość φ poza zakresem strefy 6.\nZakres 49,39-55,93.")
        if 19.50<lon<=22.50:
            if 49.09<=lat<=54.55: return ("EPSG:2178",None)
            else: return (None,"Szerokość φ poza zakresem strefy 7.\nZakres 49,09-54,55.")
        if 22.50<lon<=24.15:
            if 49.00<=lat<=54.41: return ("EPSG:2179",None)
            else: return (None,"Szerokość φ poza zakresem strefy 8.\nZakres 49,00-54,41.")
        return (None,"Długość λ poza zakresem układu PL-ETRF2000.")

    def transformuj_punkt(self,pt):
        kod_strefy,komunikat = self.wyznacz_kod_strefy(pt.x(),pt.y())
        if kod_strefy:
            crs1 = QgsCoordinateReferenceSystem("EPSG:9702") 
            crs2 = QgsCoordinateReferenceSystem(kod_strefy)
            proj = QgsCoordinateTransform(crs1,crs2,QgsProject.instance())
            return (proj.transform(pt),kod_strefy,None)
        else:
            return (None,None,komunikat)
    def toggled_dms_values(self):
        if self.is_dms_entered():
            return self.b_dms_text,self.l_dms_text
        if self.is_deg_entered():
            b_deg=self.deg_text_to_deg(self.b_deg_text)
            l_deg=self.deg_text_to_deg(self.l_deg_text)
            if b_deg and l_deg:
                decimal_remainder1=self.b_deg_text.split(self._locale.decimalPoint())[1]
                len_decimal_remainder1=len(decimal_remainder1)
                dms_decimal1=len_decimal_remainder1-self.DEG_DMS_DIF
                decimal_remainder2=self.l_deg_text.split(self._locale.decimalPoint())[1]
                len_decimal_remainder2=len(decimal_remainder2)
                dms_decimal2=len_decimal_remainder2-self.DEG_DMS_DIF
                b_dms_text=self.deg_b_to_dms_text(b_deg,dms_decimal1)
                l_dms_text=self.deg_l_to_dms_text(l_deg,dms_decimal2)
                return b_dms_text,l_dms_text
        return None,None
        
    def toggle_to_dms(self):
        if not self.le1.text() and not self.le2.text():
            self.format="dms"
            self.setValidator(self.dms_validator)
            return
        b_dms_text,l_dms_text=self.toggled_dms_values()
        if b_dms_text and l_dms_text:
            self.format="dms"
            self.setValidator(self.dms_validator)
            self.setText(b_dms_text,l_dms_text)

    def toggled_deg_values(self):
        if self.is_deg_entered():
            return self.b_deg_text,self.l_deg_text
        if self.is_dms_entered():
            b_deg=self.dms_text_to_deg(self.b_dms_text)
            l_deg=self.dms_text_to_deg(self.l_dms_text)
            if b_deg and l_deg:
                self.b_dms_parts=self.dms_text_to_parts(self.b_dms_text)
                decimal_remainder1=self.b_dms_parts[2].split(self._locale.decimalPoint())[1]
                len_decimal_remainder1=len(decimal_remainder1)
                deg_decimal1=len_decimal_remainder1+self.DMS_DEG_DIF
                self.l_dms_parts=self.dms_text_to_parts(self.l_dms_text)
                decimal_remainder2=self.l_dms_parts[2].split(self._locale.decimalPoint())[1]
                len_decimal_remainder2=len(decimal_remainder2)
                deg_decimal2=len_decimal_remainder2+self.DMS_DEG_DIF
                b_deg_text=self._locale.toString(b_deg,'f',deg_decimal1)
                l_deg_text=self._locale.toString(l_deg,'f',deg_decimal2)
                return b_deg_text,l_deg_text
        return None,None
    
    def toggle_to_deg(self):
        if not self.le1.text() and not self.le2.text():
            self.format="deg"
            self.setValidator(self.deg_validator)
            return
        b_deg_text,l_deg_text=self.toggled_deg_values()
        if b_deg_text and l_deg_text:
            self.format="deg"
            self.setValidator(self.deg_validator)
            self.setText(b_deg_text,l_deg_text)
        
    def is_deg_entered(self):
        if self.b_deg_text and self.l_deg_text:
            return True
        else:
            return False
            
    def is_dms_entered(self):
        if self.b_dms_text and self.l_dms_text:
            return True
        else:
            return False
            
    def entered_decimal_parts(self):
        if self.is_deg_entered():
            return "deg",self.b_deg_text,self.l_deg_text
        if self.is_dms_entered():
            decimal_part1=self.dms_text_to_parts(self.b_dms_text)[2]
            decimal_part2=self.dms_text_to_parts(self.l_dms_text)[2]
            return "dms",decimal_part1,decimal_part2
        
class Pl2000_2LE(TwoLineEdit):
        
    def __init__(self, parent,locale):
        
        super(Pl2000_2LE,self).__init__(parent)
        
        self.format_wkt=False
        self.reverse_order=False
        self._locale=locale
        
        self.x=None
        self.y=None
        
        self.le1.sigCopy.disconnect()
        self.le2.sigCopy.disconnect()
        self.le1.sigCopy.connect(self.le1_sigCopy)
        self.le2.sigCopy.connect(self.le2_sigCopy)
        
    def le1_sigCopy(self):
        clipboard = QApplication.clipboard()
        clipboard.clear()
        if self.le2.hasSelectedText():
            if self.le1.hasSelectedText():
                if self.reverse_order:
                    text = self.le2.selectedText()+self.separator+self.le1.selectedText()
                else:
                    text = self.le1.selectedText()+self.separator+self.le2.selectedText()
                clipboard.setText(text)
            else:
                self.le2.copy()
        else:
            self.le1.copy()

    def le2_sigCopy(self):
        self.le1_sigCopy()

    def setLocale(self,locale):
            
        decimal_point=self._locale.decimalPoint()
        self._locale=locale

        if decimal_point!=self._locale.decimalPoint():
            if self.le1.text():
                x_text=self.le1.text().replace(decimal_point,self._locale.decimalPoint())
                self.le1.setText(x_text)
            if self.le2.text():
                y_text=self.le2.text().replace(decimal_point,self._locale.decimalPoint())
                self.le2.setText(y_text)
                
    def toDouble(self):
        d1=None
        d2=None
        if self.le1.text(): 
            d1=self._locale.toDouble(self.le1.text())[0]
        if self.le2.text():
            d2=self._locale.toDouble(self.le2.text())[0]
        return (d1,d2)
    
class MyDockWidget(QDockWidget):
    
    def __init__(self,title,parent,flags,settings):
        
        super(MyDockWidget,self).__init__(title,parent,flags)

        self.settings = settings
        
        self.locale=QLocale()
        
        self.setObjectName(title)
        self.title=title
 
        widget=QWidget(self)
        self.setWidget(widget) 
        layout=QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignHCenter)
        widget.setLayout(layout)
        
        self.tabs = QTabWidget(widget)
        self.tabs.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
        self.tabs.setFocusPolicy(Qt.NoFocus)
        self.tabKonwerter=self.tabKonwerter()
        self.tabs.addTab(self.tabKonwerter,"Konwerter")
        self.tabOpcje=self.tabUstawienia()
        self.tabs.addTab(self.tabOpcje,"Ustawienia")
        
        menu=QMenuBar(widget)
        menu.addAction("Pomoc", self.help)
        self.tabs.setCornerWidget(menu)
        
        layout.addWidget(self.tabs)
        layout.addStretch()
        
        self.pl_etrf2000_2le.le1.setFocus()
    
    def tabKonwerter(self):
        
        def pl_etrf2000_grBox(self,parent):
        
            layout = QGridLayout()
            layout.setAlignment(Qt.AlignTop)
            pl_etrf2000_grBox=QGroupBox("PL-ETRF2000 (EPSG:9702)",parent)
            pl_etrf2000_grBox.setFocusPolicy(Qt.NoFocus)
            pl_etrf2000_grBox.setLayout(layout)
            b_lab=QLabel("φ",pl_etrf2000_grBox)
            l_lab=QLabel("λ",pl_etrf2000_grBox)
            pl_etrf2000_2le=PlEtrf2000_2LE(pl_etrf2000_grBox,self.locale)
            pl_etrf2000_2le.setObjectName("pl_etrf2000_2le")
            self.b_units_lab=QLabel("°",pl_etrf2000_grBox)
            self.l_units_lab=QLabel("°",pl_etrf2000_grBox)
            w=QFontMetrics(self.b_units_lab.font()).width("° ’ ”")
            self.b_units_lab.setFixedWidth(w)
            self.l_units_lab.setFixedWidth(w)
            layout.addWidget(b_lab,0,0,Qt.AlignRight)
            layout.addWidget(l_lab,1,0,Qt.AlignRight)
            layout.addWidget(pl_etrf2000_2le,0,1,2,1)
            layout.addWidget(self.b_units_lab,0,2)
            layout.addWidget(self.l_units_lab,1,2)
            
            return pl_etrf2000_grBox,pl_etrf2000_2le
        
        def pl_2000_grBox(self,parent):
        
            layout = QGridLayout()
            pl_2000_grBox=QGroupBox("PL-2000",parent)
            pl_2000_grBox.setFocusPolicy(Qt.NoFocus)
            pl_2000_grBox.setLayout(layout)
            x_lab=QLabel("x",pl_2000_grBox)
            y_lab=QLabel("y",pl_2000_grBox)
            pl_2000_2le=Pl2000_2LE(pl_2000_grBox,self.locale)
            pl_2000_2le.setObjectName("pl_2000_2le")
            pl_2000_2le.setReadOnly(True)
            self.x_units_lab=QLabel("m",pl_2000_grBox)
            self.y_units_lab=QLabel("m",pl_2000_grBox)
            w=QFontMetrics(self.x_units_lab.font()).width("° ’ ”")
            self.x_units_lab.setFixedWidth(w)
            self.y_units_lab.setFixedWidth(w)
            layout.addWidget(x_lab,0,0,Qt.AlignRight)
            layout.addWidget(y_lab,1,0,Qt.AlignRight)
            layout.addWidget(pl_2000_2le,0,1,2,1)
            layout.addWidget(self.x_units_lab,0,2)
            layout.addWidget(self.y_units_lab,1,2)
            
            return pl_2000_grBox,pl_2000_2le
            
            
        def xy_round_accuracy(self,locale,format,decimal_part1,decimal_part2):
            decimal_remainder1=decimal_part1.split(locale.decimalPoint())[1]
            decimal_remainder2=decimal_part2.split(locale.decimalPoint())[1]
            len_decimal_remainder1=len(decimal_remainder1)
            len_decimal_remainder2=len(decimal_remainder2)
            if len_decimal_remainder1==len_decimal_remainder2:
                if format=="deg":
                    xy_decimal=len_decimal_remainder1-5
                    dx=float(f"2e-{xy_decimal}")
                    dy=float(f"1e-{xy_decimal}")
                    return xy_decimal,dx,dy
                if format=="dms":
                    xy_decimal=len_decimal_remainder1-1
                    dx=float(f"4e-{xy_decimal}")
                    dy=float(f"2e-{xy_decimal}")
                    return xy_decimal,dx,dy
            else:
                return None,None,None
        
        
        def xy_accuracy(self,locale,format,pt,decimal_part,pt_dms,pt_deg):
            xy_decimal=6
            decimal_remainder=decimal_part.split(locale.decimalPoint())[1]
            len_decimal_remainder=len(decimal_remainder)
            step=float(f"1e-{len_decimal_remainder}")
            if format=="deg":
                b_deg,l_deg=pt_deg
                b_deg_succ=b_deg+step
                l_deg_succ=l_deg+step
            if format=="dms":
                b_dms,l_dms=pt_dms
                b_dms_succ=list(b_dms)
                b_dms_succ[2]=b_dms_succ[2]+step
                b_dms_succ=tuple(b_dms_succ)
                l_dms_succ=list(l_dms)
                l_dms_succ[2]=l_dms_succ[2]+step
                l_dms_succ=tuple(l_dms_succ)
                b_deg_succ=self.pl_etrf2000_2le.dms_to_deg(b_dms_succ)
                l_deg_succ=self.pl_etrf2000_2le.dms_to_deg(l_dms_succ)
            pt_succ,kod_strefy,komunikat=self.pl_etrf2000_2le.transformuj_punkt(QgsPointXY(l_deg_succ,b_deg_succ))
            dx=pt_succ.y()-pt.y()
            dy=pt_succ.x()-pt.x()
            return xy_decimal,dx,dy
            
        def pl_etrf2000_2le_editingFinished(self):
            if not self.pl_etrf2000_2le.hasFocus() and not self.pl_2000_2le.hasFocus():
                return
                
            if not self.pl_etrf2000_2le.le1.text():
                dlg=QMessageBox(self)
                dlg.setWindowTitle("Uwaga")
                text=f"Należy podać współrzędną φ"
                dlg.setText(text)
                dlg.show()
                return
                
            if not self.pl_etrf2000_2le.le2.text():
                dlg=QMessageBox(self)
                dlg.setWindowTitle("Uwaga")
                text=f"Należy podać współrzędną λ"
                dlg.setText(text)
                dlg.show()
                return
            
            b_deg,l_deg=None,None
            
            str1=self.pl_etrf2000_2le.le1.text()
            str2=self.pl_etrf2000_2le.le2.text()
            locale=self.pl_etrf2000_2le._locale
            format=self.pl_etrf2000_2le.format
            LOWER_DEG_DECI=self.pl_etrf2000_2le.LOWER_DEG_DECI
            UPPER_DEG_DECI=self.pl_etrf2000_2le.UPPER_DEG_DECI
            LOWER_DMS_DECI=self.pl_etrf2000_2le.LOWER_DMS_DECI
            UPPER_DMS_DECI=self.pl_etrf2000_2le.UPPER_DMS_DECI
            
            if format=="deg":
                b_deg=self.pl_etrf2000_2le.deg_text_to_deg(str1)
                l_deg=self.pl_etrf2000_2le.deg_text_to_deg(str2)
                if not b_deg or not l_deg:
                    dlg=QMessageBox(self)
                    dlg.setWindowTitle("Uwaga")
                    text=f"Należy podać liczbę formatu dwie cyfry" \
                         f" z {LOWER_DEG_DECI}-{UPPER_DEG_DECI} miejscami dziesiętnymi."
                    dlg.setText(text)
                    dlg.show()
                    return
                    
            if format=="dms":
                b_dms_parts=self.pl_etrf2000_2le.dms_text_to_parts(str1)
                l_dms_parts=self.pl_etrf2000_2le.dms_text_to_parts(str2)
                if not b_dms_parts or not l_dms_parts:
                    dlg=QMessageBox(self)
                    dlg.setWindowTitle("Uwaga")
                    text=f"Należy podać dwie cyfry stopni, minuty " \
                         f"oraz sekundy z {LOWER_DMS_DECI}-{UPPER_DMS_DECI} miejscami dziesiętnymi. " \
                         f"Stopnie, minuty i sekundy muszą być rozdzielone spacją albo odpowiednim " \
                         f"znakiem jednostek."
                    dlg.setText(text)
                    dlg.show()
                    return
                if b_dms_parts and l_dms_parts:
                    b_dms=self.pl_etrf2000_2le.dms_parts_to_dms(b_dms_parts)
                    l_dms=self.pl_etrf2000_2le.dms_parts_to_dms(l_dms_parts)
                    b_deg=self.pl_etrf2000_2le.dms_to_deg(b_dms)
                    l_deg=self.pl_etrf2000_2le.dms_to_deg(l_dms)

            if b_deg and l_deg:
                ent_format,ent_decimal_part1,ent_decimal_part2=self.pl_etrf2000_2le.entered_decimal_parts()
                xy_decimal,dx,dy=xy_round_accuracy(self,locale,ent_format,ent_decimal_part1,ent_decimal_part2)
                if xy_decimal:
                    pt,kod_strefy,komunikat=self.pl_etrf2000_2le.transformuj_punkt(QgsPointXY(l_deg,b_deg))
                    if pt:
                        self.x=pt.y()
                        self.y=pt.x()
                        x_text=locale.toString(self.x,'f',xy_decimal)
                        y_text=locale.toString(self.y,'f',xy_decimal)
                        self.pl_2000_2le.setText(x_text,y_text)
                        self.pl_2000_grBox.setTitle("PL-2000 ("+kod_strefy+")")
                        dxmm_text=locale.toString(dx*1000)
                        dymm_text=locale.toString(dy*1000)
                        text=f"x±{dxmm_text}mm y±{dymm_text}mm"
                        self.label.setText(text)
                    else:
                        self.label.setText(komunikat)
                        self.pl_2000_grBox.setTitle("PL-2000")
                else:
                    dlg=QMessageBox(self)
                    dlg.setWindowTitle("Uwaga")
                    text=f"Obie współrzędne muszą mieć taką samą ilość miejsc dziesiętnych."
                    dlg.setText(text)
                    dlg.show()
                    
        
        def pl_etrf2000_2le_textChanged(self):
            
            if self.label.text(): self.label.clear()
            self.pl_2000_2le.clear()
            self.x=None
            self.y=None
            if self.pl_2000_grBox!="PL-2000": self.pl_2000_grBox.setTitle("PL-2000")
        
        def pl_etrf2000_2le_toggle_format(self):

            if self.pl_etrf2000_2le.format=="deg":
                self.b_units_lab.setText("°")
                self.l_units_lab.setText("°")
            if self.pl_etrf2000_2le.format=="dms":
                self.b_units_lab.setText("° ’ ”")
                self.l_units_lab.setText("° ’ ”")
            
            
            if self.label.text(): self.label.clear()
            self.pl_2000_2le.clear()
            if self.pl_2000_grBox!="PL-2000": self.pl_2000_grBox.setTitle("PL-2000")
        
        widget=QWidget(self)
        layout=QVBoxLayout(widget)
        widget.setLayout(layout)
        
        pl_etrf2000_grBox,self.pl_etrf2000_2le=pl_etrf2000_grBox(self,widget)
        self.pl_2000_grBox,self.pl_2000_2le=pl_2000_grBox(self,widget)
        self.pl_etrf2000_2le.editingFinished.connect(lambda: pl_etrf2000_2le_editingFinished(self))
        self.pl_etrf2000_2le.textChanged.connect(lambda: pl_etrf2000_2le_textChanged(self))
        self.label=QLabel(widget)
        self.label.setFixedHeight(2*self.label.sizeHint().height()+10) 
        self.label.setWordWrap(True)
        layout.addWidget(pl_etrf2000_grBox)
        layout.addWidget(self.pl_2000_grBox)
        layout.addWidget(self.label)
        layout.addStretch()

        self.pl_etrf2000_2le.le1.sigKey_T.connect(lambda: pl_etrf2000_2le_toggle_format(self))
        self.pl_etrf2000_2le.le2.sigKey_T.connect(lambda: pl_etrf2000_2le_toggle_format(self))
        
        return widget
    
    def tabUstawienia(self):
        
        def decimal_point_cmbbox_currentTextChanged(self):
            prev_locale=self.locale
            if self.decimal_point_cmbbox.currentText()=="kropka":
                self.settings.setValue('decimal_point_cmbbox',"kropka")
                self.locale=QLocale().c()
            if self.decimal_point_cmbbox.currentText()=="systemowy":
                self.settings.setValue('decimal_point_cmbbox',"systemowy")
                self.locale=QLocale()
            self.pl_etrf2000_2le.setLocale(self.locale)
            self.pl_2000_2le.setLocale(self.locale)
            label_text=self.label.text()
            if label_text and self.pl_2000_2le.le1.text() and self.pl_2000_2le.le2.text():
                label_text=label_text.replace(prev_locale.decimalPoint(),self.locale.decimalPoint())
                self.label.setText(label_text)
        
        def restore_default_settings(self):
            self.set_default_settings()
            read_settings(self)
        
        def read_settings(self):
            self.decimal_point_cmbbox.setCurrentText(self.settings.value('decimal_point_cmbbox'))
            self.coordinates_separator_cmbbox.setCurrentText(self.settings.value('copy_paste_coordinates_separator_cmbbox'))
            self.order_lb_chkbox.setChecked(self.settings.value('copy_paste_order_lb_chkbox',False,bool))
            self.order_yx_chkbox.setChecked(self.settings.value('copy_paste_order_yx_chkbox',False,bool))
        
        def copy_paste_grBox(self,parent):
            
            def order_lb_chkbox_stateChanged(self):
                self.pl_etrf2000_2le.reverse_order=self.order_lb_chkbox.isChecked()
                self.settings.setValue('copy_paste_order_lb_chkbox',self.order_lb_chkbox.isChecked())
                    
            def order_yx_chkbox_stateChanged(self):
                self.pl_2000_2le.reverse_order=self.order_yx_chkbox.isChecked()
                self.settings.setValue('copy_paste_order_yx_chkbox',self.order_yx_chkbox.isChecked())
                
            def coordinates_separator_cmbbox_currentTextChanged(self):
                if self.coordinates_separator_cmbbox.currentText()=="enter":
                    self.settings.setValue('copy_paste_coordinates_separator_cmbbox',"enter")
                    self.pl_etrf2000_2le.separator='\n'
                    self.pl_2000_2le.separator='\n'
                elif self.coordinates_separator_cmbbox.currentText()=="spacja":
                    self.settings.setValue('copy_paste_coordinates_separator_cmbbox',"spacja")
                    self.pl_etrf2000_2le.separator=' '
                    self.pl_2000_2le.separator=' '
                elif self.coordinates_separator_cmbbox.currentText()=="tab":
                    self.settings.setValue('copy_paste_coordinates_separator_cmbbox',"tab")
                    self.pl_etrf2000_2le.separator='\t'
                    self.pl_2000_2le.separator='\t'
            
            
            layout = QVBoxLayout()
            layout.setAlignment(Qt.AlignTop)
            copy_paste_grBox=QGroupBox("Kopiowanie i wklejanie",parent)
            copy_paste_grBox.setStyleSheet("font-weight: normal;")
            copy_paste_grBox.setFocusPolicy(Qt.NoFocus)
            copy_paste_grBox.setLayout(layout)
            
            order_lb_lab=QLabel("Kolejność λ φ",widget)
            self.order_lb_chkbox=QCheckBox(widget)
            self.order_lb_chkbox.stateChanged.connect(lambda: order_lb_chkbox_stateChanged(self))
            
            order_yx_lab=QLabel("Kolejność y x",widget)
            self.order_yx_chkbox=QCheckBox(widget)
            self.order_yx_chkbox.stateChanged.connect(lambda: order_yx_chkbox_stateChanged(self))
            
            coordinates_separator_lab=QLabel("Separator",widget)
            self.coordinates_separator_cmbbox=QComboBox(widget)
            self.coordinates_separator_cmbbox.addItems(["enter","spacja","tab"])
            self.coordinates_separator_cmbbox.setFixedSize(self.coordinates_separator_cmbbox.sizeHint())
            self.coordinates_separator_cmbbox.currentTextChanged.connect(lambda: coordinates_separator_cmbbox_currentTextChanged(self))
        
            layout1=QHBoxLayout()
            layout1.addWidget(order_lb_lab)
            layout1.addWidget(self.order_lb_chkbox)
            layout1.addWidget(order_yx_lab)
            layout1.addWidget(self.order_yx_chkbox)
            layout2=QHBoxLayout()
            layout2.addWidget(coordinates_separator_lab)
            layout2.addWidget(self.coordinates_separator_cmbbox)
            layout2.addStretch()
            layout2.addSpacing(10)
            layout.addLayout(layout1)
            layout.addLayout(layout2)
            
            return copy_paste_grBox
        
        widget=QWidget(self)
        layout=QVBoxLayout(widget)
        widget.setLayout(layout)
        
        self.decimal_point_cmbbox=QComboBox(widget)
        self.decimal_point_cmbbox.addItems(["kropka","systemowy"])
        self.decimal_point_cmbbox.setFixedSize(self.decimal_point_cmbbox.sizeHint())
        self.decimal_point_cmbbox.currentTextChanged.connect(lambda: decimal_point_cmbbox_currentTextChanged(self))
        
        self.copy_paste_grBox=copy_paste_grBox(self,widget)
        
        default_settings_pshbtn=QPushButton("Przywróć",widget)
        default_settings_pshbtn.clicked.connect(lambda: restore_default_settings(self))
        default_settings_pshbtn.setFixedSize(default_settings_pshbtn.sizeHint())
        
        decimal_point_lab=QLabel("Separator dzisiętny",widget)
        default_settings_lab=QLabel("Ustawienia domyślne",widget)
        
        read_settings(self)
        
        layout2=QHBoxLayout()
        layout2.addWidget(decimal_point_lab)
        layout2.addWidget(self.decimal_point_cmbbox,0,Qt.AlignLeft)
        layout4=QHBoxLayout()
        layout4.addWidget(default_settings_lab)
        layout4.addWidget(default_settings_pshbtn)
        layout4.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        layout.addLayout(layout2)
        layout.addWidget(self.copy_paste_grBox)
        layout.addStretch()
        layout.addLayout(layout4)
        layout.addStretch()
        
        return widget
        
    def help(self):

        dlg = QMessageBox(self)
        dlg.setWindowTitle(self.title + " Pomoc")

        p1="Program przelicza współrzędne punktu z układu PL-ETRF2000 do układu PL-2000.\n\n"

        p2="Może być przydatny przy opracowywaniu wyników pomiarów GNSS w odniesieniu do stacji " \
           "referencyjnych ASG-EPOS, gdzie współrzędne stacji podane są w układzie PL-ETRF2000. " \
           "Uzyskane z pomiarów współrzędne punktów w układzie PL-ETRF2000, po przeliczeniu " \
           "do układu PL-2000, można nanieść na mapę w układzie PL-2000 z granicami działek " \
           "i konturami budynków.\n\n "
        
        p3= "Program pozwala na wprowadzenie współrzędnych punktu układu\n" \
            "PL-ETRF2000 w dwóch formatach:\n\n" \
            "- stopniach (zwany także formatem dziesiętnym, formatem decimal, formatem deg albo dd),\n\n" \
            "- stopniach minutach sekundach (format dms).\n\n" \
            "Formaty przełącza się naciskając klawisz t. Można wprowadzić maksymalnie 10 miejsc " \
            "po przecinku dla formatu deg i maksymalnie 6 miejsc po przecinku sekund dla formatu dms. " \
            "Współrzędne wynikowe w układzie PL-2000 wyliczane są po wprowadzeniu współrzędnych PL-ETRF2000 " \
            "i naciśnięciu klawisza Tab albo Enter.\n\n" \
        
        p4= "PRZYKŁAD PRACY Z KONWERTEREM\n" \
            "W wyniku pomiaru uzyskano współrzędne punktu w układzie PL-ETRF2000 " \
            "szerokość φ=52,486491259 i długość λ=16,890655164 i wpisano do dowolnego edytora. " \
            "W edytorze zaznaczamy obie współrzędne 52,486491259 16,890655164 (rozdzielone spacją) i kopiujemy do schowka. " \
            "Przechodzimy do QGIS, gdzie pole φ λ powinno być otoczone cienką obwódką podświetlania w kolorze niebieskim. " \
            "Wklejamy skopiowane współrzędne. " \
            "Naciskamy kalwisz Tab aby wykonać obliczenia i przejść do pola x y.\n" \
            "W wyniku powinniśmy uzyskać:\n" \
            "- obok nazwy PL-2000 kod układu strefy EPSG:2177,\n" \
            "- współrzędne x=5817607,0999 i y=6424648,0600,\n" \
            "- możliwy błąd obliczeń: x±0,2mm y±0,1mm, oszacowany na podstawie ilości miejsc po przecinku " \
            "współrzędnych φ i λ.\n\n"
            
        p5= "KLAWISZE:\n" \
            "Tab albo Shift+Tab - przejście pomiędzy polami,\n" \
            "t - przełączenie między formatami współrzędnych PL-ETRF2000 jeśli kursor jest w linii φ albo λ,\n" \
            "Ctrl+a - zaznaczenie całego tekstu w polu,\n" \
            "strzałka góra albo strzałka dół - przejście pomiędzy liniami φ i λ\n\n" \
            
        p6="Uwaga W funkcjach QGIS współrzędne x y są odwrotnie niż w układzie PL-2000.\n\n"
        
            
        p8= "Separator dziesiętny - ustawia wyświetlany znak odzielający miejsca dziesiętne. Jeśli wybrany jest separator " \
            "systemowy, a w systemie jest ustawiony język polski, to separatorem będzie przecinek. " \
            "Niezależnie od tego ustawienia można wpisywać współrzędne z kropką albo przecinkiem.\n\n"
        
        p9= "Kolejność λ φ - kopiowanie do schowka lub wklejanie ze schowka współrzędnych w kolejności λ φ " \
            "zamiast φ λ.\n\n"
            
        p10="Kolejność y x - kopiowanie do schowka lub wklejanie ze schowka współrzędnych w kolejności y x " \
            "zamiast x y.\n\n"
            
        p11="Separator - znak wstawiany pomiędzy współrzędne " \
            "przy kopiowaniu dwóch współrzędnych do schowka.\n\n"
            
        p12="Ustawienia domyślne - kliknięcie przycisku Przywróć przywróci ustawienia domyślne programu."

        if self.tabs.currentIndex()==0:
            dlg.setText(p1+p2+p3+p4+p5+p6)
        else:
            dlg.setText(p8+p9+p10+p11+p12)
        dlg.show()
        
    def set_default_settings(self):
        self.settings.setValue('decimal_point_cmbbox',"systemowy")
        self.settings.setValue('copy_paste_coordinates_separator_cmbbox',"spacja")
        self.settings.setValue('copy_paste_order_lb_chkbox',False)
        self.settings.setValue('copy_paste_order_yx_chkbox',False)

class KonwerterPLETRF2000PL2000Plugin():

    def __init__(self, iface):
        self.iface = iface
        self.title='Konwerter PL-ETRF2000 PL-2000'
       
        self.settings = QSettings(QgsApplication.qgisSettingsDirPath()+"python/plugins/konwerterPLETRF2000PL2000Plugin/konwerterPLETRF2000PL2000Plugin.ini",QSettings.IniFormat)
        
    def initGui(self):
        self.myDockWidget=MyDockWidget(self.title,
                                       self.iface.mainWindow(),
                                       Qt.SubWindow,
                                       self.settings) 
        self.iface.mainWindow().addDockWidget(Qt.RightDockWidgetArea, self.myDockWidget)
        
    def unload(self):
        self.iface.removeDockWidget(self.myDockWidget)
        self.myDockWidget=None
        

