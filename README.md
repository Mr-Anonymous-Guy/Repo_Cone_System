# 🚀 Repo_Clone_System

> *Because typing the same clone location over and over again is a crime against productivity.*

A small Python CLI utility that clones GitHub repositories while remembering where you usually clone them. It saves your previous locations and repository URLs so your future self has to type less and code more.

---

## ✨ Features

* 🔗 Clone any public GitHub repository
* 🔄 **Continuous clone mode**: Keep cloning multiple repositories without restarting the app
* 🚪 **Type "exit" anytime at repository prompt**: Gracefully quit the application whenever you are done
* ⌨️ **Interactive Arrow-Key Destination Menu**: Navigate using ↑ and ↓ arrow keys, press Enter to select, or Esc to cancel
* 📂 **Automatic Previous Locations**: Instant access to your last used location and clone history
* 📁 **Optional creation of a new destination folder**: Safely create a single missing folder level with Y/N confirmation
* 🧠 **Memory system**: Automatically stores clone history in `memory.json` without duplicates
* 📌 **Folder conflict handling**: Detects existing folder names and prompts you to choose another name
* ⚠️ Handles common Git errors:
  * Repository not found
  * Invalid GitHub URL
  * Private repositories
  * No internet connection
  * Git not installed
* 🛠️ Automatically creates required files on first run

---

## 📦 Requirements & Installation

* Python 3.8+
* Git installed and added to your system PATH
* `questionary` Python package

Install dependencies:

```bash
pip install questionary
```

Check Git installation:

```bash
git --version
```

---

## ▶️ Usage

Run the script:

```bash
python app.py
```

Example session:

```text
============================================================
GitHub Repository Cloner
============================================================

GitHub Repository URL
> https://github.com/facebook/react.git

Choose Clone Destination

❯ ➕ New Location

  🕒 Last Used
    D:\Projects

────────────────────

  D:\Projects
  D:\Learning
  E:\Github
  F:\College

Cloning repository...

============================================================
Repository cloned successfully!
============================================================

Repository : react
Folder     : react
Location   : D:\Projects\react

------------------------------------------
Ready for another repository.
(Type 'exit' to quit.)
------------------------------------------

GitHub Repository URL
> exit

Thanks for using Repo_Clone_System!
Goodbye.
```

---

## 📋 Interactive Destination Selector

The destination selector provides a terminal interface built dynamically from `memory.json`:

```text
Choose Clone Destination

❯ ➕ New Location

  🕒 Last Used
    D:\Projects

────────────────────

  D:\Projects
  D:\Learning
  E:\Github
  F:\College
```

### Controls & Features:
* **Arrow keys (↑ / ↓)**: Navigate options seamlessly
* **Enter**: Confirm selection
* **Esc**: Cancel selection and return to the repository prompt
* **Automatic history menu**: Displays all previously saved clone locations without duplicates
* **Previous locations**: Instantly select your last used directory (`🕒 Last Used`) or any item from history without confirmation

---

## 🧠 Memory System

The project automatically creates a `memory.json` file the first time you run it.

Example `memory.json`:

```json
{
    "last_location": "D:\\Projects",
    "locations": [
        "D:\\Projects",
        "D:\\Learning",
        "E:\\Github",
        "F:\\College"
    ],
    "repositories": [
        "https://github.com/facebook/react.git",
        "https://github.com/vercel/next.js.git"
    ]
}
```

The script remembers:

* Your last clone location (`last_location`)
* Every unique location you've used (`locations`)
* Every repository you've cloned (`repositories`)

---

## 📂 Folder Conflict?

If a folder with the same repository name already exists, the script won't overwrite it.

Instead, it'll politely ask:

```text
Folder 'react' already exists.
Enter another folder name
>
```

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
