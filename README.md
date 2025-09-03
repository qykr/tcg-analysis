# LLM Response Analyzer

A small web app to review and annotate LLM responses to competitive programming problems. It joins responses to problem metadata from a CSV, supports filtering, categorization, descriptions, Markdown rendering, and autosaves annotations locally and to disk.

## Features
- Auto-loads `responses.json` and `output.csv` on startup (if present alongside `index.html`).
- Manual upload still available for both files.
- Join responses to problems by `problem_id` (1-based CSV row index) or fallback to `name`.
- Filters: difficulty, type, category, search (over description and metadata).
- Per-response: description, category assignment, trace, and problem details (question, tags, URL, limits).
- Markdown rendering for problem descriptions (supports lists, emphasis, fenced code blocks).
- Categories: create/rename/delete.
- Submit/Hide submitted flow to mark analyses as done and hide them from the list (toggle button to show them again).
- Autosave annotations to `localStorage` and to `annotations.json` (via a tiny Python server). Import/Export available.

## Requirements
- Python 3.8+
- A modern browser

## Quick start
1) Clone the repo

```bash
git clone https://github.com/qykr/tcg-analysis.git
cd tcg-analysis
```

2) Start the server (serves static files and saves annotations)

```bash
python3 server.py
```

This starts on http://127.0.0.1:5173/.

3) Open the app
- Navigate to `http://127.0.0.1:5173/` in your browser.
- If `responses.json` and `output.csv` exist in the folder, they load automatically.
- Otherwise, use the file pickers at the top to upload them manually.

4) Review and annotate
- Use the filters (difficulty, type, search, category).
- Expand “Problem details” to see the Markdown-rendered description, tags, URL, time and memory limits.
- Add a description and assign a category. Edits autosave.
- Click “Submit analysis” on a response to mark it submitted; use the “Show/Hide submitted” button to toggle visibility.
- Use Export/Import for annotations if needed.

## Files
- `index.html`: App shell and UI layout
- `styles.css`: Dark theme styles
- `app.js`: App logic, CSV/JSON parsing, filters, rendering, autosave
- `server.py`: Static server + `POST/GET /api/annotations` to persist `annotations.json`
- `responses.json`: Example responses file
- `output.csv`: Problems CSV (includes `question`, `difficulty`, `tags`, `url`, `time_limit`, `memory_limit`)
- `tools/add_problem_id_column.py`: Helper to generate `output_with_ids.csv` by prepending a `problem_id` column (1-based index)

## Input formats
- `responses.json`: array of items like:

```json
{
  "id": "r-0001",
  "problem_id": 2,
  "problem_name": "nth-fibonacci-number1335",
  "type": "solution",
  "model": "gpt-4o",
  "trace": "Explained dynamic programming approach...",
  "difficulty": "EASY"
}
```

- `output.csv`: must include at least `name`, `question`, `difficulty`, `tags` (stringified list OK), `url`, `time_limit`, `memory_limit`.
  - The app treats the row index (1-based) as `problem_id` for joining.

## CSV helper (optional)
If your CSV lacks a `problem_id` column and you’d like one, run:

```bash
python3 tools/add_problem_id_column.py
```

This writes `output_with_ids.csv` which the app will prefer if present.

## Notes
- Large files: If `output.csv` is over 50 MB, GitHub recommends Git LFS. The app itself can read large CSV files, but repo pushes may warn you.
- Security: Problem descriptions are rendered with `marked` and sanitized with `DOMPurify`.

## Troubleshooting
- CSS not loading when opening `index.html` directly: serve over HTTP using `python3 server.py`.
- Auto-load not picking up files: verify `responses.json` and `output.csv` sit next to `index.html`.
- Annotations not saving to file: ensure you’re using `server.py` (not `python -m http.server`). You should see `annotations.json` update as you edit.
