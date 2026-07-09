try:
    from flask import Flask, request, jsonify
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from arcanisdb.api.python_api import ArcanisAPI


class ArcanisRESTAPI:
    def __init__(self, db_path: str = ":memory:", encryption_key: str = None):
        if not HAS_FLASK:
            raise ImportError("Flask is required for the REST API. Install with: pip install flask")

        self.api = ArcanisAPI(db_path, encryption_key)
        self.app = Flask("ArcanisDatabase")
        self._register_routes()

    def _register_routes(self):
        app = self.app

        @app.route("/info", methods=["GET"])
        def info():
            return jsonify(self.api.info())

        @app.route("/collections", methods=["GET"])
        def list_collections():
            return jsonify(self.api.list_collections())

        @app.route("/collections", methods=["POST"])
        def create_collection():
            data = request.get_json()
            name = data.get("name")
            if not name:
                return jsonify({"error": "name required"}), 400
            schema = data.get("schema")
            result = self.api.create_collection(name, schema)
            return jsonify({"result": result}), 201

        @app.route("/collections/<name>", methods=["DELETE"])
        def drop_collection(name):
            self.api.drop_collection(name)
            return jsonify({"result": f"Collection '{name}' dropped"})

        @app.route("/collections/<name>/records", methods=["POST"])
        def insert_record(name):
            data = request.get_json()
            if isinstance(data, list):
                ids = self.api.insert_many(name, data)
                return jsonify({"ids": ids}), 201
            else:
                rid = self.api.insert(name, data)
                return jsonify({"id": rid}), 201

        @app.route("/collections/<name>/records/<int:rid>", methods=["GET"])
        def get_record(name, rid):
            record = self.api.get(name, rid)
            if record is None:
                return jsonify({"error": "not found"}), 404
            return jsonify(record)

        @app.route("/collections/<name>/records/<int:rid>", methods=["PUT"])
        def update_record(name, rid):
            data = request.get_json()
            success = self.api.update(name, rid, data)
            if not success:
                return jsonify({"error": "not found"}), 404
            return jsonify({"result": "updated"})

        @app.route("/collections/<name>/records/<int:rid>", methods=["DELETE"])
        def delete_record(name, rid):
            success = self.api.delete(name, rid)
            if not success:
                return jsonify({"error": "not found"}), 404
            return jsonify({"result": "deleted"})

        @app.route("/collections/<name>/query", methods=["GET"])
        def query_records(name):
            filters = request.args.get("filters")
            limit = request.args.get("limit", 100, type=int)
            offset = request.args.get("offset", 0, type=int)
            import json as j
            filters_dict = j.loads(filters) if filters else None
            results = self.api.query(name, filters_dict, limit, offset)
            return jsonify(results)

        @app.route("/kv/<collection>/<key>", methods=["GET"])
        def kv_get(collection, key):
            value = self.api.kv_get(collection, key)
            if value is None:
                return jsonify({"error": "not found"}), 404
            return jsonify({"key": key, "value": value})

        @app.route("/kv/<collection>/<key>", methods=["PUT"])
        def kv_set(collection, key):
            data = request.get_json()
            self.api.kv_set(collection, key, data.get("value"))
            return jsonify({"result": "set"})

        @app.route("/kv/<collection>/<key>", methods=["DELETE"])
        def kv_delete(collection, key):
            self.api.kv_delete(collection, key)
            return jsonify({"result": "deleted"})

        @app.route("/vectors/<collection>/search", methods=["POST"])
        def vector_search(collection):
            data = request.get_json()
            results = self.api.vector_search(
                collection,
                data["vector"],
                data.get("top_k", 10),
                data.get("metric", "cosine"),
            )
            return jsonify(results)

        @app.route("/vectors/<collection>", methods=["POST"])
        def vector_insert(collection):
            data = request.get_json()
            vid = self.api.vector_insert(
                collection,
                data["vector"],
                data.get("metadata"),
            )
            return jsonify({"id": vid}), 201

        @app.route("/embeddings/<collection>/search", methods=["POST"])
        def embed_search(collection):
            data = request.get_json()
            results = self.api.embed_search(
                collection,
                data["vector"],
                data.get("top_k", 10),
                data.get("metric", "cosine"),
            )
            return jsonify(results)

        @app.route("/retrieve/<collection>", methods=["POST"])
        def retrieve(collection):
            data = request.get_json()
            results = self.api.retrieve(
                collection,
                data["vector"],
                data.get("top_k", 5),
                data.get("min_score", 0.0),
            )
            return jsonify(results)

        @app.route("/query", methods=["POST"])
        def execute_query():
            data = request.get_json()
            result = self.api.query_ql(data["query"])
            return jsonify({"result": result})

        @app.route("/backup", methods=["POST"])
        def backup():
            data = request.get_json() or {}
            path = self.api.backup(data.get("path"))
            return jsonify({"path": path})

        @app.route("/restore", methods=["POST"])
        def restore():
            data = request.get_json()
            result = self.api.restore(data["path"])
            return jsonify({"result": result})

    def run(self, host: str = "127.0.0.1", port: int = 8653, debug: bool = False):
        self.app.run(host=host, port=port, debug=debug)

    def close(self):
        self.api.close()
