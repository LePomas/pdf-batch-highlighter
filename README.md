# PDF Batch Highlighter

A PyQt5 desktop app that highlights a list of search terms across one or two PDF files simultaneously. Terms are loaded from a plain text file; results are saved as new PDFs in a `Result/` folder.

Useful for quickly marking up large technical documents — datasheets, standards, requirements — against a known keyword list.

## Features

- Load up to two PDF files at once
- Load search terms from a `.txt` file (one term per line)
- Choose highlight color from 13 presets with live preview
- Background processing via `QThread` — UI stays responsive
- Real-time progress bar and log output
- Handles existing output files: overwrite or auto-rename with timestamp
- Cross-platform (Windows, macOS, Linux)

## Requirements

- Python 3.8+

## Installation

```sh
pip install -r requirements.txt
```

## Usage

```sh
python pdf_highlighter.py
```

1. Click **Select First PDF** (and optionally **Select Second PDF**).
2. Click **Select Search Terms File** — a `.txt` with one keyword per line.
3. Pick a highlight color.
4. Click **Highlight PDFs**.

Highlighted files are saved to `Result/<original_name>_highlighted.pdf`.

## Search Terms File Format

```
keyword one
another term
PART-NUMBER-123
```

## Tech Stack

`PyMuPDF` · `PyQt5`

## License

MIT
