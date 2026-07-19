from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus
from experience.ecosystem import EcosystemCoordinator


class ConceptCard(QFrame):
    clicked = Signal(str, str)

    def __init__(self, name, category="general", connections=0, parent=None):
        super().__init__(parent)
        self._concept_name = name
        self._category = category
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            ConceptCard {{
                background: {T.surface}; border: 1px solid {T.border_light};
                border-radius: 5px;
            }}
            ConceptCard:hover {{ border-color: {T.accent}; background: {T.accent_bg}; }}
        """)
        l = QVBoxLayout(self)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(3)
        self.name_lbl = QLabel(name)
        self.name_lbl.setStyleSheet(T.label_style() + f"font-size: {T.font_size_sm};")
        l.addWidget(self.name_lbl)
        row = QHBoxLayout()
        row.setSpacing(6)
        cat = QLabel(category.upper())
        cat.setStyleSheet(T.muted_style() + f"font-size: {T.font_size_xs};")
        row.addWidget(cat)
        conn = QLabel(f"{connections} links")
        conn.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_xs};")
        row.addWidget(conn)
        row.addStretch()
        l.addLayout(row)

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit(self._concept_name, self._category)
        super().mousePressEvent(event)


class KnowledgeGraphSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self.eco = EcosystemCoordinator()
        self._selected_concept = None
        self.update_interval(3000)

    def _init_content(self):
        l = QVBoxLayout(self.content)
        l.setContentsMargins(12, 8, 12, 12)
        l.setSpacing(6)

        summary_row = QHBoxLayout()
        self.nodes_label = QLabel("CONCEPTS: 0")
        self.nodes_label.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_sm}; color: {T.accent};")
        summary_row.addWidget(self.nodes_label)
        summary_row.addSpacing(16)
        self.edges_label = QLabel("RELATIONS: 0")
        self.edges_label.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_sm}; color: {T.purple};")
        summary_row.addWidget(self.edges_label)
        summary_row.addStretch()
        l.addLayout(summary_row)

        l.addSpacing(6)
        self.selected_label = QLabel("")
        self.selected_label.setStyleSheet(T.label_style() + f"font-size: {T.font_size_sm}; color: {T.accent};")
        self.selected_label.setVisible(False)
        l.addWidget(self.selected_label)

        l.addSpacing(6)
        hdr = QLabel("RECENT CONCEPTS")
        hdr.setStyleSheet(T.muted_style())
        l.addWidget(hdr)

        self.cards_container = QVBoxLayout()
        self.cards_container.setSpacing(4)
        l.addLayout(self.cards_container)

        self._refresh_concepts()

        l.addStretch()

    def _refresh_concepts(self, highlight=None):
        for i in reversed(range(self.cards_container.count())):
            w = self.cards_container.itemAt(i).widget()
            if w:
                w.deleteLater()

        concepts = self.eco.get_concepts()
        stats = self.eco.get_stats()
        self.nodes_label.setText(f"CONCEPTS: {stats.get('concepts', 0)}")
        self.edges_label.setText(f"RELATIONS: {stats.get('relations', 0)}")

        for c in concepts[:8]:
            card = ConceptCard(c["name"], c["category"], 0)
            card.clicked.connect(self._on_concept_clicked)
            if highlight and c["name"] == highlight:
                card.setStyleSheet(card.styleSheet() + f"ConceptCard {{ border-color: {T.accent}; background: {T.accent_bg}; }}")
            self.cards_container.addWidget(card)

    def _on_concept_clicked(self, name, category):
        self._selected_concept = name
        self.selected_label.setText(f"\u25B6 {name} ({category})")
        self.selected_label.setVisible(True)
        self._bus.emit(EventBus.CONCEPT_CREATED, {
            "name": name,
            "category": category,
            "source": self._surface_id,
        })
        self._bus.emit(EventBus.OBJECTIVE_UPDATE, {
            "objective": f"Exploring: {name}",
        })

    def _on_tick(self):
        self._refresh_concepts(self._selected_concept)

    def _setup_events(self):
        self._bus.subscribe(EventBus.KNOWLEDGE_UPDATED, self._on_knowledge)
        self._bus.subscribe(EventBus.CONCEPT_CREATED, self._on_concept_from_other)

    def _on_concept_from_other(self, event, data):
        name = data.get("name", "")
        source = data.get("source", "")
        if source != self._surface_id:
            self._selected_concept = name
            self.selected_label.setText(f"\u25B6 {name} (from {source})")
            self.selected_label.setVisible(True)
            self._refresh_concepts(name)

    def _on_knowledge(self, event, data):
        stats = self.eco.get_stats()
        self.nodes_label.setText(f"CONCEPTS: {stats.get('concepts', 0)}")
        self.edges_label.setText(f"RELATIONS: {stats.get('relations', 0)}")
