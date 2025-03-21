# 03.07.24

import sys


# External libraries
import httpx
from bs4 import BeautifulSoup
from rich.console import Console


# Internal utilities
from StreamingCommunity.Util.config_json import config_manager
from StreamingCommunity.Util.headers import get_userAgent
from StreamingCommunity.Util.table import TVShowManager


# Logic class
from StreamingCommunity.Api.Template.config_loader import site_constant
from StreamingCommunity.Api.Template.Util import search_domain
from StreamingCommunity.Api.Template.Class.SearchType import MediaManager
from StreamingCommunity.TelegramHelp.telegram_bot import get_bot_instance


# Variable
console = Console()
media_search_manager = MediaManager()
table_show_manager = TVShowManager()
max_timeout = config_manager.get_int("REQUESTS", "timeout")


def title_search(word_to_search: str) -> int:
    """
    Search for titles based on a search query.

    Parameters:
        - title_search (str): The title to search for.

    Returns:
        - int: The number of titles found.
    """
    if site_constant.TELEGRAM_BOT:
        bot = get_bot_instance()

    media_search_manager.clear()
    table_show_manager.clear()

    # Check if domain is working
    domain_to_use, base_url = search_domain(site_constant.SITE_NAME, site_constant.FULL_URL)

    if domain_to_use is None or base_url is None:
        console.print("[bold red]Error: Unable to determine valid domain or base URL.[/bold red]")
        console.print("[yellow]The service might be temporarily unavailable or the domain may have changed.[/yellow]")
        sys.exit(1)

    search_url = f"{site_constant.FULL_URL}/?s={word_to_search}"
    console.print(f"[cyan]Search url: [yellow]{search_url}")

    try:
        response = httpx.get(url=search_url, headers={'user-agent': get_userAgent()}, timeout=max_timeout, follow_redirects=True)
        response.raise_for_status()

    except Exception as e:
        console.print(f"Site: {site_constant.SITE_NAME}, request search error: {e}")

    # Create soup and find table
    soup = BeautifulSoup(response.text, "html.parser")

    # Inizializza la lista delle scelte
    if site_constant.TELEGRAM_BOT:
        choices = []

    for div in soup.find_all("div", class_ = "card-content"):
        try:

            url = div.find("h3").find("a").get("href")
            title = div.find("h3").find("a").get_text(strip=True)
            desc = div.find("p").find("strong").text

            title_info = {
                'name': title,
                'desc': desc,
                'url': url
            }

            media_search_manager.add_media(title_info)

            if site_constant.TELEGRAM_BOT:

                # Crea una stringa formattata per ogni scelta con numero
                choice_text = f"{len(choices)} - {title_info.get('name')} ({title_info.get('desc')}) - url: {title_info.get('url')}"
                choices.append(choice_text)

        except Exception as e:
            print(f"Error parsing a film entry: {e}")

    if site_constant.TELEGRAM_BOT:
        if choices:
            bot.send_message(f"Lista dei risultati:", choices)

    # Return the number of titles found
    return media_search_manager.get_length()