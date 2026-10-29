# P17 — Stack & Queue Operations Simulator

A desktop application for learning and demonstrating two core data structures:

- **Stack** — LIFO (Last In, First Out): push, pop, peek
- **Queue** — FIFO (First In, First Out): enqueue, dequeue, peek front, peek rear

Built with Python and CustomTkinter. Runs fully offline on Windows 10 and 11.

## Features

| Area | What it does |
|---|---|
| Dashboard | Live cards for stack size, queue size, total / successful / failed operations; quick Push, Pop, Enqueue, Dequeue; mini views of both structures; recent activity |
| Stack Simulator | Push, Pop, Peek, Is Empty, Clear; vertical stack drawing with the top marked; size, capacity and top value readouts; overflow and underflow messages |
| Queue Simulator | Enqueue, Dequeue, Peek Front, Peek Rear, Is Empty, Clear; horizontal queue drawing with front and rear marked |
| Operation History | Every operation (including failures) with number, structure, operation, value, status, details and timestamp; search; filter by structure and operation; Refresh; Clear History; Export CSV |
| Data Structure Visualizer | Large live views of both structures with arrows, index numbers and a legend. Very large structures show the top / front / rear and a "+N more" marker, so the layout never breaks |
| Settings | Dark / light theme, maximum stack and queue capacity, history display limit, confirm-before-clear, developer text, reset to defaults. Values are validated and saved to `data/settings.json` |
| About | Project summary, technologies, LIFO and FIFO explanations, your own developer text |

Behaviour worth knowing:

- Values are text, up to 20 characters, trimmed of surrounding spaces. Empty or over-long input is rejected with a message and recorded as a failed operation.
- Capacities default to 10 and can be 1 to 100. You cannot lower a capacity below the number of elements currently stored; pop or clear first.
- **Clear History** empties the activity log and resets the statistics. It never touches the stack or queue. Clearing the stack or queue never touches the history.
- The history table shows at most the display limit (default 100 rows). The dashboard totals count every operation regardless of that limit.
- CSV export uses the current search and filters, includes all matching stored records (not just the displayed rows), and opens cleanly in Excel.
- The app keeps up to 5,000 history records in memory for the session.

## Install and run (Windows PowerShell)

```powershell
cd P17-Stack-Queue-Simulator
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

If PowerShell refuses to activate the environment, run this once in the same window and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Any Python 3.11 or newer works; replace `py -3.11` with `py -3` or `python` if you prefer. In VS Code, open the folder, choose the `.venv` interpreter (Ctrl+Shift+P → *Python: Select Interpreter*), then run `main.py`.

## Run the tests

```powershell
python -m unittest discover -s tests -t . -v
```

The suite covers the stack and queue (including empty, full and invalid cases), history recording, filtering, search and CSV export, settings validation and persistence, the layout maths used for drawing, and a headless smoke test of every page and button handler. The smoke test uses lightweight fake widgets (`tests/fake_gui.py`), so it needs no display and does not require CustomTkinter. It checks wiring and behaviour, not appearance.

## Package as a Windows .exe (optional)

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name P17-Simulator --collect-all customtkinter main.py
```

The executable is created at `dist\P17-Simulator.exe`. When packaged, settings are stored in a `data` folder next to the `.exe`.

## Project layout

```
main.py                 entry point
simulator.py            service layer: owns stack, queue, history, settings; records every operation
stack.py                LIFO stack
queue_structure.py      FIFO queue (named to avoid the standard-library "queue")
history_manager.py      records, filters, statistics, CSV export
settings_manager.py     validated JSON settings
visualizer.py           pure layout maths for drawing (no GUI imports)
constants.py, errors.py shared names and exceptions
ui/                     theme, reusable components, canvas, one module per page
data/settings.json      saved settings (created automatically if missing)
tests/                  unittest suite
```

Business logic never imports the GUI, so it can be tested and reused on its own.

## Customising

- **Developer information:** Settings → *Developer information*. It is shown on the About page. Nothing personal is hard-coded.
- **Colours and fonts:** every colour is defined once in `ui/theme.py` as a (light, dark) pair; fonts are Segoe UI and Consolas.
- **Version:** `APP_VERSION` in `constants.py`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `CustomTkinter is not installed` | Activate the virtual environment, then `python -m pip install -r requirements.txt` |
| `ModuleNotFoundError: tkinter` | Reinstall Python from python.org and keep *tcl/tk and IDLE* ticked in the installer |
| `py` is not recognised | Use `python` instead, or reinstall Python with *Add python.exe to PATH* ticked |
| Text looks too large or small | Windows display scaling is applied automatically; adjust it in Windows Settings → Display |
| Window is cut off on a small screen | The window opens sized to fit the screen; maximise it for the roomiest layout |
| A notice about settings appears in the terminal | `data/settings.json` was missing values or damaged. Defaults were used for those fields; save settings once to rewrite the file |
| Settings will not save | The `data` folder must be writable. Avoid running from a read-only location |
| Tests fail with `ModuleNotFoundError` | Run them from the project folder using the command above |
