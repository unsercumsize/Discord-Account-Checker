# Discord Admin Checker

A small desktop app built with CustomTkinter to check your Discord token and categorize the servers you have access to.

## What it does

- Uses a Discord user token to fetch account info
- Loads your joined servers
- Shows which servers you own, where you have admin permissions, moderator rights, or just normal membership
- Lets you click through categories and see server details

## Requirements

- Python 3.8 or newer
- `tkinter` (usually included with Python on Windows)
- `customtkinter`
- `requests`
- `Pillow`

## Setup

1. Clone or download this repository.
2. Open a terminal in the project folder.
3. Install the dependencies:

```powershell
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

or
```cmd/terminal
python main.py
```


Then paste in your Discord token, click `Check Admin Servers`, and wait for the app to load your servers.

## Important

- This app requires a valid Discord user token.
- Only use your own token and follow Discord's terms of service.

## Files

- `main.py` — app source code
- `requirements.txt` — dependency list
