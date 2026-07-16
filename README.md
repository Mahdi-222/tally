# Tally — AR Follow-Up Queue

A small internal tool that turns a CSV of unpaid invoices into a reviewed, ready-to-send follow-up queue.
It classifies each invoice by real risk signals (never treating a first-time late payer the same as a
repeat one), drafts the right message for that situation with Claude, and ( when a human approves ) opens
a pre-filled email in the reviewer's own mail client, so a person sends it rather than a machine.

*(To run it, see `START-HERE.md`.)*

## How it works

- **Classification.** Each invoice lands in one of three tiers based on the client's broader history of
  lateness (supplied in the data) and this invoice's own reschedule count — not just how many days
  overdue it is.
- **Two separate signals on each card.** The *tier* (silent / engaged / repeat-offender) reflects the
  client's track record. The *strike badge* reflects only how many times this specific invoice has been
  rescheduled, capped at 3. They're read together, and can differ — a client flagged on history may show a
  low strike count.
- **Repeat offenders lose the reschedule option.** This closes an obvious loophole: without it, a client
  could push their due date forever and never actually pay.
- **The client never sees their own history cited back to them.** Internally the system uses everything it
  knows to calibrate tone and priority. The drafted message stays warm and forward-looking. For the
  engaged tier it acknowledges the client has been in touch, but never fabricates a quote from a past
  reply — it knows *that* they responded, not the exact words.
- **Approve opens an email; nothing sends on its own.** Approving a draft opens the reviewer's mail client
  with the client's address, subject, and message pre-filled (via `mailto:`). A human hits send. For
  payment chasing you want a person on the last step, and there's no sending infrastructure to misconfigure.
- **Resilient upload.** If the AI response for one invoice fails or comes back malformed, that row falls
  back to a safe placeholder instead of failing the whole batch.
- **Upload tracking.** The header shows when the data was last refreshed, from what file, and how many
  times it's been uploaded.

## Where the data comes from

The tool doesn't track history it only reads it. The core fields (client, amount, due date, and the client's
**email**) come straight from any billing system: that's the system that sent the invoice, so it already
holds them. Because the email rides along in the same export, there's no separate contact list to keep in
sync. The two behavioral signals (reschedule count, whether the client has responded before) assume the AR
system logs engagement, which mature setups do. The CSV stands in for that export.

## A note on scope

This is intentionally a CSV-in prototype. In a real deployment the ingestion step would connect directly to
whatever system holds live invoice data, and the `mailto:` handoff would become a real sending integration
(e.g. SendGrid, Resend, or the Gmail API) with a verified domain so we  keep the same process of reviewing and sending


## Tools used

Python, Flask, and the Anthropic API (Claude) for the AI-generated summaries and drafted messages.
Frontend is plain HTML/CSS/JS, no framework. Built end-to-end with AI-assisted coding.
