/**
 * app.js — Purchase Order Approval Workflow frontend
 *
 * Responsibilities:
 *  - Role switching (Requester / Manager)
 *  - CRUD calls to Flask REST API
 *  - Render PO lists & detail modal
 *  - Notification bell with polling
 */

/* =========================================================
   Helpers
   ========================================================= */

const API = {
  async get(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error((await res.json()).error || res.statusText);
    return res.json();
  },
  async post(url, body = {}) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  },
};

function fmtCurrency(n) {
  return "Rp " + Number(n).toLocaleString("id-ID");
}

function fmtDate(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusBadge(status) {
  const labels = {
    DRAFT: "Draft",
    PENDING_APPROVAL: "Pending Approval",
    APPROVED: "Approved",
    REJECTED: "Rejected",
    COMPLETED: "Completed",
  };
  return `<span class="status-badge status-${status}">${labels[status] || status}</span>`;
}

/* =========================================================
   Toast
   ========================================================= */

let _toast;
function showToast(msg, type = "success") {
  const el = document.getElementById("appToast");
  el.className = `toast align-items-center text-white border-0 bg-${type}`;
  document.getElementById("appToastBody").textContent = msg;
  if (!_toast) _toast = new bootstrap.Toast(el, { delay: 3500 });
  _toast.show();
}

/* =========================================================
   State
   ========================================================= */

let currentRole = "requester";   // "requester" | "manager"
let activePOId = null;           // PO being acted upon in a modal

/* =========================================================
   Role switching
   ========================================================= */

document.querySelectorAll('input[name="roleSwitch"]').forEach((radio) => {
  radio.addEventListener("change", (e) => {
    currentRole = e.target.value;
    document.getElementById("requesterView").classList.toggle("d-none", currentRole !== "requester");
    document.getElementById("managerView").classList.toggle("d-none", currentRole !== "manager");
    loadPOs();
    loadNotifications();
  });
});

/* =========================================================
   PO rendering helpers
   ========================================================= */

function renderPoItem(po) {
  const div = document.createElement("div");
  div.className = "po-item d-flex justify-content-between align-items-start";
  div.dataset.poId = po.id;
  div.innerHTML = `
    <div class="flex-grow-1 me-2">
      <div class="fw-semibold">${escHtml(po.item_name)}</div>
      <div class="text-muted small">
        <span>Qty: ${po.quantity}</span>
        <span class="mx-1">·</span>
        <span>${fmtCurrency(po.total_price)}</span>
        <span class="mx-1">·</span>
        <span>by ${escHtml(po.requester)}</span>
      </div>
      ${po.po_number ? `<div class="po-number-badge small mt-1">${escHtml(po.po_number)}</div>` : ""}
    </div>
    <div class="d-flex flex-column align-items-end gap-1">
      ${statusBadge(po.status)}
      <span class="text-muted" style="font-size:0.72rem">${fmtDate(po.updated_at)}</span>
    </div>
  `;
  div.addEventListener("click", () => openPoDetail(po.id));
  return div;
}

function renderEmpty(msg = "No purchase orders found.") {
  const div = document.createElement("div");
  div.className = "po-empty";
  div.innerHTML = `<i class="bi bi-inbox fs-2 d-block mb-2"></i>${msg}`;
  return div;
}

function escHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

/* =========================================================
   Load & render PO lists
   ========================================================= */

async function loadPOs() {
  try {
    const pos = await API.get("/api/pos");

    if (currentRole === "requester") {
      renderMyPos(pos);
    } else {
      renderPendingPos(pos.filter((p) => p.status === "PENDING_APPROVAL"));
      renderAllPos(pos);
    }
  } catch (err) {
    console.error("loadPOs:", err);
  }
}

function renderMyPos(pos) {
  const container = document.getElementById("myPoList");
  container.innerHTML = "";
  if (!pos.length) {
    container.appendChild(renderEmpty("You have no purchase orders yet."));
    return;
  }
  pos.slice().reverse().forEach((po) => container.appendChild(renderPoItem(po)));
}

function renderPendingPos(pos) {
  const container = document.getElementById("pendingPoList");
  container.innerHTML = "";
  if (!pos.length) {
    container.appendChild(renderEmpty("No pending approvals. ✓"));
    return;
  }
  pos.forEach((po) => {
    const item = renderPoItem(po);
    // Add quick-action buttons
    const actions = document.createElement("div");
    actions.className = "d-flex gap-2 mt-2";
    actions.innerHTML = `
      <button class="btn btn-sm btn-success approve-btn" data-po-id="${po.id}">
        <i class="bi bi-check-lg me-1"></i>Approve
      </button>
      <button class="btn btn-sm btn-danger reject-btn" data-po-id="${po.id}">
        <i class="bi bi-x-lg me-1"></i>Reject
      </button>
    `;
    // Stop propagation so clicking buttons doesn't open detail
    actions.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (btn.classList.contains("approve-btn")) openApproveModal(btn.dataset.poId);
        else openRejectModal(btn.dataset.poId);
      });
    });
    item.appendChild(actions);
    container.appendChild(item);
  });
}

