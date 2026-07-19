import os
import re

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSplitter,
    QTreeView, QPlainTextEdit, QToolBar, QPushButton,
    QMenu, QInputDialog, QWidget, QFileDialog,
    QFileSystemModel, QTextEdit,
)
from PySide6.QtCore import Qt, QModelIndex, QRect, QSize, Signal
from PySide6.QtGui import (
    QFont, QColor, QTextFormat, QPainter, QAction,
    QKeySequence, QSyntaxHighlighter, QTextCharFormat,
    QTextCursor,
)

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus


PROJECTS_ROOT = os.path.join(
    os.environ.get("USERPROFILE", "C:\\Users\\Sagar Makani"),
    "OneDrive", "ARCANIS LABS", ".ecosystem", "projects",
)


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#c678dd"))
        kw_fmt.setFontWeight(QFont.Bold)
        keywords = [
            "and", "as", "assert", "async", "await", "break", "class",
            "continue", "def", "del", "elif", "else", "except", "finally",
            "for", "from", "global", "if", "import", "in", "is", "lambda",
            "nonlocal", "not", "or", "pass", "raise", "return", "try",
            "while", "with", "yield", "True", "False", "None",
        ]
        for kw in keywords:
            self._rules.append((re.compile(r"\b" + kw + r"\b"), kw_fmt))

        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#98c379"))
        self._rules.append((re.compile(r"\"\"\".*?\"\"\"", re.MULTILINE), str_fmt))
        self._rules.append((re.compile(r"'''.*?'''", re.MULTILINE), str_fmt))
        self._rules.append((re.compile(r"\".*?\""), str_fmt))
        self._rules.append((re.compile(r"'.*?'"), str_fmt))

        com_fmt = QTextCharFormat()
        com_fmt.setForeground(QColor("#7f848e"))
        com_fmt.setFontItalic(True)
        self._rules.append((re.compile(r"#.*$"), com_fmt))

        dec_fmt = QTextCharFormat()
        dec_fmt.setForeground(QColor("#e5c07b"))
        self._rules.append((re.compile(r"@\w+"), dec_fmt))

        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#d19a66"))
        self._rules.append((re.compile(r"\b[0-9]+\b"), num_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor
        self.setFixedWidth(48)
        self.setCursor(Qt.ArrowCursor)

    def sizeHint(self):
        return QSize(48, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor("#282c34"))

        block = self._editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self._editor.blockBoundingGeometry(block)
                    .translated(self._editor.contentOffset()).top())
        bottom = top + round(self._editor.blockBoundingRect(block).height())

        cursor = self._editor.textCursor()
        current_line = cursor.blockNumber()
        mono_font = QFont(T.font_mono.split(",")[0].strip(), 10)
        mono_font.setStyleHint(QFont.Monospace)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                if block_number == current_line:
                    painter.setPen(QColor("#61afef"))
                elif block_number % 5 == 0:
                    painter.setPen(QColor("#5c6370"))
                else:
                    painter.setPen(QColor("#3e4452"))

                painter.setFont(mono_font)
                painter.drawText(
                    0, top, 44, self._editor.blockBoundingRect(block).height(),
                    Qt.AlignRight | Qt.AlignVCenter, number,
                )

            block = block.next()
            top = bottom
            bottom = top + round(self._editor.blockBoundingRect(block).height())

        painter.end()


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._highlighter = PythonSyntaxHighlighter(self.document())

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background: #1e2229;
                color: #abb2bf;
                border: none;
                font-family: '{T.font_mono}';
                font-size: 13px;
                padding: 4px 0px;
                selection-background-color: #3e4452;
            }}
        """)
        self.setTabStopDistance(
            QFontMetricsF(self.font()).horizontalAdvance(' ') * 4
        )
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._update_line_number_width()
        self._highlight_current_line()

    def _update_line_number_width(self):
        self.setViewportMargins(48, 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), 48, rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), 48, cr.height())
        )

    def _highlight_current_line(self):
        selections = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor("#2c313a"))
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            selections.append(sel)
        self.setExtraSelections(selections)


class ProjectWorkspaceSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self.update_interval(0)
        self._current_file = None

        self._ensure_projects_root()

    # ── Setup ──────────────────────────────────────────────────

    def _ensure_projects_root(self):
        if not os.path.isdir(PROJECTS_ROOT):
            try:
                os.makedirs(PROJECTS_ROOT, exist_ok=True)
            except Exception:
                pass

    def _init_content(self):
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {T.border.name()};
            }}
        """)

        # ── Left Panel: File Tree ─────────────────────────────
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        tree_header = QLabel("PROJECT FILES")
        tree_header.setStyleSheet(
            f"font-size: {T.font_size_xs}px; font-weight: 600; "
            f"color: {T.text_muted.name()}; letter-spacing: 1px; "
            f"font-family: '{T.font_family}'; "
            f"padding: 6px 10px; background: {T.surface_alt.name()};"
            f"border-bottom: 1px solid {T.border_light.name()};"
        )
        left_layout.addWidget(tree_header)

        self.model = QFileSystemModel()
        self.model.setRootPath(PROJECTS_ROOT)
        self.model.setFilter(
            Qt.DirFilter | Qt.FilesFilter | Qt.NoDotAndDotDot
        )

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(PROJECTS_ROOT))
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setHeaderHidden(True)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        self.tree.clicked.connect(self._on_tree_clicked)
        self.tree.setStyleSheet(f"""
            QTreeView {{
                background: transparent;
                border: none;
                outline: none;
                font-size: {T.font_size_sm}px;
                color: {T.text.name()};
            }}
            QTreeView::item {{
                padding: 3px 8px;
                border-radius: 0px;
            }}
            QTreeView::item:hover {{
                background: {T.surface_alt.name()};
            }}
            QTreeView::item:selected {{
                background: {T.accent_bg.name()};
                color: {T.accent.name()};
            }}
            QTreeView::branch {{
                background: transparent;
            }}
        """)
        left_layout.addWidget(self.tree)

        # ── Right Panel: Editor ───────────────────────────────
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background: {T.surface_alt.name()};
                border: none;
                border-bottom: 1px solid {T.border_light.name()};
                padding: 2px 4px;
                spacing: 4px;
            }}
        """)

        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedHeight(24)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T.accent.name()};
                color: #fff;
                border: none;
                border-radius: 3px;
                padding: 2px 12px;
                font-size: {T.font_size_xs}px;
                font-weight: 600;
                font-family: '{T.font_family}';
            }}
            QPushButton:hover {{
                background: {T.accent.darker(110).name()};
            }}
            QPushButton:disabled {{
                background: {T.border_light.name()};
                color: {T.text_muted.name()};
            }}
        """)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_file)
        toolbar.addWidget(self.save_btn)

        self.path_label = QLabel("No file open")
        self.path_label.setStyleSheet(
            f"font-size: {T.font_size_xs}px; color: {T.text_sec.name()}; "
            f"font-family: '{T.font_mono}'; padding: 0px 8px;"
        )
        toolbar.addWidget(self.path_label)
        toolbar.addStretch()

        right_layout.addWidget(toolbar)

        self.editor = CodeEditor()
        right_layout.addWidget(self.editor)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([240, 600])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        self._setup_shortcuts()

    def _setup_shortcuts(self):
        save_shortcut = QAction("Save", self)
        save_shortcut.setShortcut(QKeySequence.Save)
        save_shortcut.triggered.connect(self._save_file)
        self.addAction(save_shortcut)

    # ── Tree Context Menu ─────────────────────────────────────

    def _show_tree_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        menu = QMenu(self.tree)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {T.surface.name()};
                border: 1px solid {T.border.name()};
                padding: 4px 0px;
                font-size: {T.font_size_sm}px;
                font-family: '{T.font_family}';
                color: {T.text.name()};
            }}
            QMenu::item {{
                padding: 4px 24px;
            }}
            QMenu::item:selected {{
                background: {T.accent_bg.name()};
                color: {T.accent.name()};
            }}
            QMenu::separator {{
                height: 1px;
                background: {T.border_light.name()};
                margin: 4px 8px;
            }}
        """)

        new_file_action = menu.addAction("New File")
        new_folder_action = menu.addAction("New Folder")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        if index.isValid():
            path = self.model.filePath(index)
            if os.path.isfile(path):
                new_file_action.triggered.connect(
                    lambda: self._new_file(os.path.dirname(path))
                )
                new_folder_action.triggered.connect(
                    lambda: self._new_folder(os.path.dirname(path))
                )
                delete_action.triggered.connect(lambda: self._delete_path(path))
            else:
                new_file_action.triggered.connect(
                    lambda: self._new_file(path)
                )
                new_folder_action.triggered.connect(
                    lambda: self._new_folder(path)
                )
                delete_action.triggered.connect(lambda: self._delete_path(path))
        else:
            root = PROJECTS_ROOT
            new_file_action.triggered.connect(lambda: self._new_file(root))
            new_folder_action.triggered.connect(lambda: self._new_folder(root))
            delete_action.setEnabled(False)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _new_file(self, parent_dir):
        name, ok = QInputDialog.getText(
            self, "New File", "File name:"
        )
        if ok and name:
            path = os.path.join(parent_dir, name)
            if not os.path.exists(path):
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("")
                except Exception as e:
                    return
                self._bus.emit(EventBus.SYSTEM_EVENT, {
                    "message": f"Created file: {name}",
                    "source": self._surface_id,
                })

    def _new_folder(self, parent_dir):
        name, ok = QInputDialog.getText(
            self, "New Folder", "Folder name:"
        )
        if ok and name:
            path = os.path.join(parent_dir, name)
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    return
                self._bus.emit(EventBus.SYSTEM_EVENT, {
                    "message": f"Created folder: {name}",
                    "source": self._surface_id,
                })

    def _delete_path(self, path):
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                os.rmdir(path)
            self._bus.emit(EventBus.SYSTEM_EVENT, {
                "message": f"Deleted: {os.path.basename(path)}",
                "source": self._surface_id,
            })
            if self._current_file == path:
                self._current_file = None
                self.editor.clear()
                self.path_label.setText("No file open")
                self.save_btn.setEnabled(False)
        except Exception as e:
            pass

    # ── Tree Click → Open File ────────────────────────────────

    def _on_tree_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self._open_file(path)

    def _open_file(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.editor.setPlainText(content)
            self._current_file = path
            rel = os.path.relpath(path, PROJECTS_ROOT)
            self.path_label.setText(rel)
            self.save_btn.setEnabled(True)

            self._bus.emit(EventBus.SYSTEM_EVENT, {
                "message": f"Opened: {os.path.basename(path)}",
                "source": self._surface_id,
            })
        except Exception as e:
            self.path_label.setText(f"Error: {str(e)}")
            self.save_btn.setEnabled(False)

    # ── Save ──────────────────────────────────────────────────

    def _save_file(self):
        if not self._current_file:
            return
        try:
            content = self.editor.toPlainText()
            with open(self._current_file, "w", encoding="utf-8") as f:
                f.write(content)
            self._bus.emit(EventBus.SYSTEM_EVENT, {
                "message": f"Saved: {os.path.basename(self._current_file)}",
                "source": self._surface_id,
            })
        except Exception as e:
            self.path_label.setText(f"Save error: {str(e)}")

    # ── Events ────────────────────────────────────────────────

    def _setup_events(self):
        self._bus.subscribe(EventBus.SYSTEM_EVENT, self._on_system_event)

    def _on_system_event(self, event, data):
        pass
