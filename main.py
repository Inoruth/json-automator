from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse
from typing import List, Dict, Any, Tuple
import openpyxl
from io import BytesIO
import json
import os

app = FastAPI()

# ---------- STATS ----------

STATS_FILE = "stats.json"


def load_stats() -> Dict[str, int]:
    """
    Load usage statistics from the JSON file.

    Returns a dictionary with:
    - total: number of conversions (rows + config)
    - rows: number of 'rows' mode conversions
    - config: number of 'config' mode conversions
    """
    if not os.path.exists(STATS_FILE):
        return {"total": 0, "rows": 0, "config": 0}
    with open(STATS_FILE, "r") as f:
        return json.load(f)


def save_stats(stats: Dict[str, int]) -> None:
    """
    Persist usage statistics to the JSON file.

    Parameters
    ----------
    stats : dict
        Dictionary returned by load_stats(), updated with new counts.
    """
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)


# ---------- UI ROUTES ----------


@app.get("/", response_class=HTMLResponse)
def root():
    """
    Redirect root URL to the main web UI (/app).
    """
    return RedirectResponse(url="/app")


@app.get("/status")
def status():
    """
    Healthcheck endpoint to verify that the app is running.
    """
    return {"status": "ok", "message": "JSON Automator is running 🚀"}


