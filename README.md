# LLM Response Analyzer

A small web app to review and annotate LLM responses to competitive programming problems. It joins responses to problem metadata from a JSON file, supports filtering, categorization, descriptions, Markdown rendering, and autosaves annotations locally and to disk.

## Features
- Auto-loads `responses.json` and `validation_problems.json` on startup (if present alongside `index.html`).
- Manual upload still available for both files.
- Join responses to problems by `problem_id` (JSON problem index) or fallback to `name`.
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

2) Start the web application

```bash
python3 run_webapp.py
```

This starts on http://127.0.0.1:5173/.

3) Open the app
- Navigate to `http://127.0.0.1:5173/` in your browser.
- If `data/responses.json` and `data/validation_problems.json` exist, they load automatically.
- Otherwise, use the file pickers at the top to upload them manually.

4) Review and annotate
- Use the filters (difficulty, type, search, category).
- Expand “Problem details” to see the Markdown-rendered description, tags, URL, time and memory limits.
- Add a description and assign a category. Edits autosave.
- Click “Submit analysis” on a response to mark it submitted; use the “Show/Hide submitted” button to toggle visibility.
- Use Export/Import for annotations if needed.

## Repository Structure
```
analysis-webapp/
├── data/                          # Data files
│   ├── validation_problems.json   # Problems JSON with metadata
│   ├── responses.jsonl            # Generated LLM responses (JSONL)
│   ├── responses.json             # Generated responses (JSON for web app)
│   └── annotations.json           # User annotations and categories
├── generation/                    # LLM response generation
│   ├── get_reasoning_traces.py    # Main generation script
│   ├── prompts.py                 # Persona-specific prompts
│   ├── lm_client.py               # OpenRouter API client
│   ├── convert_to_json.py         # JSONL to JSON converter
│   ├── run_generation.py          # Complete generation pipeline
│   ├── test_generation.py         # Test with small subset
│   ├── resume_generation.py       # Resume interrupted generation
│   └── requirements.txt           # Python dependencies
├── webapp/                        # Web application
│   ├── index.html                 # App shell and UI layout
│   ├── styles.css                 # Dark theme styles
│   ├── app.js                     # App logic, filters, rendering
│   └── server.py                  # Static server + API endpoints
├── tools/                         # Utility scripts
│   └── add_problem_id_column.py   # CSV helper script
├── run_webapp.py                  # Main entry point for web app
├── run_generation.py              # Main entry point for generation
├── test_generation.py             # Main entry point for testing
└── README.md                      # This file
```

## Generating LLM Responses
The repo includes scripts to generate LLM responses for all problems in `validation_problems.json`:

### Setup
1) Install dependencies:
```bash
pip install -r requirements.txt
```

2) Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY='your-key-here'
```

### Generate Responses
- **Test run** (2 problems, 4 responses):
```bash
python3 test_generation.py
```

- **Full generation** (300 problems, 600 responses):
```bash
python3 run_generation.py
```

This generates:
- `data/responses.jsonl`: Raw output from LLM
- `data/responses.json`: Converted format for the web app

The script creates two types of responses per problem:
- **Naive coder**: Writes code without much thought or optimization
- **Reasoning**: Expert analysis with detailed step-by-step reasoning

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

- `validation_problems.json`: must include at least `question`, `difficulty`, `input_output` keys with problem data.
  - The app treats the problem index as `problem_id` for joining.

## JSON helper (optional)
If your JSON lacks proper problem indices and you'd like to add them, run:

```bash
python3 tools/add_problem_id_column.py
```

This writes `validation_problems_with_ids.json` which the app will prefer if present.

## Notes
- Large files: If `validation_problems.json` is over 50 MB, GitHub recommends Git LFS. The app itself can read large JSON files, but repo pushes may warn you.
- Security: Problem descriptions are rendered with `marked` and sanitized with `DOMPurify`.

## Troubleshooting
- CSS not loading when opening `webapp/index.html` directly: serve over HTTP using `python3 run_webapp.py`.
- Auto-load not picking up files: verify `data/responses.json` and `data/validation_problems.json` exist.
- Annotations not saving to file: ensure you're using `run_webapp.py`. You should see `data/annotations.json` update as you edit.
- Generation errors: make sure you're in the correct directory and have set `OPENROUTER_API_KEY`.
