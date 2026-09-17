// Meridian HMS — shared interactive behaviour (no framework, vanilla JS)

document.addEventListener("DOMContentLoaded", () => {
  initInvoiceLineItems();
  initLabTestTotal();
  initAppointmentStatus();
});

/* Invoice builder: add / remove line item rows and keep the running total live */
function initInvoiceLineItems() {
  const container = document.getElementById("line-items");
  if (!container) return;
  const addBtn = document.getElementById("add-line-item");
  const totalEl = document.getElementById("invoice-total");

  function recalc() {
    let total = 0;
    container.querySelectorAll(".line-item-row").forEach((row) => {
      const qty = parseFloat(row.querySelector('[name="qty"]').value) || 0;
      const price = parseFloat(row.querySelector('[name="unit_price"]').value) || 0;
      total += qty * price;
    });
    if (totalEl) totalEl.textContent = "₹" + total.toFixed(2);
  }

  function bindRow(row) {
    row.querySelectorAll("input").forEach((inp) => inp.addEventListener("input", recalc));
    const removeBtn = row.querySelector(".remove-row");
    if (removeBtn) {
      removeBtn.addEventListener("click", () => {
        if (container.querySelectorAll(".line-item-row").length > 1) {
          row.remove();
          recalc();
        }
      });
    }
  }

  container.querySelectorAll(".line-item-row").forEach(bindRow);

  if (addBtn) {
    addBtn.addEventListener("click", () => {
      const template = container.querySelector(".line-item-row");
      const clone = template.cloneNode(true);
      clone.querySelectorAll("input").forEach((inp) => (inp.value = inp.name === "qty" ? 1 : ""));
      container.appendChild(clone);
      bindRow(clone);
    });
  }

  recalc();
}

/* Lab order builder: show a running count + estimated cost as tests are checked */
function initLabTestTotal() {
  const checklist = document.getElementById("test-checklist");
  if (!checklist) return;
  const countEl = document.getElementById("selected-count");
  const totalEl = document.getElementById("selected-total");

  function recalc() {
    const checked = checklist.querySelectorAll('input[type="checkbox"]:checked');
    let total = 0;
    checked.forEach((c) => (total += parseFloat(c.dataset.price || 0)));
    if (countEl) countEl.textContent = checked.length;
    if (totalEl) totalEl.textContent = "₹" + total.toFixed(2);
  }

  checklist.querySelectorAll('input[type="checkbox"]').forEach((c) => c.addEventListener("change", recalc));
  recalc();
}

/* Appointment list: update status inline without a full page reload */
function initAppointmentStatus() {
  document.querySelectorAll(".status-select").forEach((select) => {
    select.addEventListener("change", async () => {
      const apptId = select.dataset.apptId;
      const status = select.value;
      try {
        const res = await fetch(`/appointments/${apptId}/status`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: `status=${encodeURIComponent(status)}`,
        });
        if (!res.ok) throw new Error("Update failed");
        const pill = select.closest("tr").querySelector(".status-pill");
        if (pill) {
          pill.textContent = status;
          pill.className = "pill status-pill " + pillClassForStatus(status);
        }
      } catch (err) {
        alert("Could not update status. Please try again.");
      }
    });
  });
}

function pillClassForStatus(status) {
  switch (status) {
    case "Completed": return "pill-green";
    case "Cancelled": return "pill-red";
    case "Checked In": return "pill-blue";
    default: return "pill-amber";
  }
}
