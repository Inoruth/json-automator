# JSON Automator

Convertissez vos fichiers **Excel (.xlsx)** en **JSON propre et validé**, sans écrire une seule ligne à la main.

👉 Idéal pour les équipes qui conservent leurs configurations dans Excel
👉 Fini les erreurs d'inattention, virgules manquantes et champs obligatoires oubliés
👉 Gratuit pendant la phase bêta

---

## 🚀 Essayez en ligne

➡️ **App en ligne :** [https://json-automator.up.railway.app](https://json-automator.up.railway.app)

Aucun compte.
Téléversez un fichier, obtenez un JSON propre — c’est tout.

---

## ✨ Pourquoi cet outil ?

Beaucoup d’équipes (dev, ops, industrie, formation…) utilisent encore Excel pour gérer leurs paramètres.

Puis quelqu’un doit :

* copier/coller
* reformater en JSON
* vérifier les types à la main
* corriger les erreurs

➡️ **Perte de temps**
➡️ **Risque d’erreurs**

JSON Automator automatise ce travail.

> **Vous importez un Excel → vous recevez un JSON validé.**

---

## 🧩 Formats acceptés

### 1️⃣ Mode debug — export brut (`rows`)

Export direct des données sous forme de lignes JSON :

```json
{
  "rows": [
    { "name": "Alice", "age": 22 },
    { "name": "Bob", "age": 28 }
  ]
}
```

Pratique pour vérifier la lecture du fichier.

---

### 2️⃣ Mode configuration (`config`)

Votre fichier Excel doit contenir au minimum :

| colonne | obligatoire | description      |
| ------- | ----------- | ---------------- |
| `key`   | ✔           | nom du paramètre |
| `value` | ✔           | valeur           |

Colonnes optionnelles :

| colonne    | type                      | rôle                   |
| ---------- | ------------------------- | ---------------------- |
| `required` | yes / no                  | valeur obligatoire     |
| `type`     | int / bool / url / string | validation automatique |

Exemple JSON généré :

```json
{
  "config": {
    "api_url": "https://api.example.com",
    "timeout": 30,
    "use_cache": true
  },
  "messages": []
}
```

Et si quelque chose ne va pas, vous obtenez des messages explicites :

```json
{
  "messages": [
    "Ligne 4: valeur obligatoire manquante pour 'token'",
    "Ligne 5: 'timeout' doit être un entier."
  ]
}
```

---

## 🔎 Validation automatique incluse

JSON Automator vérifie :

✔ clés dupliquées
✔ valeurs obligatoires manquantes
✔ entiers invalides
✔ booléens incohérents (`yes/no`, `true/false`, etc.)
✔ URL non valides

---

## 🛠️ Stack technique

* **FastAPI** — backend
* **OpenPyXL** — lecture Excel
* **Uvicorn** — serveur
* **Railway** — hébergement
* UI simple — HTML / JS vanilla

Le projet reste volontairement simple pour rester fiable.

---

## 🧭 Roadmap (bêta)

* ⏳ téléchargement du JSON généré
* ⏳ API publique (POST avec fichier)
* ⏳ sauvegarde de modèles
* ⏳ compte PRO (limites élevées + fonctionnalités avancées)

> Vous avez une idée utile ?
> **Ouvrez une issue ou laissez un commentaire !**

👉 [https://github.com/Djelloul94380/json-automator/issues](https://github.com/Djelloul94380/json-automator/issues)

---

## 🤝 Contribuer / signaler un bug

Les PRs et retours sont bienvenus.

Avant d’ouvrir une issue, merci de :

1. décrire votre fichier Excel
2. fournir un exemple minimal
3. coller le message d’erreur

---

## 📄 Licence

Projet en bêta — usage libre pendant la phase de test.

---

## ❤️ Auteur

Développé par **Djelloul** — curieux d’automatisation, simplicité et outils utiles.

Si vous utilisez JSON Automator, dites-le — ça motive énormément 🙂
