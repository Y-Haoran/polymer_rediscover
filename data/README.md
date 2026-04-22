# Data Directory

This directory is intentionally empty in git.

Suggested layout:

- `fda_iid/raw/`: downloaded FDA IID files
- `dailymed/raw/`: downloaded SPL exports or parsed label tables
- `schema/`: candidate polymer tables and synonym mappings
- `benchmark/`: train, validation, and test benchmark manifests
- `interim/`: normalized tables with synonym mapping
- `processed/`: model-ready ranking datasets

Do not commit licensed, proprietary, or large downloaded datasets by default.
