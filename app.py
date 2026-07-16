import os
import csv
import io
import json
from datetime import datetime

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

app = Flask(__name__)

# The Anthropic client reads ANTHROPIC_API_KEY from the environment automatically.
client = Anthropic()

MODEL = "claude-sonnet-5"

# In-memory state is fine for a local demo — no database needed.
state = {
    "last_upload_time": None,
    "last_upload_filename": None,
    "upload_count": 0,
}


def classify_invoice(row):
    """Three buckets: silent, engaged, repeat_offender.

    repeat_offender takes priority over the others — it exists specifically
    to close the loophole where a client (or a single invoice) could keep
    getting rescheduled forever and never actually pay.
    """
    reschedule_count = int(row["reschedule_count"])
    prior_late_invoices = int(row["prior_late_invoices"])
    ever_responded = row["ever_responded"].strip().lower() == "yes"

    if reschedule_count >= 3 or prior_late_invoices >= 2:
        return "repeat_offender"
    elif ever_responded:
        return "engaged"
    else:
        return "silent"


def priority_score(row):
    """Bigger, older invoices matter more. Used only to rank within a bucket —
    repeat_offender invoices are always surfaced first regardless of score,
    since those need a human judgment call, not just routine approval."""
    amount = float(row["amount"])
    days_overdue = int(row["days_overdue"])
    return amount * days_overdue


def generate_ai_content(invoice):
    """Calls Claude to produce two things per invoice:
    1. an internal, plain-English summary for the human reviewer (history-aware)
    2. the actual drafted message to the client (never cites their history back
       to them — see the tone rules below)
    """
    prompt = f"""You are helping an accounts receivable team follow up on unpaid invoices.

Invoice details:
- Client: {invoice['client_name']}
- Amount: ${invoice['amount']:.2f}
- Days overdue: {invoice['days_overdue']}
- Bucket: {invoice['bucket']}
- Times this invoice has already been rescheduled: {invoice['reschedule_count']}
- This client's count of prior late invoices (history, not this one): {invoice['prior_late_invoices']}

Return ONLY a valid JSON object with exactly three fields, "summary", "subject", and "drafted_message". No other text, no markdown fences.

"summary": one sentence, for an internal reviewer only, plain English, that can reference the client's history if relevant (e.g. "third reschedule on this one" or "no history of lateness before this").

"subject": a short, professional email subject line for this follow-up (e.g. "Invoice reminder — Acme Co" or "Following up on your overdue invoice"). No history references.

"drafted_message": the actual follow-up message that would be sent to the client. Rules:
- Never mention the client's past lateness or reschedule history explicitly. The client should never see a reference to their own track record.
- Match the tone to the bucket:
  - silent (never responded): low-pressure, friendly, no accusation. Include a line offering to pick a new due date via this placeholder link: [RESCHEDULE_LINK]
  - engaged (has responded before, still unpaid): a bit firmer, may acknowledge that they've been in touch before in a general way, but must NOT quote or invent a specific past message (we don't have the text of it). Still include [RESCHEDULE_LINK]
  - repeat_offender: direct, ask for a firm commitment or partial payment today. Do NOT include a reschedule link or offer to reschedule.
- Keep it under 80 words.
- Sign off as "The Amigo Accounts Team"."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )

        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text = block.text.strip()
                break

        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)
        # Make sure all three fields are present; fall back on any that aren't.
        return {
            "summary": data.get("summary", "").strip() or "Follow-up needed — review before sending.",
            "subject": data.get("subject", "").strip() or f"Invoice reminder — {invoice['client_name']}",
            "drafted_message": data.get("drafted_message", "").strip()
            or "Hi,\n\nWe're following up on your overdue invoice. Please let us know how you'd like to proceed.\n\nThe Amigo Accounts Team",
        }
    except Exception as e:
        # One bad row must never take down the whole upload. Log it and hand back
        # a safe placeholder the reviewer can edit, so the queue still renders.
        print(f"  ! AI generation failed for {invoice['client_name']}: {e}")
        return {
            "summary": "Could not auto-draft — please write this one manually.",
            "subject": f"Invoice reminder — {invoice['client_name']}",
            "drafted_message": "Hi,\n\nWe're following up on your overdue invoice. Please let us know how you'd like to proceed.\n\nThe Amigo Accounts Team",
        }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    content = file.stream.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    invoices = []
    for row in reader:
        bucket = classify_invoice(row)
        invoice = {
            "client_name": row["client_name"],
            # Email comes from the same billing export as everything else —
            # the system that sent the invoice already has it on file.
            "email": row.get("email", "").strip(),
            "amount": float(row["amount"]),
            "due_date": row["due_date"],
            "days_overdue": int(row["days_overdue"]),
            "reschedule_count": int(row["reschedule_count"]),
            "prior_late_invoices": int(row["prior_late_invoices"]),
            "bucket": bucket,
            "priority_score": priority_score(row),
        }
        ai_content = generate_ai_content(invoice)
        invoice["summary"] = ai_content["summary"]
        invoice["subject"] = ai_content["subject"]
        invoice["drafted_message"] = ai_content["drafted_message"]
        invoices.append(invoice)

    # repeat_offender always first, then descending by priority score
    invoices.sort(key=lambda inv: (0 if inv["bucket"] == "repeat_offender" else 1, -inv["priority_score"]))

    state["last_upload_time"] = datetime.now().strftime("%B %d, %Y, %I:%M %p")
    state["last_upload_filename"] = file.filename
    state["upload_count"] += 1

    return jsonify({"invoices": invoices, "meta": state})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
