# 🚀 Repo_Clone_System

> *Because typing the same clone location over and over again is a crime against productivity.*

A small Python CLI utility that clones GitHub repositories while remembering where you usually clone them. It saves your previous locations and repository URLs so your future self has to type less and code more.

---

## ✨ Features

* 🔗 Clone any public GitHub repository
* 🔄 **Continuous clone mode**: Keep cloning multiple repositories without restarting the app
* 🚪 **Type "exit" anytime at repository prompt**: Gracefully quit the application whenever you are done
* 📂 **Automatic previous-location reuse**: Press Enter to instantly use your last used destination location without confirmation prompts
* 📁 **Optional creation of a new destination folder**: Safely create a single missing folder level with Y/N confirmation
* 🧠 **Memory system**: Automatically stores clone history in `memory.json`
* 📌 **Folder conflict handling**: Detects existing folder names and prompts you to choose another name
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
python app.py
```

Example session:

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

## 🧠 Memory System

The project automatically creates a `memory.json` file the first time you run it.

Pressing **ENTER** at the destination prompt automatically uses the last location stored in `memory.json`.

Example `memory.json`:

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

---

## 💡 Examples

### Automatic Previous Location Reuse

```text
Destination Folder
(Leave blank to use previous location)
>

Using previous location:
D:\Projects
```

### Folder Creation (One Level)

```text
Destination Folder
(Leave blank to use previous location)
> D:\Projects\Python

Folder does not exist.

Would you like to create it?
(Y/N): Y

Folder created successfully.
```

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