function renderAllPos(pos) {
  const container = document.getElementById("allPoList");
  container.innerHTML = "";
  if (!pos.length) {
    container.appendChild(renderEmpty());
    return;
  }
  pos.slice().reverse().forEach((po) => container.appendChild(renderPoItem(po)));
}

/* =========================================================
   PO Detail Modal
   ========================================================= */

let _detailModal;

async function openPoDetail(poId) {
  try {
    const po = await API.get(`/api/pos/${poId}`);
    activePOId = po.id;

    const body = document.getElementById("poDetailBody");
    const footer = document.getElementById("poDetailFooter");

    body.innerHTML = buildDetailHTML(po);
    footer.innerHTML = buildDetailFooter(po);

    // Wire up footer buttons
    const submitBtn = footer.querySelector("#detailSubmitBtn");
    if (submitBtn) submitBtn.addEventListener("click", () => handleSubmit(po.id));

    const approveBtn = footer.querySelector("#detailApproveBtn");
    if (approveBtn) approveBtn.addEventListener("click", () => { _detailModal.hide(); openApproveModal(po.id); });

    const rejectBtn = footer.querySelector("#detailRejectBtn");
    if (rejectBtn) rejectBtn.addEventListener("click", () => { _detailModal.hide(); openRejectModal(po.id); });

    if (!_detailModal) _detailModal = new bootstrap.Modal(document.getElementById("poDetailModal"));
    _detailModal.show();
  } catch (err) {
    showToast(err.message, "danger");
  }
}

function buildDetailHTML(po) {
  const rows = [
    ["PO ID", `<code>${po.id}</code>`],
    ["Item Name", escHtml(po.item_name)],
    ["Quantity", po.quantity],
    ["Est. Unit Price", fmtCurrency(po.estimated_price)],
    ["Total Price", `<strong>${fmtCurrency(po.total_price)}</strong>`],
    ["Description", po.description ? escHtml(po.description) : "<em class='text-muted'>—</em>"],
    ["Status", statusBadge(po.status)],
    ["Requester", escHtml(po.requester)],
    ["Created At", fmtDate(po.created_at)],
    ["Last Updated", fmtDate(po.updated_at)],
  ];

  if (po.approved_by) {
    rows.push(["Approved By", escHtml(po.approved_by)]);
    rows.push(["Approved At", fmtDate(po.approved_at)]);
  }
  if (po.rejected_by) {
    rows.push(["Rejected By", escHtml(po.rejected_by)]);
    rows.push(["Rejected At", fmtDate(po.rejected_at)]);
    rows.push(["Rejection Reason", `<span class="text-danger">${escHtml(po.rejection_reason)}</span>`]);
  }
  if (po.po_number) {
    rows.push(["PO Number", `<span class="po-number-badge">${escHtml(po.po_number)}</span>`]);
  }

  const tableRows = rows.map(([k, v]) =>
    `<tr><th class="text-muted fw-normal" style="width:40%">${k}</th><td>${v}</td></tr>`
  ).join("");

  const historyHTML = po.history.map((h) => `
    <div class="history-step">
      <div class="fw-semibold small">${escHtml(h.action)}</div>
      <div class="text-muted small">${escHtml(h.description)}</div>
      <div class="text-muted" style="font-size:0.72rem">${fmtDate(h.timestamp)}</div>
    </div>
  `).join("");

  return `
    <table class="table table-sm table-borderless mb-4">
      <tbody>${tableRows}</tbody>
    </table>
    <h6 class="fw-semibold mb-3"><i class="bi bi-clock-history me-1"></i>History</h6>
    <div class="history-timeline">${historyHTML}</div>
  `;
}

