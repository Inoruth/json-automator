from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from typing import List, Dict, Any, Tuple
import openpyxl
from io import BytesIO

app = FastAPI()

# ---------- ROUTES DE BASE / UI ----------

@app.get("/", response_class=HTMLResponse)
def root():
    # Redirige vers l'interface
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
        <title>JSON Automator</title>
        <style>
            body { font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
                   max-width: 900px; margin: 40px auto; padding: 0 16px; }
            h1 { font-size: 1.8rem; margin-bottom: .5rem; }
            .card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 24px; }
            .row { margin-bottom: 12px; }
            label { display:block; margin-bottom:4px; font-weight:500; }
            .radio-group { display:flex; gap:16px; margin-top:4px; }
            button { padding:8px 16px; border-radius:6px; border:none; cursor:pointer; font-weight:500; }
            button#convertBtn { background:#0f766e; color:white; }
            button#convertBtn:disabled { background:#9ca3af; cursor:not-allowed; }
            pre { background:#111827; color:#e5e7eb; padding:12px; border-radius:8px; overflow-x:auto; font-size:.9rem; }
            .messages { margin-top:8px; color:#92400e; font-size:.9rem; }
        </style>
    </head>
    <body>
        <h1>JSON Automator</h1>
        <p>Convertis un fichier Excel (.xlsx) en JSON : soit brut (rows), soit en config key/value.</p>

        <div class="card">
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
            </div>
        </div>

        <div class="card">
            <h2>Résultat JSON</h2>
            <pre id="result">{}</pre>
            <div id="messages" class="messages"></div>
        </div>

        <script>
            const btn = document.getElementById('convertBtn');
            const fileInput = document.getElementById('fileInput');
            const resultPre = document.getElementById('result');
            const messagesDiv = document.getElementById('messages');

            btn.addEventListener('click', async () => {
                const file = fileInput.files[0];
                if (!file) { alert("Merci de sélectionner un fichier .xlsx"); return; }

                const mode = document.querySelector('input[name="mode"]:checked').value;
                const endpoint = mode === 'rows' ? '/convert' : '/convert/config';

                const formData = new FormData();
                formData.append('file', file);

                btn.disabled = true;
                btn.textContent = "Conversion...";
                resultPre.textContent = "{}";
                messagesDiv.textContent = "";

                try {
                    const res = await fetch(endpoint, { method: 'POST', body: formData });
                    const type = res.headers.get('content-type') || '';

                    if (!res.ok) {
                        if (type.includes('application/json')) {
                            const err = await res.json();
                            if (err.detail && err.detail.messages)
                                messagesDiv.textContent = err.detail.messages.join(' | ');
                            else messagesDiv.textContent = JSON.stringify(err.detail || err);
                        } else messagesDiv.textContent = "Erreur serveur";
                        return;
                    }

                    const data = await res.json();
                    resultPre.textContent = JSON.stringify(data, null, 2);
                    if (data.messages?.length) messagesDiv.textContent = data.messages.join(' | ');
                }
                catch {
                    messagesDiv.textContent = "Erreur de connexion au serveur";
                }
                finally {
                    btn.disabled = false;
                    btn.textContent = "Convertir";
                }
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

    if not any(headers):
        raise HTTPException(status_code=400, detail="La première ligne doit contenir des en-têtes.")

    rows: List[Dict[str, Any]] = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        d: Dict[str, Any] = {}
        for idx, v in enumerate(row):
            name = headers[idx] if idx < len(headers) else f"col_{idx}"
            d[name] = v
        if any(v not in (None, "") for v in d.values()):
            rows.append(d)

    return rows


def rows_to_config_key_value(rows: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Colonnes minimales :
      - key
      - value
    Colonnes optionnelles :
      - required : yes/no
      - type : int/bool/url/string
    """
    config: Dict[str, Any] = {}
    messages: List[str] = []

    if not rows:
        messages.append("Aucune ligne de données.")
        return config, messages

    first = rows[0]
    if "key" not in first or "value" not in first:
        messages.append("Les colonnes 'key' et 'value' sont obligatoires.")
        return config, messages

    seen = set()

    for idx, row in enumerate(rows, start=2):
        key = row.get("key")
        value = row.get("value")
        required = str(row.get("required", "no")).strip().lower()
        value_type = str(row.get("type", "string")).strip().lower()

        if not key or str(key).strip() == "":
            messages.append(f"Ligne {idx}: clé vide — ignorée.")
            continue

        k = str(key).strip()

        if k in seen:
            messages.append(f"Ligne {idx}: clé '{k}' dupliquée — écrasement.")
        seen.add(k)

        if required == "yes" and (value is None or str(value) == ""):
            messages.append(f"Ligne {idx}: valeur obligatoire manquante pour '{k}'.")

        converted = value
        if value_type == "int":
            try:
                converted = int(value)
            except:
                messages.append(f"Ligne {idx}: '{k}' doit être un entier.")
        elif value_type == "bool":
            s = str(value).lower()
            if s in ["true","1","yes"]:
                converted = True
            elif s in ["false","0","no"]:
                converted = False
            else:
                messages.append(f"Ligne {idx}: '{k}' doit être un booléen (true/false).")
        elif value_type == "url":
            if not str(value).startswith(("http://","https://")):
                messages.append(f"Ligne {idx}: '{k}' doit être une URL valide (http/https).")

        config[k] = converted

    if not config:
        messages.append("Aucune entrée valide générée.")

    return config, messages


# ---------- API ----------

@app.post("/convert")
async def convert_excel_to_json(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Seuls les .xlsx sont supportés.")
    rows = parse_excel_to_json(await file.read())
    return JSONResponse(content={"rows": rows})


@app.post("/convert/config")
async def convert_excel_to_config(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Seuls les .xlsx sont supportés.")
    rows = parse_excel_to_json(await file.read())
    config, messages = rows_to_config_key_value(rows)

    if not config:
        raise HTTPException(status_code=400, detail={"messages": messages})

    return JSONResponse(content={"config": config, "messages": messages})
