#grblCommander

## `macros` folder

This folder contains all the macros available to grblCommander:

* Only `*.py` files inside this folder and its subfolders will be considered as macros
* File name will be used as macro name
* Folder names will be joined using dots to form a path (e.g. `gc.start`)

Default folders:

* `def`: grblCommander *default* **internal** macros
* `demo`: sample macros to start learning
* `u`: user macros (initially empty)

Further information can be found in the `README.md` files inside these folders.

User macro files can directly placed in this folder but it is recommended to use the `u` (*user*) folder and even create subfolders inside to organize code.