function buildDetailFooter(po) {
  let html = `<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>`;

  if (currentRole === "requester" && po.status === "DRAFT") {
    html += `
      <button type="button" class="btn btn-primary" id="detailSubmitBtn">
        <i class="bi bi-send me-1"></i>Submit for Approval
      </button>`;
  }

  if (currentRole === "manager" && po.status === "PENDING_APPROVAL") {
    html += `
      <button type="button" class="btn btn-danger" id="detailRejectBtn">
        <i class="bi bi-x-circle me-1"></i>Reject
      </button>
      <button type="button" class="btn btn-success" id="detailApproveBtn">
        <i class="bi bi-check-circle me-1"></i>Approve
      </button>`;
  }

  return html;
}

/* =========================================================
   Submit
   ========================================================= */

async function handleSubmit(poId) {
  try {
    await API.post(`/api/pos/${poId}/submit`);
    if (_detailModal) _detailModal.hide();
    showToast("PO submitted for approval!");
    loadPOs();
    loadNotifications();
  } catch (err) {
    showToast(err.message, "danger");
  }
}

/* =========================================================
   Approve Modal
   ========================================================= */

let _approveModal;

function openApproveModal(poId) {
  activePOId = poId;
  document.getElementById("managerNameApprove").value = "";
  document.getElementById("approveError").classList.add("d-none");
  if (!_approveModal) _approveModal = new bootstrap.Modal(document.getElementById("approveModal"));
  _approveModal.show();
}

document.getElementById("confirmApproveBtn").addEventListener("click", async () => {
  const manager = document.getElementById("managerNameApprove").value.trim();
  const errEl = document.getElementById("approveError");
  errEl.classList.add("d-none");

  if (!manager) {
    errEl.textContent = "Manager name is required.";
    errEl.classList.remove("d-none");
    return;
  }

  try {
    await API.post(`/api/pos/${activePOId}/approve`, { manager });
    _approveModal.hide();
    showToast("Purchase Order approved and PO document issued!", "success");
    loadPOs();
    loadNotifications();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove("d-none");
  }
});

/* =========================================================
   Reject Modal
   ========================================================= */

let _rejectModal;

function openRejectModal(poId) {
  activePOId = poId;
  document.getElementById("managerNameReject").value = "";
  document.getElementById("rejectionReason").value = "";
  document.getElementById("rejectError").classList.add("d-none");
  if (!_rejectModal) _rejectModal = new bootstrap.Modal(document.getElementById("rejectModal"));
  _rejectModal.show();
}

