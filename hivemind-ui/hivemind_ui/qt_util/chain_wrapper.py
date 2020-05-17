from PySide2 import QtWidgets, QtCore, QtGui


class ChainingWrapper(object):
    def __init__(self, wrapped: QtWidgets.QWidget):
        self._wrapped = wrapped
        
    def get(self) -> QtWidgets.QWidget:
        return self._wrapped

    def setAcceptDrops(self, on: bool) -> 'ChainingWrapper':
        self._wrapped.setAcceptDrops(on)
        return self

    def setAccessibleDescription(self, description) -> 'ChainingWrapper':
        self._wrapped.setAccessibleDescription(description)
        return self

    def setAccessibleName(self, name: str) -> 'ChainingWrapper':
        self._wrapped.setAccessibleName(name)
        return self

    def setAttribute(self, arg__1: QtCore.Qt.WidgetAttribute, on: bool = True) -> 'ChainingWrapper':
        self._wrapped.setAttribute(arg__1, on=on)
        return self

    def setAutoFillBackground(self, enabled: bool) -> 'ChainingWrapper':
        self._wrapped.setAutoFillBackground(enabled)
        return self

    def setBackgroundRole(self, arg__1: QtGui.QPalette.ColorRole) -> 'ChainingWrapper':
        self._wrapped.setBackgroundRole(arg__1)
        return self

    def setBaseSize(self, *args) -> 'ChainingWrapper':
        """
        setBaseSize(self, arg__1: PySide2.QtCore.QSize)
        setBaseSize(self, basew: int, baseh: int)
        """
        self._wrapped.setBaseSize(*args)
        return self

    def setContentsMargins(self, *args) -> 'ChainingWrapper':
        """
        setContentsMargins(self, left: int, top: int, right: int, bottom: int)
        setContentsMargins(self, margins: PySide2.QtCore.QMargins)
        """
        self._wrapped.setContentsMargins(*args)
        return self

    def setContextMenuPolicy(self, policy: QtCore.Qt.ContextMenuPolicy) -> 'ChainingWrapper':
        self._wrapped.setContextMenuPolicy(policy)
        return self

    def setCursor(self, arg__1: QtGui.QCursor) -> 'ChainingWrapper':
        self._wrapped.setCursor(arg__1)
        return self

    def setDisabled(self, arg__1: bool) -> 'ChainingWrapper':
        self._wrapped.setDisabled(arg__1)
        return self

    def setEnabled(self, arg__1: bool) -> 'ChainingWrapper':
        self._wrapped.setEnabled(arg__1)
        return self

    def setFixedHeight(self, h: int) -> 'ChainingWrapper':
        self._wrapped.setFixedHeight(h)
        return self

    def setFixedSize(self, *args) -> 'ChainingWrapper':
        """
        setFixedSize(self, arg__1: PySide2.QtCore.QSize)
        setFixedSize(self, w: int, h: int)
        """
        self._wrapped.setFixedSize(*args)
        return self

    def setFixedWidth(self, w: int) -> 'ChainingWrapper':
        self._wrapped.setFixedWidth(w)
        return self

    def setFocus(self, *args) -> 'ChainingWrapper':
        """
        setFocus(self)
        setFocus(self, reason: PySide2.QtCore.Qt.FocusReason)
        """
        self._wrapped.setFocus(*args)
        return self

    def setFocusPolicy(self, policy: QtCore.Qt.FocusPolicy) -> 'ChainingWrapper':
        self._wrapped.setFocusPolicy(policy)
        return self

    def setFocusProxy(self, arg__1: QtWidgets.QWidget) -> 'ChainingWrapper':
        self._wrapped.setFocusProxy(arg__1)
        return self

    def setFont(self, arg__1: QtGui.QFont) -> 'ChainingWrapper':
        self._wrapped.setFont(arg__1)
        return self

    def setForegroundRole(self, arg__1: QtGui.QPalette.ColorRole) -> 'ChainingWrapper':
        self._wrapped.setForegroundRole(arg__1)
        return self

    def setGeometry(self, *args) -> 'ChainingWrapper':
        """
        setGeometry(self, arg__1: PySide2.QtCore.QRect)
        setGeometry(self, x: int, y: int, w: int, h: int)
        """
        self._wrapped.setGeometry(*args)
        return self

    def setGraphicsEffect(self, effect: QtWidgets.QGraphicsEffect) -> 'ChainingWrapper':
        self._wrapped.setGraphicsEffect(effect)
        return self

    def setHidden(self, hidden: bool) -> 'ChainingWrapper':
        self._wrapped.setHidden(hidden)
        return self

    def setInputMethodHints(self, hints: QtCore.Qt.InputMethodHints) -> 'ChainingWrapper':
        self._wrapped.setInputMethodHints(hints)
        return self

    def setLayout(self, arg__1: QtWidgets.QLayout) -> 'ChainingWrapper':
        self._wrapped.setLayout(arg__1)
        return self

    def setLayoutDirection(self, direction: QtCore.Qt.LayoutDirection) -> 'ChainingWrapper':
        self._wrapped.setLayoutDirection(direction)
        return self

    def setLocale(self, locale: QtCore.QLocale) -> 'ChainingWrapper':
        self._wrapped.setLocale(locale)
        return self

    def setMask(self, *args) -> 'ChainingWrapper':
        """
        setMask(self, arg__1: PySide2.QtGui.QBitmap)
        setMask(self, arg__1: PySide2.QtGui.QRegion)
        """
        self._wrapped.setMask(*args)
        return self

    def setMaximumHeight(self, maxh: int) -> 'ChainingWrapper':
        self._wrapped.setMaximumHeight(maxh)
        return self

    def setMaximumSize(self, *args) -> 'ChainingWrapper':
        """
        setMaximumSize(self, arg__1: PySide2.QtCore.QSize)
        setMaximumSize(self, maxw: int, maxh: int)
        """
        self._wrapped.setMaximumSize(*args)
        return self

    def setMaximumWidth(self, maxw: int) -> 'ChainingWrapper':
        self._wrapped.setMaximumWidth(maxw)
        return self

    def setMinimumHeight(self, minh: int) -> 'ChainingWrapper':
        self._wrapped.setMinimumHeight(minh)
        return self

    def setMinimumSize(self, *args) -> 'ChainingWrapper':
        """
        setMinimumSize(self, arg__1: PySide2.QtCore.QSize)
        setMinimumSize(self, minw: int, minh: int)
        """
        self._wrapped.setMinimumSize(*args)
        return self

    def setMinimumWidth(self, minw: int) -> 'ChainingWrapper':
        self._wrapped.setMinimumWidth(minw)
        return self

    def setMouseTracking(self, enable: bool) -> 'ChainingWrapper':
        self._wrapped.setMouseTracking(enable)
        return self

    def setPalette(self, arg__1: QtGui.QPalette) -> 'ChainingWrapper':
        self._wrapped.setPalette(arg__1)
        return self

    def setParent(self, *args) -> 'ChainingWrapper':
        """
        setParent(self, parent: PySide2.QtWidgets.QWidget)
        setParent(self, parent: PySide2.QtWidgets.QWidget, f: PySide2.QtCore.Qt.WindowFlags)
        """
        self._wrapped.setParent(*args)
        return self

    def setShortcutAutoRepeat(self, id: int, enable: bool = True) -> 'ChainingWrapper':
        self._wrapped.setShortcutAutoRepeat(id, enable=enable)
        return self

    def setShortcutEnabled(self, id: int, enable: bool = True) -> 'ChainingWrapper':
        self._wrapped.setShortcutEnabled(id, enable=enable)
        return self

    def setSizeIncrement(self, *args) -> 'ChainingWrapper':
        """
        setSizeIncrement(self, arg__1: PySide2.QtCore.QSize)
        setSizeIncrement(self, w: int, h: int)
        """
        self._wrapped.setSizeIncrement(*args)
        return self

    def setSizePolicy(self, *args) -> 'ChainingWrapper':
        """
        setSizePolicy(self, arg__1: PySide2.QtWidgets.QSizePolicy)
        setSizePolicy(self, horizontal: PySide2.QtWidgets.QSizePolicy.Policy, vertical: PySide2.QtWidgets.QSizePolicy.Policy)
        """
        self._wrapped.setSizePolicy(*args)
        return self

    def setStatusTip(self, arg__1: str) -> 'ChainingWrapper':
        self._wrapped.setStatusTip(arg__1)
        return self

    def setStyle(self, arg__1: QtWidgets.QStyle) -> 'ChainingWrapper':
        self._wrapped.setStyle(arg__1)
        return self

    def setStyleSheet(self, styleSheet: str) -> 'ChainingWrapper':
        self._wrapped.setStyleSheet(styleSheet)
        return self

    def setTabletTracking(self, enable: bool) -> 'ChainingWrapper':
        self._wrapped.setTabletTracking(enable)
        return self

    def setTabOrder(self, arg__1: QtWidgets.QWidget, arg__2: QtWidgets.QWidget) -> 'ChainingWrapper':
        self._wrapped.setTabOrder(arg__1, arg__2)
        return self

    def setToolTip(self, arg__1: str) -> 'ChainingWrapper':
        self._wrapped.setToolTip(arg__1)
        return self

    def setToolTipDuration(self, msec: int) -> 'ChainingWrapper':
        self._wrapped.setToolTipDuration(msec)
        return self

    def setUpdatesEnabled(self, enable: bool) -> 'ChainingWrapper':
        self._wrapped.setUpdatesEnabled(enable)
        return self

    def setVisible(self, visible: bool) -> 'ChainingWrapper':
        self._wrapped.setVisible(visible)
        return self

    def setWhatsThis(self, arg__1: str) -> 'ChainingWrapper':
        self._wrapped.setWhatsThis(arg__1)
        return self

    def setWindowFilePath(self, filePath: str) -> 'ChainingWrapper':
        self._wrapped.setWindowFilePath(filePath)
        return self

    def setWindowFlag(self, arg__1: QtCore.Qt.WindowType, on: bool = True) -> 'ChainingWrapper':
        self._wrapped.setWindowFlag(arg__1, on=on)
        return self

    def setWindowFlags(self, type: QtCore.Qt.WindowFlags) -> 'ChainingWrapper':
        self._wrapped.setWindowFlags(type)
        return self

    def setWindowIcon(self, icon: QtGui.QIcon) -> 'ChainingWrapper':
        self._wrapped.setWindowIcon(icon)
        return self

    def setWindowIconText(self, arg__1: str) -> 'ChainingWrapper':
        self._wrapped.setWindowIconText(arg__1)
        return self

    def setWindowModality(self, windowModality: QtCore.Qt.WindowModality) -> 'ChainingWrapper':
        self._wrapped.setWindowModality(windowModality)
        return self

    def setWindowModified(self, arg__1: bool) -> 'ChainingWrapper':
        self._wrapped.setWindowModified(arg__1)
        return self

    def setWindowOpacity(self, level: float) -> 'ChainingWrapper':
        self._wrapped.setWindowOpacity(level)
        return self

    def setWindowRole(self, arg__1: str) -> 'ChainingWrapper':
        self._wrapped.setWindowRole(arg__1)
        return self

    def setWindowState(self, state: QtCore.Qt.WindowStates) -> 'ChainingWrapper':
        self._wrapped.setWindowState(state)
        return self

    def setWindowTitle(self, arg__1: str) -> 'ChainingWrapper':
        self._wrapped.setWindowTitle(arg__1)
        return self

    # From QLabel
    def setAlignment(self, arg__1: QtCore.Qt.Alignment) -> 'ChainingWrapper':
        self._wrapped.setAlignment(arg__1)
        return self

    def setBuddy(self, arg__1: QtWidgets.QWidget) -> 'ChainingWrapper':
        self._wrapped.setBuddy(arg__1)
        return self

    def setIndent(self, arg__1: int) -> 'ChainingWrapper':
        self._wrapped.setIndent(arg__1)
        return self

    def setMargin(self, arg__1: int) -> 'ChainingWrapper':
        self._wrapped.setMargin(arg__1)
        return self

    def setMovie(self, movie: QtGui.QMovie) -> 'ChainingWrapper':
        self._wrapped.setMovie(movie)
        return self

    def setNum(self, *args) -> 'ChainingWrapper':
        """
        setNum(self, arg__1: float)
        setNum(self, arg__1: int)
        """
        self._wrapped.setNum(*args)
        return self

    def setOpenExternalLinks(self, open: bool) -> 'ChainingWrapper':
        self._wrapped.setOpenExternalLinks(open)
        return self

    def setPicture(self, arg__1: QtGui.QPicture) -> 'ChainingWrapper':
        self._wrapped.setPicture(arg__1)
        return self

    def setPixmap(self, arg__1: QtGui.QPixmap) -> 'ChainingWrapper':
        self._wrapped.setPixmap(arg__1)
        return self

    def setScaledContents(self, arg__1: bool) -> 'ChainingWrapper':
        self._wrapped.setScaledContents(arg__1)
        return self

    def setSelection(self, arg__1: int, arg__2: int) -> 'ChainingWrapper':
        self._wrapped.setSelection(arg__1, arg__2)
        return self

    def setText(self, arg__1: str) -> 'ChainingWrapper':
        self._wrapped.setText(arg__1)
        return self

    def setTextFormat(self, arg__1: QtCore.Qt.TextFormat) -> 'ChainingWrapper':
        self._wrapped.setTextFormat(arg__1)
        return self

    def setTextInteractionFlags(self, flags: QtCore.Qt.TextInteractionFlags) -> 'ChainingWrapper':
        self._wrapped.setTextInteractionFlags(flags)
        return self

    def setWordWrap(self, on: bool) -> 'ChainingWrapper':
        self._wrapped.setWordWrap(on)
        return self
