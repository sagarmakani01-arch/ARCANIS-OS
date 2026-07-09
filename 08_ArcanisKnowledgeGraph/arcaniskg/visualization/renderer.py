from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship


class GraphRenderer:
    def __init__(self, graph: Graph):
        self.graph = graph

    def to_dot(self, title: str = "KnowledgeGraph") -> str:
        lines = [f'digraph "{title}" {{', "  rankdir=LR;", "  node [shape=box, style=rounded];"]
        for node in self.graph.nodes:
            label = node.type
            if node.properties:
                prop_str = "\\n".join(
                    f"{k}: {v}" for k, v in list(node.properties.items())[:3]
                )
                label = f"{node.type}\\n---\\n{prop_str}"
            node_id = self._dot_id(node.id)
            lines.append(f'  {node_id} [label="{label}"];')
        for rel in self.graph.relationships:
            src = self._dot_id(rel.source_id)
            tgt = self._dot_id(rel.target_id)
            label = rel.type
            if rel.properties:
                extras = " ".join(
                    f"{k}={v}" for k, v in list(rel.properties.items())[:2]
                )
                label = f"{rel.type}\\n{extras}"
            lines.append(f'  {src} -> {tgt} [label="{label}"];')
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def _dot_id(id_str: str) -> str:
        safe = id_str.replace("-", "_").replace(".", "_")
        if safe and safe[0].isalpha():
            return safe
        return f"n_{safe}"

    def to_cytoscape_json(self) -> Dict[str, List[Dict[str, Any]]]:
        elements: Dict[str, List[Dict[str, Any]]] = {"nodes": [], "edges": []}
        for node in self.graph.nodes:
            elements["nodes"].append(
                {
                    "data": {
                        "id": node.id,
                        "type": node.type,
                        "label": node.type,
                        **node.properties,
                    }
                }
            )
        for rel in self.graph.relationships:
            elements["edges"].append(
                {
                    "data": {
                        "id": rel.id,
                        "source": rel.source_id,
                        "target": rel.target_id,
                        "label": rel.type,
                        "type": rel.type,
                        **{
                            k: v
                            for k, v in rel.properties.items()
                            if isinstance(v, (str, int, float, bool))
                        },
                    }
                }
            )
        return elements

    def to_d3_json(self) -> Dict[str, List[Dict[str, Any]]]:
        return self.to_cytoscape_json()

    def to_visjs_json(self) -> Dict[str, List[Dict[str, Any]]]:
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        for node in self.graph.nodes:
            nodes.append(
                {
                    "id": node.id,
                    "label": node.type,
                    "title": json.dumps(node.properties),
                    "group": node.type,
                }
            )
        for rel in self.graph.relationships:
            edges.append(
                {
                    "id": rel.id,
                    "from": rel.source_id,
                    "to": rel.target_id,
                    "label": rel.type,
                    "title": json.dumps(rel.properties),
                    "arrows": "to",
                }
            )
        return {"nodes": nodes, "edges": edges}

    def to_html(self, title: str = "Knowledge Graph") -> str:
        vis_data = self.to_visjs_json()
        vis_json = json.dumps(vis_data, indent=2)
        return f"""<!DOCTYPE html>
<html>
<head>
  <title>{title}</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.6/vis-network.min.js">
  </script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.6/dist/vis-network.min.css" />
  <style>
    body {{ margin: 0; padding: 0; }}
    #mynetwork {{ width: 100vw; height: 100vh; background: #f8f9fa; }}
  </style>
</head>
<body>
  <div id="mynetwork"></div>
  <script>
    const data = {vis_json};
    const container = document.getElementById('mynetwork');
    const options = {{
      physics: {{ stabilization: false }},
      edges: {{ smooth: {{ type: 'curvedCW' }} }},
      nodes: {{ shape: 'box', font: {{ size: 14 }} }}
    }};
    new vis.Network(container, data, options);
  </script>
</body>
</html>"""
