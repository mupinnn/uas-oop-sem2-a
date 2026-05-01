"""
workflow_engine.py
------------------
WorkflowEngine — the central orchestrator for the PO approval workflow.

Design patterns used:
  • Singleton  — exactly one engine instance exists for the lifetime of the app.
  • Observer   — the engine notifies registered observers whenever a PO changes
                 state, decoupling notification logic from business logic.
"""

from __future__ import annotations

import datetime
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .po_states import StatusEnum, WorkflowError
from .purchase_order import PurchaseOrder


# ---------------------------------------------------------------------------
# Observer contract
# ---------------------------------------------------------------------------

class WorkflowObserver(ABC):
    """Abstract observer that receives workflow events."""

    @abstractmethod
    def on_event(self, event: str, po: PurchaseOrder, message: str) -> None:
        pass


# ---------------------------------------------------------------------------
# Concrete observer — in-memory notification store
# ---------------------------------------------------------------------------

class NotificationService(WorkflowObserver):
    """
    Stores workflow notifications in memory.
    Notifications are tagged with a target_role so the UI can filter them.
    """

    _ROLE_MAP: Dict[str, str] = {
        "PO_SUBMITTED": "manager",
        "PO_APPROVED": "requester",
        "PO_REJECTED": "requester",
        "PO_COMPLETED": "requester",
    }

    def __init__(self) -> None:
        self._store: List[dict] = []

    def on_event(self, event: str, po: PurchaseOrder, message: str) -> None:
        self._store.append(
            {
                "id": str(uuid.uuid4()),
                "event": event,
                "po_id": po.id,
                "po_item": po.item_name,
                "requester": po.requester,
                "message": message,
                "timestamp": datetime.datetime.now().isoformat(),
                "read": False,
                "target_role": self._ROLE_MAP.get(event, "all"),
            }
        )

    def get_all(self) -> List[dict]:
        return list(reversed(self._store))

    def get_for_role(self, role: str) -> List[dict]:
        return [n for n in reversed(self._store) if n["target_role"] in (role, "all")]

    def mark_read(self, notification_id: str) -> bool:
        for n in self._store:
            if n["id"] == notification_id:
                n["read"] = True
                return True
        return False

    def mark_all_read(self, role: Optional[str] = None) -> None:
        """Mark all notifications as read, optionally filtered by target role."""
        for n in self._store:
            if role is None or n["target_role"] in (role, "all"):
                n["read"] = True

    def clear(self) -> None:
        self._store.clear()


# ---------------------------------------------------------------------------
# Workflow Engine — Singleton
# ---------------------------------------------------------------------------