@app.get("/app", response_class=HTMLResponse)
def app_ui():
    """
    Serve the main HTML UI.

    The UI lets the user:
    - upload an Excel file (.xlsx)
    - choose conversion mode (rows / config)
    - see the JSON result
    - download the JSON
    - download an example Excel file
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>JSON Automator – Excel to JSON</title>

        <style>
            body { font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
                   max-width: 960px; margin: 40px auto; padding: 0 16px; color:#111827; }
            h1 { font-size: 2rem; margin-bottom: .5rem; }
            h2 { font-size: 1.3rem; margin-bottom: .5rem; }
            p  { margin: 0.25rem 0 0.75rem 0; }
            .hero { margin-bottom: 16px; }
            .badge { display:inline-block; font-size:.75rem; padding:2px 8px;
                     border-radius:999px; background:#ecfdf5; color:#047857; margin-bottom:8px; }
            .grid { display:grid; grid-template-columns: 1.2fr 1fr; gap:24px; align-items:flex-start; }
            .card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; margin-bottom: 24px; background:white; }
            .row { margin-bottom: 12px; }
            label { display:block; margin-bottom:4px; font-weight:500; }
            .radio-group { display:flex; gap:16px; margin-top:4px; }
            button { padding:8px 16px; border-radius:6px; border:none; cursor:pointer; font-weight:500; }
            #convertBtn { background:#0f766e; color:white; }
            #convertBtn:disabled { background:#9ca3af; cursor:not-allowed; }
            #downloadBtn { background:#2563eb; color:white; margin-left:8px; }
            #downloadBtn:disabled { background:#9ca3af; }
            #exampleBtn { background:#6b7280; color:white; margin-left:8px; }
            pre { background:#111827; color:#e5e7eb; padding:12px; border-radius:8px; overflow-x:auto; font-size:.9rem; }
            .messages { margin-top:8px; color:#92400e; font-size:.9rem; }
            .muted { color:#6b7280; font-size:.85rem; }
            table { border-collapse: collapse; width:100%; font-size:.85rem; }
            th, td { border:1px solid #e5e7eb; padding:6px 8px; }
            th { background:#f9fafb; }
            .notice { background:#eef2ff; border-color:#c7d2fe; }
            .notice strong { font-weight:600; }
        </style>
    </head>

    <body>
        <div class="hero">
            <span class="badge">Free beta</span>
            <h1>JSON Automator</h1>
            <p>Convert Excel config sheets into clean JSON, with basic validation.</p>
        </div>

        <div class="card notice">
            <p>
                <strong>Note:</strong> JSON Automator works best for
                <strong>flat or lightly-nested configuration files</strong>
                (API settings, feature flags, app configs, etc.).
                Support for deep / highly-nested JSON structures is planned.
            </p>
        </div>

        <div class="grid">
            <div>
                <div class="card">
                    <h2>1. Use the tool</h2>

                    <div class="row">
                        <label for="fileInput">Excel file (.xlsx)</label>
                        <input type="file" id="fileInput" accept=".xlsx" />
                    </div>

                    <div class="row">
                        <label>Conversion mode</label>
                        <div class="radio-group">
                            <label><input type="radio" name="mode" value="rows" checked /> Rows (debug)</label>
                            <label><input type="radio" name="mode" value="config" /> Config key/value</label>
                        </div>
                    </div>

                    <div class="row">
                        <button id="convertBtn">Convert</button>
                        <button id="downloadBtn" disabled>Download JSON</button>
                        <button id="exampleBtn" type="button">Download example (.xlsx)</button>
                    </div>
                </div>

                <div class="card">
                    <h2>2. JSON result</h2>
                    <pre id="result">{}</pre>
                    <div id="messages" class="messages"></div>
                </div>
            </div>

            <div>
                <div class="card">
                    <h2>Expected Excel format</h2>
                    <p class="muted">Minimal example:</p>

                    <table>
                        <tr><th>key</th><th>value</th><th>required</th><th>type</th></tr>
                        <tr><td>api_url</td><td>https://api.example.com</td><td>yes</td><td>url</td></tr>
                        <tr><td>timeout</td><td>30</td><td>no</td><td>int</td></tr>
                        <tr><td>use_cache</td><td>true</td><td>no</td><td>bool</td></tr>
                    </table>

                    <p class="muted">Automatic validation (ints, booleans, URLs, missing required fields…).</p>
                </div>
            </div>
        </div>

        <script>
            const btn = document.getElementById('convertBtn');
            const downloadBtn = document.getElementById('downloadBtn');
            const exampleBtn = document.getElementById('exampleBtn');
            const fileInput = document.getElementById('fileInput');
            const resultPre = document.getElementById('result');
            const messagesDiv = document.getElementById('messages');

            let lastResult = null;

            btn.addEventListener('click', async () => {
                const file = fileInput.files[0];
                if (!file) { alert("Please select a .xlsx file first."); return; }

                const mode = document.querySelector('input[name=\\"mode\\"]:checked').value;
                const endpoint = mode === 'rows' ? '/convert' : '/convert/config';

                const formData = new FormData();
                formData.append('file', file);

                btn.disabled = true;
                downloadBtn.disabled = true;
                btn.textContent = "Converting...";
                messagesDiv.textContent = "";
                resultPre.textContent = "{}";

                try {
                    const res = await fetch(endpoint, { method: 'POST', body: formData });
                    const type = res.headers.get('content-type') || '';
                    const data = await res.json();

                    if (!res.ok) {
                        if (type.includes('application/json')) {
                            if (data.detail && data.detail.messages)
                                messagesDiv.textContent = data.detail.messages.join(' | ');
                            else
                                messagesDiv.textContent = JSON.stringify(data.detail || data);
                        } else {
                            messagesDiv.textContent = "Server error while converting.";
                        }
                        return;
                    }

                    lastResult = data;
                    downloadBtn.disabled = false;
                    resultPre.textContent = JSON.stringify(data, null, 2);
                    if (data.messages?.length) {
                        messagesDiv.textContent = data.messages.join(' | ');
                    }
                }
                catch (e) {
                    messagesDiv.textContent = "Network error while calling the API.";
                }
                finally {
                    btn.disabled = false;
                    btn.textContent = "Convert";
                }
            });

            downloadBtn.addEventListener('click', () => {
                if (!lastResult) return;

                const blob = new Blob(
                    [JSON.stringify(lastResult, null, 2)],
                    { type: "application/json" }
                );

                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "result.json";
                a.click();
                URL.revokeObjectURL(url);
            });

            exampleBtn.addEventListener('click', () => {
                window.location.href = "/example";
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ---------- EXCEL LOGIC ----------


def parse_excel_to_json(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Parse the first sheet of an Excel workbook into a list of row dictionaries.

    Parameters
    ----------
    file_bytes : bytes
        Raw content of the uploaded .xlsx file.

    Returns
    -------
    list[dict]
        One dict per non-empty row. Keys come from the header row (row 1),
        values from subsequent rows.

    Raises
    ------
    HTTPException (400)
        If the file is not a valid Excel workbook or the header row is empty.
    """
    try:
        workbook = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read Excel file.")

    sheet = workbook.active
    headers = [str(c.value) if c.value is not None else "" for c in sheet[1]]

    if not any(headers):
        raise HTTPException(status_code=400, detail="First row must contain headers.")

    rows: List[Dict[str, Any]] = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        d: Dict[str, Any] = {}
        for idx, v in enumerate(row):
            col_name = headers[idx] if idx < len(headers) else f"col_{idx}"

            # special handling: if this is the 'required' column and the cell is empty,
            # normalize it to "no" instead of leaving it as null
            if col_name == "required" and (v is None or str(v).strip() == ""):
                d[col_name] = "no"
            else:
                d[col_name] = v

        # Ignore fully empty rows
        if any(v not in (None, "") for v in d.values()):
            rows.append(d)

    return rows


