# Prediction Plot Generation Tool

Automates generation of prediction maps and report image replacement using QGIS and Python. The main workflow renders band-specific maps (e.g., 700/850 MHz) with legends and grid overlays, and saves per-site outputs. A companion script updates selected images inside DOCX templates.

## Project Structure
- `main.py`: QGIS-driven plot generator for site IDs across bands.
- `Replace_img.py`: Replaces selected images inside DOCX reports per site/band.
- `code_version/`: Historical/alternative versions (`v1.py`–`v4.py`) of the generator.
- `launch_qgis.bat`: Windows launcher to run `main.py` using QGIS’s embedded Python.

## Requirements
- Windows with QGIS LTR installed (tested with `QGIS 3.28.14`).
- Python embedded in QGIS (used via `pyqgis.exe`) for `main.py`.
- External Python (system Python 3.9+) for `Replace_img.py`.
- Python libraries used:
  - `qgis`, `processing`, `PyQt5` (via QGIS environment)
  - `pandas` (CSV lookups)
  - `python-docx` (DOCX manipulation; only for `Replace_img.py`)

## Setup
1. Install QGIS LTR and confirm the prefix path is valid. The scripts default to `C:\Program Files\QGIS 3.28.14\apps\qgis-ltr`.
2. Ensure the shapetools plugin is installed in your QGIS profile; the scripts attempt to load it from `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins`.
3. Prepare input data folders and CSVs referenced by `main.py` (e.g., `cell_file/final_cell.csv`, `site_data/reh`, `legend/...`). Paths are currently hardcoded; adjust them to your environment.
4. For `Replace_img.py`, install dependencies in your system Python:
   ```bash
   pip install pandas python-docx
   ```

## Usage

### Generate Prediction Plots
- Recommended: use the batch launcher to run under the QGIS Python runtime:
  1. Double-click `launch_qgis.bat` or run it from a terminal.
  2. Follow prompts to enter the number of Site IDs and each Site ID.
  3. Outputs are saved per-site into folders under the configured `output_dir`.

- Direct run (advanced): If your environment variables are set for QGIS, you can run:
  ```bash
  "C:\Program Files\QGIS 3.28.14\apps\Python39\pyqgis.exe" main.py
  ```

### Replace Images in DOCX Reports
Run with system Python after adjusting `INPUT_DOCX_ROOT`, `DEFAULT_OUTPUT_DIR`, and CSV paths inside `Replace_img.py`:
```bash
python Replace_img.py
```

## Configuration Notes
- `main.py` contains hardcoded paths for:
  - `csv_path`: points to the cell data CSV
  - `site_data_root`: root folder containing banded site data (`700/850/...`)
  - `output_dir`: destination for generated images
  - `legend_images`: list of legend image file paths
- Update these paths to match your local environment before running.

## Troubleshooting
- QGIS prefix invalid: Verify `QGIS_PREFIX_PATH` or the default path exists.
- Shapetools provider registration fails: Ensure the plugin is installed under your QGIS profile.
- Layer load errors: Confirm `.tab` files exist in the band/site folders and the CSV has correct `SITE ID`, `Site ID_L700`, `Site ID_L850` entries.
- Legend image missing: Confirm the `legend/...` image paths exist.

## Notes
- The `code_version/` scripts are kept for reference; `main.py` is the current entry point.
- No license file is included. Add one if you plan to share externally.