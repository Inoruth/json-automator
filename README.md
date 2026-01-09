# JSON Automator

Convert **Excel (.xlsx)** configuration sheets into **clean, validated JSON** — without writing JSON by hand.

> Excel is treated as an **input UI**, not a long‑term source of truth.
> If something is wrong, fix the sheet (or schema) and regenerate.

---

## 🚀 Live demo

➡️ **Web app:** [https://json-automator.up.railway.app](https://json-automator.up.railway.app)

* No account
* Free beta
* Upload Excel → get JSON

---

## ✨ Why JSON Automator exists

Many teams still manage configuration in Excel:

* API settings
* feature flags
* application parameters
* environment configs

Then someone has to:

* copy / paste
* rewrite JSON manually
* guess types
* debug production issues caused by small mistakes

JSON Automator removes that friction.

> **Excel in → validated JSON out.**

---

## 🧠 Core idea

* Excel is **easy to edit** by non‑developers
* JSON is **safe and explicit** for applications
* The tool sits between both

JSON is **always generated**, never edited by hand.

---

## 🧩 Supported modes

### 1️⃣ Rows mode (debug)

Exports each Excel row as raw JSON using the header names.

Useful to:

* inspect how the file is parsed
* debug messy or unknown sheets

Example:

```json
{
  "data": {
    "Sheet1": [
      { "name": "Alice", "age": 22 },
      { "name": "Bob", "age": 28 }
    ]
  },
  "messages": []
}
```

---

### 2️⃣ Config key/value mode (validated)

Designed for configuration files.

#### Required columns

| column  | description     |
| ------- | --------------- |
| `key`   | config key name |
| `value` | config value    |

#### Optional columns

| column     | allowed values            | purpose                  |
| ---------- | ------------------------- | ------------------------ |
| `required` | yes / no                  | marks value as mandatory |
| `type`     | int / bool / url / string | automatic validation     |

Example Excel:

| key       | value                                              | required | type |
| --------- | -------------------------------------------------- | -------- | ---- |
| api_url   | [https://api.example.com](https://api.example.com) | yes      | url  |
| timeout   | 30                                                 | no       | int  |
| use_cache | true                                               | no       | bool |

Generated JSON:

```json
{
  "data": {
    "api_url": "https://api.example.com",
    "timeout": 30,
    "use_cache": true
  },
  "messages": []
}
```

---

## 🔎 Validation rules

JSON Automator checks:

* duplicate keys
* missing required values
* integer / boolean mismatches
* invalid URLs
* empty or inconsistent cells

Errors are **explicit** and shown to the user so the Excel file can be fixed.

---

## 🧱 Current limitations

* Best suited for **flat or lightly‑nested** configs
* Deep / complex nesting is **not automatic yet**
* Excel structure must remain consistent

These constraints are **intentional** to keep behavior predictable.

---

## 🧪 Schema direction (in progress)

Based on early feedback, the next evolution is **schema‑driven validation**:

* teams define a schema (keys, types, required fields, aliases)
* Excel uploads are validated against it
* JSON is always regenerated from Excel + schema

This makes:

* Excel a controlled input UI
* schema the real source of truth
* JSON fully reproducible

---

## 🛠 Tech stack

* FastAPI
* OpenPyXL
* Uvicorn
* Railway
* Vanilla HTML / JS

Simple by design.

---

## 🧭 Roadmap

* Download generated JSON
* Public API (POST Excel → JSON)
* Schema support
* Saved templates
* Paid plan for teams (limits, schemas, API)

---

## 🤝 Feedback & contributions

Ideas, issues, and PRs are welcome.

If reporting a bug, please include:

1. Excel structure
2. minimal example
3. error message

➡️ [https://github.com/Djelloul94380/json-automator/issues](https://github.com/Inoruth/json-automator/issues)

---

## 📄 License

Free during beta.

---

## ❤️ Author

Built by **Djelloul**.

If this tool saves you time, feedback is appreciated — it directly shapes the next features.
