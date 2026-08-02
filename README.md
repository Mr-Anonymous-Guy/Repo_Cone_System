# 🚀 Repo_Clone_System

> *Because typing the same clone location over and over again is a crime against productivity.*

A small Python CLI utility that clones GitHub repositories while remembering where you usually clone them. It saves your previous locations and repository URLs so your future self has to type less and code more.

---

## ✨ Features

* 🔗 Clone any public GitHub repository
* 📂 Remembers your last clone location
* 🧠 Stores clone history in a simple `memory.json`
* 📌 Reuse your previous location by simply pressing **Enter**
* 📁 Detects existing folder names and lets you choose another
* ⚠️ Handles common Git errors:

  * Repository not found
  * Invalid GitHub URL
  * Private repositories
  * No internet connection
  * Git not installed
* 🛠️ Automatically creates required files on first run

---

## 📦 Requirements

* Python 3.8+
* Git installed and added to your system PATH

Check Git installation:

```bash
git --version
```

---

## ▶️ Usage

Run the script:

```bash
python clone.py
```

Example:

```text
============================================================
GitHub Repository Cloner
============================================================

GitHub Repository URL
> https://github.com/facebook/react.git

Destination Folder
(Leave blank to use previous location)
> D:\Projects

Cloning repository...

============================================================
Repository cloned successfully!
============================================================

Repository : react
Folder     : react
Location   : D:\Projects\react
```

---

## 🧠 Memory System

The project automatically creates a `memory.json` file the first time you run it.

Example:

```json
{
    "last_location": "D:\\Projects",
    "locations": [
        "D:\\Projects",
        "E:\\Learning"
    ],
    "repositories": [
        "https://github.com/facebook/react.git",
        "https://github.com/vercel/next.js.git"
    ]
}
```

The script remembers:

* Your last clone location
* Every unique location you've used
* Every repository you've cloned

No database.
No setup.
Just one tiny JSON file.

---

## 📂 Folder Conflict?

If a folder with the same repository name already exists, the script won't overwrite it.

Instead, it'll politely ask:

> "Hey... that folder already exists. Want to give it another name?"

Because deleting your projects without asking would be rude.

---

## 🤔 Why?

Me:

> *"I'll only clone one repository today."*

Also me, 30 minutes later:

```
git clone ...
git clone ...
git clone ...
git clone ...
git clone ...
```

After typing the same destination folder for the 18th time...

**Repo_Clone_System was born.**

---

## 📌 Future Ideas

* ⭐ Clone from history
* ⭐ Favorite locations
* ⭐ Search previous repositories
* ⭐ Open cloned project in VS Code
* ⭐ Clone statistics
* ⭐ Interactive terminal menu
* ⭐ GUI version

---

## 🤝 Contributing

Feel free to fork the project, improve it, or add your own ideas.

Pull requests are always welcome.

---

## 📜 License

Use it.
Modify it.
Break it.
Fix it.

Just don't blame the script if you accidentally clone the wrong repository. 😄