document.getElementById("confirmRejectBtn").addEventListener("click", async () => {
  const manager = document.getElementById("managerNameReject").value.trim();
  const reason = document.getElementById("rejectionReason").value.trim();
  const errEl = document.getElementById("rejectError");
  errEl.classList.add("d-none");

  if (!manager) {
    errEl.textContent = "Manager name is required.";
    errEl.classList.remove("d-none");
    return;
  }
  if (!reason) {
    errEl.textContent = "Rejection reason is required.";
    errEl.classList.remove("d-none");
    return;
  }

  try {
    await API.post(`/api/pos/${activePOId}/reject`, { manager, reason });
    _rejectModal.hide();
    showToast("Purchase Order rejected.", "warning");
    loadPOs();
    loadNotifications();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove("d-none");
  }
});

/* =========================================================
   Create PO Form
   ========================================================= */

document.getElementById("createPoForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const errEl = document.getElementById("createPoError");
  errEl.classList.add("d-none");
  form.classList.add("was-validated");

  if (!form.checkValidity()) return;

  const payload = {
    requester: document.getElementById("requesterName").value.trim(),
    item_name: document.getElementById("itemName").value.trim(),
    quantity: parseInt(document.getElementById("quantity").value, 10),
    estimated_price: parseFloat(document.getElementById("estimatedPrice").value),
    description: document.getElementById("description").value.trim(),
  };

  try {
    await API.post("/api/pos", payload);
    form.reset();
    form.classList.remove("was-validated");
    showToast("Purchase Order saved as Draft!");
    loadPOs();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove("d-none");
  }
});

/* =========================================================
   Refresh buttons
   ========================================================= */

document.getElementById("refreshRequesterBtn").addEventListener("click", () => loadPOs());
document.getElementById("refreshManagerBtn").addEventListener("click", () => loadPOs());

/* =========================================================
   Notifications
   ========================================================= */

async function loadNotifications() {
  try {
    const notifications = await API.get(`/api/notifications?role=${currentRole}`);
    renderNotifications(notifications);
  } catch (err) {
    console.error("loadNotifications:", err);
  }
}

function renderNotifications(notifications) {
  const badge = document.getElementById("notifBadge");
  const list = document.getElementById("notifList");
  const emptyEl = document.getElementById("notifEmpty");

  // Remove old items (keep header items)
  list.querySelectorAll(".notif-item").forEach((el) => el.remove());

  const unread = notifications.filter((n) => !n.read);
  if (unread.length > 0) {
    badge.textContent = unread.length;
    badge.classList.remove("d-none");
  } else {
    badge.classList.add("d-none");
  }

  if (!notifications.length) {
    emptyEl.style.display = "";
    return;
  }

  emptyEl.style.display = "none";
  notifications.forEach((n) => {
    const li = document.createElement("li");
    li.className = `notif-item${n.read ? "" : " unread"}`;
    li.innerHTML = `
      <div class="fw-semibold">${escHtml(n.po_item)}</div>
      <div class="text-muted">${escHtml(n.message)}</div>
      <div class="text-muted" style="font-size:0.7rem">${fmtDate(n.timestamp)}</div>
    `;
    li.addEventListener("click", async () => {
      if (!n.read) {
        await API.post(`/api/notifications/${n.id}/read`);
        loadNotifications();
      }
    });
    list.appendChild(li);
  });
}

document.getElementById("clearNotifBtn").addEventListener("click", async (e) => {
  e.stopPropagation();
  await API.post("/api/notifications/clear");
  loadNotifications();
});

// Mark all unread as read when bell dropdown opens — single batch API call
document.getElementById("notifBell").addEventListener("show.bs.dropdown", async () => {
  const notifications = await API.get(`/api/notifications?role=${currentRole}`);
  const hasUnread = notifications.some((n) => !n.read);
  if (hasUnread) {
    await API.post("/api/notifications/read-all", { role: currentRole });
    loadNotifications();
  } else {
    renderNotifications(notifications);
  }
});

/* =========================================================
   Polling — refresh every 10 seconds
   ========================================================= */

setInterval(() => {
  loadPOs();
  loadNotifications();
}, 10000);

/* =========================================================
   Boot
   ========================================================= */

loadPOs();
loadNotifications();
