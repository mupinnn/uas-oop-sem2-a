"""
app.py
------
Flask REST API for the Purchase Order Approval Workflow application.
"""

import os

from flask import Flask, jsonify, render_template, request

from models import WorkflowEngine, WorkflowError

app = Flask(__name__)
engine = WorkflowEngine.get_instance()


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Purchase Order API
# ---------------------------------------------------------------------------


@app.route("/api/pos", methods=["GET"])
def list_pos():
    """Return all purchase orders."""
    pos = engine.get_all_pos()
    return jsonify([po.to_dict() for po in pos])


@app.route("/api/pos", methods=["POST"])
def create_po():
    """Create a new PO in DRAFT status (Requester action)."""
    data = request.get_json(silent=True) or {}
    try:
        quantity = int(data.get("quantity", 0))
        estimated_price = float(data.get("estimated_price", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Quantity and estimated price must be valid numbers."}), 400
    try:
        po = engine.create_draft(
            requester=data.get("requester", ""),
            item_name=data.get("item_name", ""),
            quantity=quantity,
            estimated_price=estimated_price,
            description=data.get("description", ""),
        )
        return jsonify(po.to_dict()), 201
    except WorkflowError as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/pos/<po_id>", methods=["GET"])
def get_po(po_id):
    """Return a single PO by ID."""
    try:
        po = engine.get_po(po_id)
        return jsonify(po.to_dict())
    except KeyError:
        return jsonify({"error": "Purchase Order not found."}), 404


@app.route("/api/pos/<po_id>/submit", methods=["POST"])
def submit_po(po_id):
    """Submit a DRAFT PO for manager approval (Requester action)."""
    try:
        po = engine.submit(po_id)
        return jsonify(po.to_dict())
    except WorkflowError as exc:
        return jsonify({"error": str(exc)}), 400
    except KeyError:
        return jsonify({"error": "Purchase Order not found."}), 404


@app.route("/api/pos/<po_id>/approve", methods=["POST"])
def approve_po(po_id):
    """Approve a PENDING_APPROVAL PO (Manager action)."""
    data = request.get_json(silent=True) or {}
    try:
        po = engine.approve(po_id, manager=data.get("manager", ""))
        return jsonify(po.to_dict())
    except WorkflowError as exc:
        return jsonify({"error": str(exc)}), 400
    except KeyError:
        return jsonify({"error": "Purchase Order not found."}), 404


@app.route("/api/pos/<po_id>/reject", methods=["POST"])
def reject_po(po_id):
    """Reject a PENDING_APPROVAL PO (Manager action)."""
    data = request.get_json(silent=True) or {}
    try:
        po = engine.reject(
            po_id,
            manager=data.get("manager", ""),
            reason=data.get("reason", ""),
        )
        return jsonify(po.to_dict())
    except WorkflowError as exc:
        return jsonify({"error": str(exc)}), 400
    except KeyError:
        return jsonify({"error": "Purchase Order not found."}), 404


# ---------------------------------------------------------------------------
# Notifications API
# ---------------------------------------------------------------------------


@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    """Return notifications.  Pass ?role=manager or ?role=requester to filter."""
    role = request.args.get("role")
    return jsonify(engine.get_notifications(role=role))


@app.route("/api/notifications/<notification_id>/read", methods=["POST"])
def mark_read(notification_id):
    """Mark a single notification as read."""
    found = engine.mark_notification_read(notification_id)
    if found:
        return jsonify({"status": "ok"})
    return jsonify({"error": "Notification not found"}), 404


@app.route("/api/notifications/read-all", methods=["POST"])
def mark_all_read():
    """Mark all notifications as read for the given role (passed as JSON body)."""
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    engine.mark_all_notifications_read(role=role)
    return jsonify({"status": "ok"})


@app.route("/api/notifications/clear", methods=["POST"])
def clear_notifications():
    """Clear all notifications."""
    engine.clear_notifications()
    return jsonify({"status": "cleared"})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
