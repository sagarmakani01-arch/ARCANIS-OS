from __future__ import annotations
import json
from typing import Any, Dict, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship
from arcaniskg.query.executor import QueryExecutor, QueryExecutionError
from arcaniskg.query.traverser import GraphTraverser
from arcaniskg.visualization.renderer import GraphRenderer


class GraphAPIHandler(BaseHTTPRequestHandler):
    graph: Graph = Graph()
    executor: QueryExecutor = QueryExecutor(graph)
    traverser: GraphTraverser = GraphTraverser(graph)
    renderer: GraphRenderer = GraphRenderer(graph)

    def log_message(self, format, *args):
        pass

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        if path == "/api/status":
            self._send_json({
                "status": "ok",
                "nodes": self.graph.node_count,
                "relationships": self.graph.relationship_count,
                "version": "0.1.0",
            })

        elif path == "/api/nodes":
            nodes = [n.to_dict() for n in self.graph.nodes]
            self._send_json({"nodes": nodes})

        elif path.startswith("/api/nodes/"):
            node_id = path[11:]
            node = self.graph.get_node(node_id)
            if node:
                self._send_json({"node": node.to_dict()})
            else:
                self._send_json({"error": "Node not found"}, 404)

        elif path == "/api/relationships":
            rels = [r.to_dict() for r in self.graph.relationships]
            self._send_json({"relationships": rels})

        elif path.startswith("/api/relationships/"):
            rel_id = path[18:]
            rel = self.graph.get_relationship(rel_id)
            if rel:
                self._send_json({"relationship": rel.to_dict()})
            else:
                self._send_json({"error": "Relationship not found"}, 404)

        elif path == "/api/query":
            query = params.get("q", [None])[0]
            if query:
                try:
                    result = self.executor.execute(query)
                    self._send_json(result)
                except QueryExecutionError as e:
                    self._send_json({"error": str(e)}, 400)
            else:
                self._send_json({"error": "Missing query parameter 'q'"}, 400)

        elif path == "/api/graph/visualize":
            fmt = params.get("format", ["json"])[0]
            if fmt == "dot":
                self._send_json({"dot": self.renderer.to_dot()})
            elif fmt == "html":
                self._send_html(self.renderer.to_html())
            elif fmt == "visjs":
                self._send_json(self.renderer.to_visjs_json())
            else:
                self._send_json(self.renderer.to_cytoscape_json())

        elif path == "/api/graph/html":
            self._send_html(self.renderer.to_html())

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_body()

        if path == "/api/nodes":
            node = Node(
                id=body.get("id"),
                type=body.get("type", "generic"),
                properties=body.get("properties", {}),
            )
            self.graph.add_node(node)
            self._send_json({"node": node.to_dict()}, 201)

        elif path == "/api/relationships":
            rel = Relationship(
                source_id=body["source_id"],
                target_id=body["target_id"],
                type=body.get("type", "related_to"),
                id=body.get("id"),
                properties=body.get("properties", {}),
            )
            try:
                self.graph.add_relationship(rel)
                self._send_json({"relationship": rel.to_dict()}, 201)
            except ValueError as e:
                self._send_json({"error": str(e)}, 400)

        elif path == "/api/query":
            query = body.get("query", "")
            if query:
                try:
                    result = self.executor.execute(query)
                    self._send_json(result)
                except QueryExecutionError as e:
                    self._send_json({"error": str(e)}, 400)
            else:
                self._send_json({"error": "Missing 'query' in body"}, 400)

        elif path == "/api/ai/discover/shared":
            key = body.get("property_key", "")
            rel_type = body.get("relationship_type", "shares_property")
            created = self.graph.ai.discovery.discover_by_shared_property(key, rel_type)
            self._send_json({"created": len(created)})

        elif path == "/api/ai/discover/similarity":
            keys = body.get("property_keys", [])
            rel_type = body.get("relationship_type", "similar_to")
            threshold = body.get("threshold", 0.5)
            created = self.graph.ai.discovery.discover_by_property_similarity(
                keys, rel_type, threshold
            )
            self._send_json({"created": len(created)})

        elif path == "/api/ai/reasoning/transitive":
            rel_type = body.get("relationship_type", "related_to")
            max_hops = body.get("max_hops", 3)
            created = self.graph.ai.reasoning.deduce_transitive(rel_type, max_hops)
            self._send_json({"created": len(created)})

        elif path == "/api/ai/reasoning/rule":
            premise = body.get("premise_rel_type", "")
            conclusion = body.get("conclusion_rel_type", "")
            rule_name = body.get("rule_name", "inferred_rule")
            created = self.graph.ai.reasoning.apply_rule(premise, conclusion, rule_name)
            self._send_json({"created": len(created)})

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/nodes/"):
            node_id = path[11:]
            if self.graph.remove_node(node_id):
                self._send_json({"status": "deleted"})
            else:
                self._send_json({"error": "Node not found"}, 404)

        elif path.startswith("/api/relationships/"):
            rel_id = path[18:]
            if self.graph.remove_relationship(rel_id):
                self._send_json({"status": "deleted"})
            else:
                self._send_json({"error": "Relationship not found"}, 404)

        else:
            self._send_json({"error": "Not found"}, 404)


def serve(graph: Optional[Graph] = None, host: str = "127.0.0.1", port: int = 8080):
    if graph is not None:
        GraphAPIHandler.graph = graph
        GraphAPIHandler.executor = QueryExecutor(graph)
        GraphAPIHandler.traverser = GraphTraverser(graph)
        GraphAPIHandler.renderer = GraphRenderer(graph)
    server = HTTPServer((host, port), GraphAPIHandler)
    print(f"Graph API running at http://{host}:{port}")
    print(f"  GET  /api/status              - Server status")
    print(f"  GET  /api/nodes               - List all nodes")
    print(f"  POST /api/nodes               - Create a node")
    print(f"  GET  /api/nodes/<id>          - Get a node")
    print(f"  DELETE /api/nodes/<id>        - Delete a node")
    print(f"  GET  /api/relationships       - List all relationships")
    print(f"  POST /api/relationships       - Create a relationship")
    print(f"  GET  /api/relationships/<id>  - Get a relationship")
    print(f"  DELETE /api/relationships/<id>- Delete a relationship")
    print(f"  GET  /api/query?q=<query>     - Execute a query")
    print(f"  POST /api/query               - Execute a query (JSON body)")
    print(f"  GET  /api/graph/html          - Interactive visualization")
    print(f"  GET  /api/graph/visualize     - Graph data (json/dot/visjs)")
    print(f"  POST /api/ai/discover/*       - AI discovery endpoints")
    print(f"  POST /api/ai/reasoning/*      - AI reasoning endpoints")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()
