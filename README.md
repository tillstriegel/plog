plog – Plug‑n‑Play Logging Utility
=================================
Drop‑in library that wires up sensible, pretty and robust logging for any Python
project with *one* line of code:

    import plog; plog.init()

The library installs two handlers by default:
- colourful Rich‐powered console output
- daily‑rotating UTF‑8 file logs inside ./logs/

Unhandled exceptions are automatically captured through ``sys.excepthook`` so
tracebacks never disappear silently.

If *rich* is unavailable the console gracefully falls back to a plain formatter
with colour‑escape codes (works on Windows 10+ via *colorama*).

------------------------------------------------------------------------
MIT License – 2025 Till Striegel