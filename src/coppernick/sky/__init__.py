"""Sky-scanning subsystem: day-sky vision, night-sky NASA cross-referencing,
hardware-agnostic camera ingestion, and passive early-warning alerting only.

Strictly passive detection/alerting -- see docs/ARCHITECTURE.md's Sky Watch
section for the explicit scope boundary. Nothing here tracks, targets, or
acts on a detected object beyond surfacing it to a human.
"""
