# Hiding Wumpus

A hide-and-seek sort of game where one NPC hides from you or another NPC.

For CPSC 481 Spring 2025.

## How to run it (Windows)

Follow these instructions if you want to run Hiding Wumpus on your own computer using its minimal requirements. If you want to run it in Visual Studio Code instead, follow the "Development quick start" instructions. 

1. Make sure Python 3.12.3 or 3.13.3 is installed. Slightly different Python versions may work just fine, but I can only guarantee that those two versions work. If you type the `python --version` into your command prompt and see that the version matches, you may continue.
1. Open a command prompt and `cd` into the project directory.
1. Create a Python virtual environment with the `python -m venv .venv` command.
1. Active the Python virtual environment with the `.\.venv\Scripts\activate.bat` command.
1. Install the required Python packages with the `pip install -r requirements.txt` command.
1. Run the program with the `python main.py` command. You should see the window come up.

## Development quick start

1. Clone this repository.
1. Make a virtual python environment and install the required python packages.
    - If you open this project in Visual Sudio Code, you can open one of the python files,
    click the Python in the status bar at the bottom of the screen, click "Create Virtual Environment...",
    choose your Python version (3.12.3 is preferred), and it will also guide you to install the required packages in requirements.txt.
    - Alternatively, you can do this in the terminal. Run `python -m venv .venv` to make a new virtual environment in the ".venv" directory, then activate it using one of the activation scripts inside (for Windows Command Prompt, it's `.\.venv\Scripts\activate.bat`, for others [see here](https://docs.python.org/3/library/venv.html)), then run `pip install -r requirements.txt`.
    - If you want Visual Studio's syntax highlighting and autocompletion to work well, you'll need to tell it to use the virtual environment.
1. Run the program by typing `python main.py` in the terminal.

## Disclaimer

This project stems from a basic LLM-generated A* pathfinding algorithm visualizer.

This is what that looked like:

![screenshot](starting-point-screenshot.png)

The prompt used can be found here:

https://claude.ai/share/29d68079-5a93-470c-a7d1-ed13229672ea
