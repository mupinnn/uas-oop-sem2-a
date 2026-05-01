"""
purchase_order.py
-----------------
PurchaseOrder model — uses the State design pattern to manage its lifecycle.
"""

from __future__ import annotations

import datetime
import uuid
from typing import List, Optional

from .po_states import DraftState, POState, StatusEnum


class PurchaseOrder:
    """
    Represents a Purchase Order document.

    The PO delegates all state-dependent behaviour to its current POState object,
    following the State design pattern.
    """

    def __init__(
        self,
        requester: str,
        item_name: str,
        quantity: int,
        estimated_price: float,
        description: str = "",
    ) -> None:
        self.id: str = str(uuid.uuid4())
        self.requester: str = requester
        self.item_name: str = item_name
        self.quantity: int = quantity
        self.estimated_price: float = estimated_price
        self.description: str = description
        self.created_at: str = datetime.datetime.now().isoformat()
        self.updated_at: str = self.created_at

        # State management
        self._state: POState = DraftState()

        # Approval/rejection metadata
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[str] = None
        self.rejected_by: Optional[str] = None
        self.rejected_at: Optional[str] = None
        self.rejection_reason: Optional[str] = None

        # Assigned when the PO is completed
        self.po_number: Optional[str] = None

        # Audit trail
        self.history: List[dict] = []
        self._add_history(
            "CREATED",
            f"Purchase Order created by {requester} — status: DRAFT.",
        )

    # ------------------------------------------------------------------
    # Internal helpers used by state classes
    # ------------------------------------------------------------------

    def _transition_to(self, state: POState) -> None:
        self._state = state
        self.updated_at = datetime.datetime.now().isoformat()

    def _add_history(self, action: str, description: str) -> None:
        self.history.append(
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "action": action,
                "description": description,
            }
        )

    # ------------------------------------------------------------------
    # Public state-delegating methods
    # ------------------------------------------------------------------

    @property
    def status(self) -> StatusEnum:
        return self._state.status

    def submit(self) -> None:
        """Requester submits the PO for manager approval."""
        self._state.submit(self)

    def approve(self, manager: str) -> None:
        """Manager approves the PO."""
        self._state.approve(self, manager)

    def reject(self, manager: str, reason: str) -> None:
        """Manager rejects the PO with a mandatory reason."""
        self._state.reject(self, manager, reason)

    def complete(self) -> None:
        """System auto-completes the PO after approval."""
        self._state.complete(self)

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def total_price(self) -> float:
        return self.quantity * self.estimated_price

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "requester": self.requester,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "estimated_price": self.estimated_price,
            "total_price": self.total_price,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at,
            "rejection_reason": self.rejection_reason,
            "po_number": self.po_number,
            "history": self.history,
        }
