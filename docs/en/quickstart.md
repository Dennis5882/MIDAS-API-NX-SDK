# midas-nx Getting Started Guide (no prior programming experience needed)

This guide is for structural engineers who use MIDAS Gen NX/Civil NX daily
but have never written a line of Python before. It walks through everything
from installing Python to running your first script, in order, so you can
follow it start to finish in one sitting.

> If you already write code, [README.md](../../README.md)'s Quick Start is
> faster. This guide is for the step before that — for anyone who isn't
> sure what Python even is yet.

## Before you start

- A Windows PC (this guide is written for Windows)
- MIDAS Gen NX or Civil NX installed, with a valid license
- An internet connection (the SDK talks to MIDAS's cloud relay server)

## Step 1: Install Python

1. Go to https://www.python.org/downloads/.
2. Click "Download Python 3.x.x" to download the installer.
3. Run the installer. **Make sure to check the "Add python.exe to PATH"
   checkbox at the bottom of the first screen** before clicking "Install
   Now." Skipping this means your command prompt won't recognize `python`
   later.
4. Once installed, verify it worked. Search for "cmd" in the Start menu to
   open Command Prompt, then type:

   ```
   python --version
   ```

   If you see something like `Python 3.x.x`, you're good. If you get
   `'python' is not recognized as an internal or external command`, you
   missed the PATH checkbox in step 3 — reinstall Python and check it this
   time.

## Step 2: Install midas-nx

In the same Command Prompt window:

```
pip install midas-nx
```

You'll see `Successfully installed midas-nx-...` when it's done.

## Step 3: Get a MAPI key

The `MAPI-Key` is the authentication key this SDK uses to talk to MIDAS
Gen NX/Civil NX. You don't get it from Python — you get it **from inside
the MIDAS Gen NX (or Civil NX) application itself**.

1. Launch MIDAS Gen NX (or Civil NX).
2. Find the **Open API** menu in the top menu bar (depending on your
   version, it may appear as "Open API" or under an "Apps" menu).
3. Choose **Issue API Key** (or similarly worded). A long string of
   letters and numbers appears — copy it.

> This key is temporary and only valid while the application is running.
> You can always get a new one from the same menu, so don't worry if you
> lose it.

## Step 4: Write and run your first script

Open Notepad (or VS Code, or any text editor) and paste the following
exactly as-is. Just replace
`"paste_the_key_you_copied_in_step_3_here"` with your actual key.

```python
from midas_nx import MidasClient, Product, doc
from midas_nx.db.node_element import Element, Node
from midas_nx.db.project import Unit
from midas_nx.db.properties.material import Material
from midas_nx.db.properties.section import Section

# Using Civil NX instead? Change this to product=Product.CIVIL.
client = MidasClient(mapi_key="paste_the_key_you_copied_in_step_3_here", product=Product.GEN)

doc.new_project(client=client)
Unit.update({1: {"DIST": "M", "FORCE": "KN"}}, client=client)

Material.create(
    {1: {"TYPE": "CONC", "NAME": "C24",
         "PARAM": [{"P_TYPE": 1, "STANDARD": "KS01(RC)", "DB": "C24"}]}},
    client=client,
)
Section.create(
    {1: {"SECTTYPE": "DBUSER", "SECT_NAME": "Column",
         "SECT_BEFORE": {"USE_SHEAR_DEFORM": True, "SHAPE": "SB", "DATATYPE": 2,
                          "SECT_I": {"vSIZE": [0.6, 0.6]}}}},
    client=client,
)
Node.create({1: {"X": 0, "Y": 0, "Z": 0}, 2: {"X": 0, "Y": 0, "Z": 3.2}}, client=client)
Element.create({1: {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 2]}}, client=client)
doc.save(client=client)

print("Success! Check Gen NX — a column should now be in the model.")
```

Save the file as `first_script.py` (your Desktop or any folder works fine).

In Command Prompt, navigate to the folder where you saved it and run it.
For example, if you saved it to your Desktop:

```
cd Desktop
python first_script.py
```

You should see `Success! Check Gen NX...` printed, and switching to the
Gen NX window will show a new 0.6m x 0.6m concrete column, 3.2m tall.

> The material/section combination above (`C24`/`KS01(RC)`) was
> live-verified against a real Gen NX and Civil NX session on 2026-07-22
> (see [docs/live_verification_notes.md](../live_verification_notes.md)) —
> this first script uses confirmed values, not an untested guess, so it's
> meant to just work.

## If something goes wrong

- **`MidasConnectionError`**: check that Gen NX/Civil NX is running and
  Open API is connected. This SDK's error messages end with a
  `(Hint: ...)` telling you what to check.
- **`MidasAuthError`**: make sure you pasted the key from step 3 exactly.
  Keys can change when you restart the app — get a fresh one and paste it
  in again if this happens.
- **Behind a corporate firewall**: see the "Troubleshooting" section in
  [README.md](../../README.md) for the exact port/address info to hand to
  your IT team.

## Next steps

- **Keep going with an AI coding assistant.** Once you know the pattern
  above, you don't need to memorize or hand-write every call yourself.
  Show this script to Claude Code, ChatGPT, GitHub Copilot, or similar, and
  ask in plain language — "make a 20m beam instead of a column," "add a
  load combination" — and it'll turn that into real `midas-nx` code. This
  SDK is built to make that easy (type hints, clear error messages).
- More realistic examples: the
  [`examples/python/`](../../examples/python/) folder on GitHub (beam load
  combinations, wind loads, construction stages, ...) — a good thing to
  show your AI assistant as a "build me something like this" reference.
- Full list of what's implemented: [ROADMAP.md](../../ROADMAP.md)
- More detailed usage and design notes: [README.md](../../README.md)

If you got stuck anywhere following this guide, please open a GitHub
issue — it helps make the guide better for the next person.
