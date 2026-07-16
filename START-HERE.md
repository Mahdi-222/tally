# Tally — how to run it

You only do two things.

## On a Mac
1. Double-click **`start.command`**
2. When it asks, paste your Anthropic API key and press Return.

That's it. Your browser opens to Tally. Click **Upload CSV** and pick `sample_invoices.csv` to see it work.

> First time only: if the Mac says *"start.command can't be opened because it is from an unidentified developer,"* right-click the file → **Open** → **Open**. You only do this once.

## On Windows
1. Double-click **`start-windows.bat`**
2. When it asks, paste your Anthropic API key and press Enter.

Your browser opens to Tally. Click **Upload CSV** and pick `sample_invoices.csv`.

---

### Where do I get the API key?
Go to **https://console.anthropic.com** → **API keys** → create one. It starts with `sk-ant-`. You paste it in once and never again.

### How do I stop it?
Close the black terminal window that opened.

### Something went wrong?
The most common cause is Python not being installed. Grab it from **https://www.python.org/downloads/** (on Windows, tick **"Add Python to PATH"** during install), then double-click the start file again.
