"""
po_states.py
------------
Implements the **State** design pattern for Purchase Order lifecycle.

States:
    DRAFT -> PENDING_APPROVAL -> APPROVED -> COMPLETED
                              -> REJECTED
"""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .purchase_order import PurchaseOrder


class StatusEnum(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class WorkflowError(Exception):
    """
    Application-level workflow / validation error.

    All messages carried by this exception are hardcoded, user-friendly strings
    defined within this package.  They are safe to surface directly to API clients.
    """


# ---------------------------------------------------------------------------
# Abstract base state
# ---------------------------------------------------------------------------

class POState(ABC):
    """Abstract base class for all Purchase Order states."""

    @property
    @abstractmethod
    def status(self) -> StatusEnum:
        pass

    # Default implementations raise errors for illegal transitions
    def submit(self, po: "PurchaseOrder") -> None:
        raise WorkflowError(
            f"Cannot submit a Purchase Order that is in '{self.status.value}' status."
        )

    def approve(self, po: "PurchaseOrder", manager: str) -> None:
        raise WorkflowError(
            f"Cannot approve a Purchase Order that is in '{self.status.value}' status."
        )

    def reject(self, po: "PurchaseOrder", manager: str, reason: str) -> None:
        raise WorkflowError(
            f"Cannot reject a Purchase Order that is in '{self.status.value}' status."
        )

    def complete(self, po: "PurchaseOrder") -> None:
        raise WorkflowError(
            f"Cannot complete a Purchase Order that is in '{self.status.value}' status."
        )

    def __str__(self) -> str:
        return self.status.value


# ---------------------------------------------------------------------------
# Concrete states
# ---------------------------------------------------------------------------

class DraftState(POState):
    """PO has been saved but not yet submitted for approval."""

    @property
    def status(self) -> StatusEnum:
        return StatusEnum.DRAFT

    def submit(self, po: "PurchaseOrder") -> None:
        # Re-validate before transitioning
        if not po.item_name or not po.item_name.strip():
            raise WorkflowError("Item name cannot be empty.")
        if po.quantity <= 0:
            raise WorkflowError("Quantity must be greater than zero.")
        if po.estimated_price <= 0:
            raise WorkflowError("Estimated price must be greater than zero.")

        po._transition_to(PendingApprovalState())
        po._add_history(
            "DRAFT → PENDING_APPROVAL",
            f"PO submitted by {po.requester} and is awaiting manager approval.",
        )


class PendingApprovalState(POState):
    """PO has been submitted and is waiting for a manager decision."""

    @property
    def status(self) -> StatusEnum:
        return StatusEnum.PENDING_APPROVAL

    def approve(self, po: "PurchaseOrder", manager: str) -> None:
        po.approved_by = manager
        po.approved_at = datetime.datetime.now().isoformat()
        po._transition_to(ApprovedState())
        po._add_history(
            "PENDING_APPROVAL → APPROVED",
            f"PO approved by {manager}.",
        )

    def reject(self, po: "PurchaseOrder", manager: str, reason: str) -> None:
        if not reason or not reason.strip():
            raise WorkflowError("A rejection reason must be provided.")
        po.rejected_by = manager
        po.rejection_reason = reason.strip()
        po.rejected_at = datetime.datetime.now().isoformat()
        po._transition_to(RejectedState())
        po._add_history(
            "PENDING_APPROVAL → REJECTED",
            f"PO rejected by {manager}. Reason: {reason}",
        )


class ApprovedState(POState):
    """PO has been approved; system will auto-complete it with a PO number."""

    @property
    def status(self) -> StatusEnum:
        return StatusEnum.APPROVED

    def complete(self, po: "PurchaseOrder") -> None:
        po._transition_to(CompletedState())
        po._add_history(
            "APPROVED → COMPLETED",
            f"Official PO document issued. PO Number: {po.po_number}",
        )


class RejectedState(POState):
    """PO has been rejected by the manager."""

    @property
    def status(self) -> StatusEnum:
        return StatusEnum.REJECTED


class CompletedState(POState):
    """PO has been fully processed and the official document issued."""

    @property
    def status(self) -> StatusEnum:
        return StatusEnum.COMPLETED
