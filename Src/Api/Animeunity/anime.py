# 11.03.24

import os
import logging


# Internal utilities
from Src.Util.console import console, msg
from Src.Util._jsonConfig import config_manager
from Src.Lib.Hls.downloader import Downloader
from Src.Util.message import start_message


# Logic class
from .Core.Player.vixcloud import VideoSource
from .Core.Util import manage_selection


# Config
ROOT_PATH = config_manager.get('DEFAULT', 'root_path')
from .costant import MAIN_FOLDER, SERIES_FOLDER, MOVIE_FOLDER


# Variable
video_source = VideoSource()



def download_episode(index_select: int):
    """
    Downloads the selected episode.

    Args:
        - index_select (int): Index of the episode to download.
    """

    # Get information about the selected episode
    obj_episode = video_source.get_info_episode(index_select)

    start_message()
    console.print(f"[yellow]Download:  [red]EP_{obj_episode.number} \n")

    # Get the embed URL for the episode
    embed_url = video_source.get_embed(obj_episode.id)

    # Parse parameter in embed text
    video_source.parse_script(embed_url)

    # Create output path
    mp4_path = None
    mp4_name = f"{index_select + 1}.mp4"
    if video_source.is_series:
        mp4_path = os.path.join(ROOT_PATH, MAIN_FOLDER, SERIES_FOLDER, video_source.series_name)
    else:
        mp4_path = os.path.join(ROOT_PATH, MAIN_FOLDER, MOVIE_FOLDER, video_source.series_name)

    # Start downloading
    Downloader(
        m3u8_playlist = video_source.get_playlist(),
        output_filename = os.path.join(mp4_path, mp4_name)
    ).start()


def donwload_series(tv_id: int, tv_name: str):
    """
    Function to download episodes of a TV series.

    Args:
        - tv_id (int): The ID of the TV series.
        - tv_name (str): The name of the TV series.
    """

    # Set up video source
    video_source.setup(
        media_id = tv_id,
        series_name = tv_name
    )

    # Get the count of episodes for the TV series
    episoded_count = video_source.get_count_episodes()
    console.log(f"[cyan]Episodes find: [red]{episoded_count}")

    # Prompt user to select an episode index
    last_command = msg.ask("\n[cyan]Insert media [red]index [yellow]or [red](*) [cyan]to download all media [yellow]or [red][1-2] [cyan]for a range of media")

    # Manage user selection
    list_episode_select = manage_selection(last_command, episoded_count)

    # Download selected episodes
    if len(list_episode_select) == 1 and last_command != "*":
        download_episode(list_episode_select[0]-1)

    # Download all other episodes selecter
    else:
        for i_episode in list_episode_select:
            download_episode(i_episode-1)


def donwload_film(id_film: int, title_name: str):
    """
    Function to download a film.

    Args:
        - id_film (int): The ID of the film.
        - title_name (str): The title of the film.
    """

    # Set up video source
    video_source.setup(
        media_id = id_film,
        series_name = title_name  
    )
    video_source.is_series = False

    # Start download
    download_episode(0)
