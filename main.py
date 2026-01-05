from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from typing import List, Dict, Any, Tuple
import openpyxl
from io import BytesIO
import json
import os

app = FastAPI()

# ---------- STATS ----------

STATS_FILE = "stats.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {"total": 0, "rows": 0, "config": 0}
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)


# ---------- ROUTES UI ----------

@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/app")


@app.get("/status")
def status():
    return {"status": "ok", "message": "JSON Automator en route 🚀"}


@app.get("/app", response_class=HTMLResponse)
def app_ui():
    html_content = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8" />
        <title>JSON Automator – Excel vers JSON</title>

        <style>
            body { font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
                   max-width: 960px; margin: 40px auto; padding: 0 16px; color:#111827; }
            h1 { font-size: 2rem; margin-bottom: .5rem; }
            h2 { font-size: 1.3rem; margin-bottom: .5rem; }
            p  { margin: 0.25rem 0 0.75rem 0; }
            .hero { margin-bottom: 24px; }
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
            pre { background:#111827; color:#e5e7eb; padding:12px; border-radius:8px; overflow-x:auto; font-size:.9rem; }
            .messages { margin-top:8px; color:#92400e; font-size:.9rem; }
            .muted { color:#6b7280; font-size:.85rem; }
            table { border-collapse: collapse; width:100%; font-size:.85rem; }
            th, td { border:1px solid #e5e7eb; padding:6px 8px; }
            th { background:#f9fafb; }
        </style>
    </head>

    <body>
        <div class="hero">
            <span class="badge">Beta gratuite</span>
            <h1>JSON Automator</h1>
            <p>Convertis tes fichiers Excel de configuration en JSON propre, avec validation automatique.</p>
        </div>

        <div class="grid">
            <div>
                <div class="card">
                    <h2>1. Utiliser l'outil</h2>

                    <div class="row">
                        <label for="fileInput">Fichier Excel (.xlsx)</label>
                        <input type="file" id="fileInput" accept=".xlsx" />
                    </div>

                    <div class="row">
                        <label>Mode de conversion</label>
                        <div class="radio-group">
                            <label><input type="radio" name="mode" value="rows" checked /> Rows (debug)</label>
                            <label><input type="radio" name="mode" value="config" /> Config key/value</label>
                        </div>
                    </div>

                    <div class="row">
                        <button id="convertBtn">Convertir</button>
                        <button id="downloadBtn" disabled>Télécharger JSON</button>
                    </div>
                </div>

                <div class="card">
                    <h2>2. Résultat JSON</h2>
                    <pre id="result">{}</pre>
                    <div id="messages" class="messages"></div>
                </div>
            </div>

            <div>
                <div class="card">
                    <h2>Format Excel attendu</h2>
                    <p class="muted">Exemple minimal :</p>

                    <table>
                        <tr><th>key</th><th>value</th><th>required</th><th>type</th></tr>
                        <tr><td>api_url</td><td>https://api.example.com</td><td>yes</td><td>url</td></tr>
                        <tr><td>timeout</td><td>30</td><td>no</td><td>int</td></tr>
                        <tr><td>use_cache</td><td>true</td><td>no</td><td>bool</td></tr>
                    </table>

                    <p class="muted">Validation automatique (entiers, booléens, URLs, champs manquants…).</p>
                </div>
            </div>
        </div>

        <script>
            const btn = document.getElementById('convertBtn');
            const downloadBtn = document.getElementById('downloadBtn');
            const fileInput = document.getElementById('fileInput');
            const resultPre = document.getElementById('result');
            const messagesDiv = document.getElementById('messages');

            let lastResult = null;

            btn.addEventListener('click', async () => {
                const file = fileInput.files[0];
                if (!file) { alert("Merci de sélectionner un fichier .xlsx"); return; }

                const mode = document.querySelector('input[name=\"mode\"]:checked').value;
                const endpoint = mode === 'rows' ? '/convert' : '/convert/config';

                const formData = new FormData();
                formData.append('file', file);

                btn.disabled = true;
                downloadBtn.disabled = true;
                btn.textContent = "Conversion...";
                messagesDiv.textContent = "";
                resultPre.textContent = "{}";

                try {
                    const res = await fetch(endpoint, { method: 'POST', body: formData });
                    const data = await res.json();

                    if (!res.ok) {
                        messagesDiv.textContent = JSON.stringify(data.detail || data);
                        return;
                    }

                    lastResult = data;
                    downloadBtn.disabled = false;
                    resultPre.textContent = JSON.stringify(data, null, 2);
                }
                catch {
                    messagesDiv.textContent = "Erreur réseau";
                }
                finally {
                    btn.disabled = false;
                    btn.textContent = "Convertir";
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
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ---------- LOGIQUE EXCEL ----------

def parse_excel_to_json(file_bytes: bytes) -> List[Dict[str, Any]]:
    try:
        workbook = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Impossible de lire le fichier Excel.")

    sheet = workbook.active
    headers = [str(c.value) if c.value is not None else "" for c in sheet[1]]

    rows = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        d = {headers[i] if i < len(headers) else f"col_{i}": v for i, v in enumerate(row)}
        if any(v not in (None, "") for v in d.values()):
            rows.append(d)
    return rows


def rows_to_config_key_value(rows: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    config = {}
    messages = []
    seen = set()

    for idx, row in enumerate(rows, start=2):
        key = str(row.get("key", "")).strip()
        value = row.get("value")
        required = str(row.get("required", "no")).lower()
        value_type = str(row.get("type", "string")).lower()

        if not key:
            messages.append(f"Ligne {idx}: clé vide — ignorée.")
            continue

        if key in seen:
            messages.append(f"Ligne {idx}: clé '{key}' dupliquée — écrasement.")
        seen.add(key)

        converted = value
        if value_type == "int":
            try: converted = int(value)
            except: messages.append(f"Ligne {idx}: '{key}' doit être un entier.")
        elif value_type == "bool":
            converted = str(value).lower() in ["true","1","yes"]
        elif value_type == "url":
            if not str(value).startswith(("http://","https://")):
                messages.append(f"Ligne {idx}: '{key}' doit être une URL valide.")

        if required == "yes" and (value is None or value == ""):
            messages.append(f"Ligne {idx}: valeur obligatoire manquante pour '{key}'.")

        config[key] = converted

    return config, messages


# ---------- API ----------

@app.post("/convert")
async def convert_excel_to_json_api(file: UploadFile = File(...)):
    rows = parse_excel_to_json(await file.read())

    stats = load_stats()
    stats["total"] += 1
    stats["rows"] += 1
    save_stats(stats)

    return {"rows": rows}


@app.post("/convert/config")
async def convert_excel_to_config_api(file: UploadFile = File(...)):
    rows = parse_excel_to_json(await file.read())
    config, messages = rows_to_config_key_value(rows)

    stats = load_stats()
    stats["total"] += 1
    stats["config"] += 1
    save_stats(stats)

    if not config:
        raise HTTPException(status_code=400, detail={"messages": messages})

    return {"config": config, "messages": messages}


@app.get("/_admin/stats")
def get_stats():
    return load_stats()
