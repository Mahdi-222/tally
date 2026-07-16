const csvInput = document.getElementById("csvInput");
const uploadStatus = document.getElementById("uploadStatus");
const queueEl = document.getElementById("queue");
const emptyState = document.getElementById("emptyState");
const cardTemplate = document.getElementById("cardTemplate");
const queueHead = document.getElementById("queueHead");
const queueCount = document.getElementById("queueCount");

const BUCKET_LABELS = {
  silent: "Silent",
  engaged: "Engaged",
  repeat_offender: "Repeat Offender",
};

function strikeLevel(invoice) {
  // Visual strike count driven by reschedules on this invoice, capped at 3.
  return Math.min(invoice.reschedule_count, 3);
}

function renderQueue(invoices) {
  queueEl.innerHTML = "";
  emptyState.hidden = invoices.length > 0;
  queueHead.hidden = invoices.length === 0;
  queueCount.textContent =
    `${invoices.length} invoice${invoices.length === 1 ? "" : "s"}`;

  invoices.forEach((invoice) => {
    const node = cardTemplate.content.cloneNode(true);
    const card = node.querySelector(".card");

    const bucketTag = node.querySelector(".bucket-tag");
    bucketTag.textContent = BUCKET_LABELS[invoice.bucket] || invoice.bucket;

    const strikeBadge = node.querySelector(".strike-badge");
    const level = strikeLevel(invoice);
    strikeBadge.textContent = level > 0 ? `Strike ${level}` : "";
    strikeBadge.classList.add(`strike-${level}`);

    node.querySelector(".client-name").textContent = invoice.client_name;
    node.querySelector(".invoice-meta").textContent =
      `$${invoice.amount.toFixed(2)} · ${invoice.days_overdue} days overdue · due ${invoice.due_date}`;

    // Show who the message goes to — pulled from the billing export.
    const recipientEl = node.querySelector(".recipient");
    recipientEl.textContent = invoice.email ? `To: ${invoice.email}` : "No email on file";

    node.querySelector(".summary").textContent = invoice.summary;
    const messageEl = node.querySelector(".drafted-message");
    messageEl.value = invoice.drafted_message;

    const approveBtn = node.querySelector(".approve-btn");
    const approvedTag = node.querySelector(".approved-tag");
    approveBtn.addEventListener("click", () => {
      // Open the reviewer's own mail client with the message pre-filled.
      // We read the textarea live, so any edits the reviewer made are included.
      // A human still hits Send — deliberate for payment chasing.
      const subject = invoice.subject || `Invoice reminder — ${invoice.client_name}`;
      const body = messageEl.value;
      const to = invoice.email || "";
      const mailto =
        `mailto:${encodeURIComponent(to)}` +
        `?subject=${encodeURIComponent(subject)}` +
        `&body=${encodeURIComponent(body)}`;
      window.location.href = mailto;

      card.classList.add("is-approved");
      approvedTag.hidden = false;
    });

    queueEl.appendChild(node);
  });
}

csvInput.addEventListener("change", async () => {
  const file = csvInput.files[0];
  if (!file) return;

  uploadStatus.textContent = "Processing…";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/upload", { method: "POST", body: formData });
    if (!res.ok) throw new Error("Upload failed");
    const data = await res.json();

    renderQueue(data.invoices);

    const meta = data.meta;
    uploadStatus.textContent =
      `Last upload: ${meta.last_upload_time} · ${meta.last_upload_filename} · Upload #${meta.upload_count}`;
  } catch (err) {
    uploadStatus.textContent = "Upload failed — check the server logs.";
    console.error(err);
  }
});
