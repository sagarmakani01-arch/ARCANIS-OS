"""REST API for ArcanisAutomation (Flask-optional).

If Flask is installed the :func:`create_app` returns a runnable WSGI app.
Otherwise the module still imports and exposes the engine wiring so the
endpoints can be adapted to any framework.
"""

from __future__ import annotations

from typing import Any, Optional

from arcanis_automation.config import AutomationConfig
from arcanis_automation.core.engine import AutomationEngine
from arcanis_automation.core.models import ExecutionResult


def create_app(config: Optional[AutomationConfig] = None) -> Any:
    try:
        from flask import Flask, request, jsonify  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Flask is required for the REST API. Install with `pip install flask`."
        ) from exc

    app = Flask("arcanis_automation")
    engine = AutomationEngine(config)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "workflows": len(engine.list_workflows())})

    @app.route("/workflows", methods=["GET"])
    def list_workflows():
        return jsonify([w.to_dict() for w in engine.list_workflows()])

    @app.route("/workflows", methods=["POST"])
    def create_workflow():
        wf = engine.create_workflow(request.get_json(force=True))
        return jsonify(wf.to_dict()), 201

    @app.route("/workflows/<wid>", methods=["GET"])
    def get_workflow(wid):
        wf = engine.get_workflow(wid)
        return (jsonify(wf.to_dict()), 200) if wf else (jsonify({"error": "not found"}), 404)

    @app.route("/workflows/<wid>", methods=["DELETE"])
    def delete_workflow(wid):
        engine.delete_workflow(wid)
        return jsonify({"deleted": wid})

    @app.route("/workflows/<wid>/trigger", methods=["POST"])
    def trigger_workflow(wid):
        ctx = request.get_json(force=True, silent=True) or {}
        results = engine.trigger(wid, ctx)
        return jsonify([r.to_dict() for r in results])

    @app.route("/generate", methods=["POST"])
    def generate():
        data = request.get_json(force=True)
        wf = engine.generate_workflow(data["description"])
        return jsonify(wf.to_dict()), 201

    @app.route("/workflows/<wid>/optimize", methods=["POST"])
    def optimize(wid):
        wf = engine.optimize_workflow(wid)
        return jsonify(wf.to_dict())

    @app.route("/workflows/<wid>/failures", methods=["GET"])
    def failures(wid):
        return jsonify(engine.detect_failures(wid))

    @app.route("/events", methods=["POST"])
    def emit_event():
        data = request.get_json(force=True)
        engine.emit_event(data["name"], data.get("data", {}))
        return jsonify({"dispatched": data["name"]})

    @app.route("/audit", methods=["GET"])
    def audit():
        return jsonify(engine.audit.read(int(request.args.get("limit", 200))))

    return app


def run_server(host: str = "127.0.0.1", port: int = 8080, **kwargs: Any) -> None:
    app = create_app()
    app.run(host=host, port=port, **kwargs)  # type: ignore[attr-defined]