def rows_to_config_key_value(rows: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Convert a list of row dictionaries into a config object.

    Expected columns (case-sensitive):
    - key (required)
    - value (required)
    - required (optional, yes/no)
    - type (optional, string/int/bool/url)

    The function:
    - builds a config dict: {key: converted_value}
    - validates required fields and basic types
    - collects warnings / errors in a list of messages

    Parameters
    ----------
    rows : list[dict]
        Output of parse_excel_to_json().

    Returns
    -------
    config : dict
        Final configuration object.
    messages : list[str]
        Validation messages (warnings / errors). Can be empty.
    """
    config: Dict[str, Any] = {}
    messages: List[str] = []

    if not rows:
        messages.append("No data rows found.")
        return config, messages

    first = rows[0]
    if "key" not in first or "value" not in first:
        messages.append("Columns 'key' and 'value' are required.")
        return config, messages

    seen = set()

    for idx, row in enumerate(rows, start=2):
        key_raw = row.get("key")
        value = row.get("value")

        # If 'required' cell is empty or normalized to "no", treat accordingly
        required = (str(row.get("required", "")).strip().lower() or "no")
        value_type = str(row.get("type", "string")).strip().lower()

        if not key_raw or str(key_raw).strip() == "":
            messages.append(f"Row {idx}: empty key — ignored.")
            continue

        key = str(key_raw).strip()

        if key in seen:
            messages.append(f"Row {idx}: duplicate key '{key}' — overwriting previous value.")
        seen.add(key)

        if required == "yes" and (value is None or str(value) == ""):
            messages.append(f"Row {idx}: missing required value for '{key}'.")

        converted = value
        if value_type == "int":
            try:
                converted = int(value)
            except Exception:
                messages.append(f"Row {idx}: '{key}' should be an integer.")
        elif value_type == "bool":
            s = str(value).lower()
            if s in ["true", "1", "yes"]:
                converted = True
            elif s in ["false", "0", "no"]:
                converted = False
            else:
                messages.append(f"Row {idx}: '{key}' should be a boolean (true/false, yes/no).")
        elif value_type == "url":
            if not str(value).startswith(("http://", "https://")):
                messages.append(f"Row {idx}: '{key}' should be a valid URL (http/https).")

        config[key] = converted

    if not config:
        messages.append("No valid entries were generated from the sheet.")

    return config, messages


# ---------- API ENDPOINTS ----------


@app.post("/convert")
async def convert_excel_to_json_api(file: UploadFile = File(...)):
    """
    API endpoint for the 'rows' mode.

    - Accepts an Excel file (.xlsx)
    - Parses it into a list of row dictionaries
    - Updates usage statistics
    - Returns: {"rows": [...]}
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    rows = parse_excel_to_json(await file.read())

    stats = load_stats()
    stats["total"] += 1
    stats["rows"] += 1
    save_stats(stats)

    return JSONResponse(content={"rows": rows})


@app.post("/convert/config")
async def convert_excel_to_config_api(file: UploadFile = File(...)):
    """
    API endpoint for the 'config' mode.

    - Accepts an Excel file (.xlsx)
    - Parses it into rows
    - Builds a config object using rows_to_config_key_value()
    - Updates usage statistics
    - On error: returns HTTP 400 with validation messages
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    rows = parse_excel_to_json(await file.read())
    config, messages = rows_to_config_key_value(rows)

    stats = load_stats()
    stats["total"] += 1
    stats["config"] += 1
    save_stats(stats)

    if not config:
        # All messages are returned to the client when nothing valid is produced
        raise HTTPException(status_code=400, detail={"messages": messages})

    return JSONResponse(content={"config": config, "messages": messages})


# ---------- EXAMPLE EXCEL ----------


@app.get("/example")
def download_example():
    """
    Download an example Excel file that matches the expected format.

    The file 'example.xlsx' must be present at the project root
    (same directory as main.py).
    """
    example_path = "example.xlsx"
    if not os.path.exists(example_path):
        raise HTTPException(status_code=404, detail="Example file not found.")
    return FileResponse(example_path, filename="example.xlsx")


# ---------- ADMIN ----------


@app.get("/_admin/stats")
def get_stats():
    """
    Return global usage statistics.

    This endpoint is open while the app is in beta, but it can be
    restricted later if needed.
    """
    return load_stats()
