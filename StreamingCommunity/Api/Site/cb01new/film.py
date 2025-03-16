# 03.07.24

import os


# External library
from rich.console import Console


# Internal utilities
from StreamingCommunity.Util.os import os_manager
from StreamingCommunity.Util.message import start_message
from StreamingCommunity.Lib.Downloader import HLS_Downloader
from StreamingCommunity.TelegramHelp.telegram_bot import TelegramSession, get_bot_instance


# Logic class
from StreamingCommunity.Api.Template.config_loader import site_constant
from StreamingCommunity.Api.Template.Class.SearchType import MediaItem


# Player
from StreamingCommunity.Api.Player.maxstream import VideoSource


# Variable
console = Console()


def download_film(select_title: MediaItem) -> str:
    """
    Downloads a film using the provided obj.

    Parameters:
        - select_title (MediaItem): The media item to be downloaded. This should be an instance of the MediaItem class, containing attributes like `name` and `url`.

    Return:
        - str: output path
    """

    if site_constant.TELEGRAM_BOT:
        bot = get_bot_instance()

    start_message()
    console.print(f"[yellow]Download:  [red]{select_title.name} \n")

    if site_constant.TELEGRAM_BOT:
      bot.send_message(f"Download in corso:\nTitolo:{select_title.name}", None)

      # Get script_id
      script_id = TelegramSession.get_session()
      if script_id != "unknown":
          TelegramSession.updateScriptId(script_id, f"{select_title.name}")

    # Setup api manger
    video_source = VideoSource(select_title.url)

    # Define output path
    title_name = os_manager.get_sanitize_file(select_title.name) +".mp4"
    mp4_path = os.path.join(site_constant.MOVIE_FOLDER, title_name.replace(".mp4", ""))

    # Get m3u8 master playlist
    master_playlist = video_source.get_playlist()

    # Download the film using the m3u8 playlist, and output filename
    r_proc = HLS_Downloader(
        m3u8_url=master_playlist, 
        output_path=os.path.join(mp4_path, title_name)
    ).start()

    if site_constant.TELEGRAM_BOT:
        bot.send_message(f"Finito di scaricare tutto", None)

        # Get script_id
        script_id = TelegramSession.get_session()
        if script_id != "unknown":
            TelegramSession.deleteScriptId(script_id)

    if r_proc['error'] is not None:
        try: os.remove(r_proc['path'])
        except: pass

    return r_proc['path']