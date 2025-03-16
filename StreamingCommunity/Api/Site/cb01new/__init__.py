# 09.06.24

from urllib.parse import quote_plus


# External library
from rich.console import Console
from rich.prompt import Prompt


# Internal utilities
from StreamingCommunity.Api.Template import get_select_title
from StreamingCommunity.TelegramHelp.telegram_bot import get_bot_instance


# Logic class
from StreamingCommunity.Api.Template.config_loader import site_constant
from .site import title_search, media_search_manager, table_show_manager
from .film import download_film


# Variable
indice = 9
_useFor = "film"
_deprecate = False
_priority = 2
_engineDownload = "mp4"

msg = Prompt()
console = Console()


def search(string_to_search: str = None, get_onylDatabase: bool = False):
    """
    Main function of the application for film and series.
    """

    if site_constant.TELEGRAM_BOT:

        bot = get_bot_instance()

        if string_to_search is None:

            # Chiedi la scelta all'utente con il bot Telegram
            string_to_search = bot.ask(
                "key_search",
                f"Inserisci la parola da cercare\noppure back per tornare alla scelta: ",
                None
            )

    else:
      if string_to_search is None:
          string_to_search = msg.ask(f"\n[purple]Insert word to search in [green]{site_constant.SITE_NAME}").strip()

    # Search on database
    len_database = title_search(quote_plus(string_to_search))

    # Return list of elements
    if get_onylDatabase:
        return media_search_manager

    if len_database > 0:

        # Select title from list
        select_title = get_select_title(table_show_manager, media_search_manager)

        # !!! ADD TYPE DONT WORK FOR SERIE
        download_film(select_title)


    else:
        if site_constant.TELEGRAM_BOT:
          bot.send_message(f"Nessun risultato trovato riprova", None)

        console.print(f"\n[red]Nothing matching was found for[white]: [purple]{string_to_search}")

        # Retry
        search()