class WorkflowEngine:
    """
    Singleton workflow engine that orchestrates the entire PO lifecycle:

        create_draft → submit → approve/reject → (auto) complete

    It publishes events to all registered WorkflowObserver instances so that
    downstream services (e.g. notifications, audit logging) remain decoupled.
    """

    _instance: Optional[WorkflowEngine] = None

    # -- Singleton constructor ------------------------------------------------

    def __new__(cls) -> WorkflowEngine:
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instance = instance
        return cls._instance

    @classmethod
    def get_instance(cls) -> WorkflowEngine:
        return cls()

    def __init__(self) -> None:
        if self._initialized:
            return
        self._pos: Dict[str, PurchaseOrder] = {}
        self._po_counter: int = 0
        self._notification_service = NotificationService()
        self._observers: List[WorkflowObserver] = [self._notification_service]
        self._initialized = True

    # -- Observer management -------------------------------------------------

    def register_observer(self, observer: WorkflowObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: WorkflowObserver) -> None:
        self._observers.remove(observer)

    def _notify(self, event: str, po: PurchaseOrder, message: str) -> None:
        for observer in self._observers:
            observer.on_event(event, po, message)

    # -- PO number generation ------------------------------------------------

    def _generate_po_number(self) -> str:
        self._po_counter += 1
        date_tag = datetime.datetime.now().strftime("%Y%m%d")
        return f"PO-{date_tag}-{self._po_counter:04d}"

    # -- Workflow steps -------------------------------------------------------

    def create_draft(
        self,
        requester: str,
        item_name: str,
        quantity: int,
        estimated_price: float,
        description: str = "",
    ) -> PurchaseOrder:
        """
        **Phase 1 / Step 1 — Create Draft**
        Requester saves the PO.  Status: DRAFT.
        """
        if not requester or not requester.strip():
            raise WorkflowError("Requester name cannot be empty.")
        if not item_name or not item_name.strip():
            raise WorkflowError("Item name cannot be empty.")
        if quantity <= 0:
            raise WorkflowError("Quantity must be greater than zero.")
        if estimated_price <= 0:
            raise WorkflowError("Estimated price must be greater than zero.")

        po = PurchaseOrder(
            requester=requester.strip(),
            item_name=item_name.strip(),
            quantity=int(quantity),
            estimated_price=float(estimated_price),
            description=description.strip(),
        )
        self._pos[po.id] = po
        return po

    def submit(self, po_id: str) -> PurchaseOrder:
        """
        **Phase 1 / Step 2 — Submit Request**
        Requester submits the DRAFT PO.  Status: DRAFT → PENDING_APPROVAL.
        Notifies managers.
        """
        po = self._get_po(po_id)
        po.submit()  # state validates & transitions
        self._notify(
            "PO_SUBMITTED",
            po,
            (
                f"New purchase request from {po.requester}: "
                f"'{po.item_name}' × {po.quantity} "
                f"(est. Rp {po.total_price:,.0f}) is awaiting your approval."
            ),
        )
        return po

    def approve(self, po_id: str, manager: str) -> PurchaseOrder:
        """
        **Phase 2 / Step 4a — Approve**
        Manager approves.  Status: PENDING_APPROVAL → APPROVED → COMPLETED.
        System auto-issues PO number and notifies requester.
        """
        if not manager or not manager.strip():
            raise WorkflowError("Manager name cannot be empty.")
        po = self._get_po(po_id)
        po.approve(manager.strip())

        # Phase 3: system auto-generates PO number and completes the PO
        po.po_number = self._generate_po_number()
        po.complete()

        self._notify(
            "PO_APPROVED",
            po,
            (
                f"Your purchase request '{po.item_name}' has been approved by "
                f"{manager}. Official PO issued: {po.po_number}."
            ),
        )
        return po

    def reject(self, po_id: str, manager: str, reason: str) -> PurchaseOrder:
        """
        **Phase 2 / Step 4b — Reject**
        Manager rejects with a mandatory reason.
        Status: PENDING_APPROVAL → REJECTED.
        """
        if not manager or not manager.strip():
            raise WorkflowError("Manager name cannot be empty.")
        po = self._get_po(po_id)
        po.reject(manager.strip(), reason)
        self._notify(
            "PO_REJECTED",
            po,
            (
                f"Your purchase request '{po.item_name}' has been rejected by "
                f"{manager}. Reason: {reason}"
            ),
        )
        return po

    # -- Query helpers --------------------------------------------------------

    def get_all_pos(self) -> List[PurchaseOrder]:
        return list(self._pos.values())

    def get_po(self, po_id: str) -> PurchaseOrder:
        return self._get_po(po_id)

    def _get_po(self, po_id: str) -> PurchaseOrder:
        if po_id not in self._pos:
            raise KeyError(f"Purchase Order '{po_id}' not found.")
        return self._pos[po_id]

    # -- Notification helpers -------------------------------------------------

    def get_notifications(self, role: Optional[str] = None) -> List[dict]:
        if role:
            return self._notification_service.get_for_role(role)
        return self._notification_service.get_all()

    def mark_notification_read(self, notification_id: str) -> bool:
        return self._notification_service.mark_read(notification_id)

    def mark_all_notifications_read(self, role: Optional[str] = None) -> None:
        self._notification_service.mark_all_read(role=role)

    def clear_notifications(self) -> None:
        self._notification_service.clear()

    # -- Testing helper -------------------------------------------------------

    def reset(self) -> None:
        """Reset all in-memory state.  Useful in unit tests."""
        self._pos.clear()
        self._po_counter = 0
        self.clear_notifications()
