# 10.12.23

import sys
import os
import platform
import argparse

from typing import Callable


# Internal utilities
from Src.Util.message import start_message
from Src.Util.console import console, msg
from Src.Util._jsonConfig import config_manager
from Src.Upload.update import update as git_update
from Src.Util.os import get_system_summary
from Src.Util.logger import Logger


# Internal api
from Src.Api.Streamingcommunity import main_film_series as streamingcommunity_film_serie
from Src.Api.Animeunity import main_anime as streamingcommunity_anime
from Src.Api.Altadefinizione import main_film as altadefinizione_film
from Src.Api.Ddlstreamitaly import title_search as ddlstreamitaly_film_serie
from Src.Api.Guardaserie import title_search as guardaserie_serie


# Config
CLOSE_CONSOLE = config_manager.get_bool('DEFAULT', 'not_close')


def run_function(func: Callable[..., None], close_console: bool = False) -> None:
    """
    Run a given function indefinitely or once, depending on the value of close_console.

    Parameters:
        func (Callable[..., None]): The function to run.
        close_console (bool, optional): Whether to close the console after running the function once. Defaults to False.
    """
    if close_console:
        while 1:
            func()
    else:
        func()


def initialize():
    """
    Initialize the application.
    Checks Python version, removes temporary folder, and displays start message.
    """

    start_message()

    # Create logger
    log_not = Logger()

    # Get system info
    get_system_summary()

    # Set terminal size for win 7
    if platform.system() == "Windows" and "7" in platform.version():
        os.system('mode 120, 40')

    # Check python version
    if sys.version_info < (3, 7):
        console.log("[red]Install python version > 3.7.16")
        sys.exit(0)

    # Attempting GitHub update
    try:
        git_update()
    except Exception as e:
        console.print(f"[blue]Req github [white]=> [red]Failed: {e}")


def main():

    initialize()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Script to download film and series from the internet.')
    parser.add_argument('-sa', '--streaming_anime', action='store_true', help='')
    parser.add_argument('-sf', '--streaming_film', action='store_true', help='')
    args = parser.parse_args()

    # Mapping command-line arguments to functions
    arg_to_function = {
        'streaming_anime': streamingcommunity_anime,
        'streaming_film': streamingcommunity_film_serie,
    }

    # Check which argument is provided and run the corresponding function
    for arg, func in arg_to_function.items():
        if getattr(args, arg):
            run_function(func, CLOSE_CONSOLE)
            return

    # Mapping user input to functions
    input_to_function = {
        '0': streamingcommunity_film_serie,
        '1': streamingcommunity_anime,
        '2': altadefinizione_film,
        '3': ddlstreamitaly_film_serie,
        '4': guardaserie_serie,
    }

    # Create dynamic prompt message and choices
    choices = list(input_to_function.keys())
    choice_labels = {
        '0': "Streamingcommunity",
        '1': "Animeunity",
        '2': "Altadefinizione",
        '3': "Ddlstreamitaly",
        '4': "Guardaserie",
    }
    prompt_message = "[cyan]Insert category [white](" + ", ".join(
        f"[red]{key}[white]: [bold magenta]{label}[white]" for key, label in choice_labels.items()
    ) + ")[white]:[/cyan]"

    # Ask the user for input
    category = msg.ask(prompt_message, choices=choices, default="0")

    # Run the corresponding function based on user input
    if category in input_to_function:
        run_function(input_to_function[category], CLOSE_CONSOLE)
    else:
        console.print("[red]Invalid category.")
        sys.exit(0)


if __name__ == '__main__':
    main()