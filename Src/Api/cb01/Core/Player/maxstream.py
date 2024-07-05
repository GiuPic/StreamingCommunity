# 05.07.24

import re
import sys
import logging


# External libraries
import httpx
from bs4 import BeautifulSoup


# Internal utilities
from Src.Util.headers import get_headers
from Src.Util.os import run_node_script, run_node_script_api


class VideoSource:
    def __init__(self, url: str):
        """
        Sets up the video source with the provided URL.

        Args:
            url (str): The URL of the video.
        """
        self.url = url
        self.redirect_url = None
        self.maxstream_url = None
        self.m3u8_url = None
        self.headers = {'user-agent': get_headers()}

    def get_redirect_url(self):
        """
        Sends a request to the initial URL and extracts the redirect URL.
        """
        try:

            # Send a GET request to the initial URL
            response = httpx.get(self.url, headers=self.headers, follow_redirects=True, timeout=10)
            response.raise_for_status()

            # Extract the redirect URL from the HTML
            soup = BeautifulSoup(response.text, "html.parser")
            self.redirect_url = soup.find("div", id="iframen1").get("data-src")
            logging.info(f"Redirect URL: {self.redirect_url}")

            return self.redirect_url
        
        except httpx.RequestError as e:
            logging.error(f"Error during the initial request: {e}")
            raise

        except AttributeError as e:
            logging.error(f"Error parsing HTML: {e}")
            raise

    def get_maxstream_url(self):
        """
        Sends a request to the redirect URL and extracts the Maxstream URL.
        """
        if not self.redirect_url:
            raise ValueError("Redirect URL not found. Please call get_redirect_url() first.")

        try:
            # Send a GET request to the redirect URL
            response = httpx.get(self.redirect_url, headers=self.headers, follow_redirects=True, timeout=10)
            response.raise_for_status()

            # Extract the Maxstream URL from the HTML
            soup = BeautifulSoup(response.text, "html.parser")
            maxstream_url = soup.find("a")
            
            if maxstream_url is None:

                # If no anchor tag is found, try the alternative method
                logging.warning("Anchor tag not found. Trying the alternative method.")
                headers = {
                    'origin': 'https://stayonline.pro',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/111.0.0.0',
                    'x-requested-with': 'XMLHttpRequest',
                }

                # Make request to stayonline api
                data = {'id': self.redirect_url.split("/")[-2], 'ref': ''}
                response = httpx.post('https://stayonline.pro/ajax/linkEmbedView.php', headers=headers, data=data)
                response.raise_for_status()
                uprot_url = response.json()['data']['value']

                # Retry getting maxtstream url
                response = httpx.get(uprot_url, headers=self.headers, follow_redirects=True, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                maxstream_url = soup.find("a").get("href")
                
            else:
                maxstream_url = maxstream_url.get("href")

            self.maxstream_url = maxstream_url
            logging.info(f"Maxstream URL: {self.maxstream_url}")

            return self.maxstream_url
        
        except httpx.RequestError as e:
            logging.error(f"Error during the request to the redirect URL: {e}")
            raise

        except AttributeError as e:
            logging.error(f"Error parsing HTML: {e}")
            raise

    def get_m3u8_url(self):
        """
        Sends a request to the Maxstream URL and extracts the .m3u8 file URL.
        """
        if not self.maxstream_url:
            raise ValueError("Maxstream URL not found. Please call get_maxstream_url() first.")

        try:
            # Send a GET request to the Maxstream URL
            response = httpx.get(self.maxstream_url, headers=self.headers, follow_redirects=True, timeout=10)
            response.raise_for_status() 
            soup = BeautifulSoup(response.text, "html.parser")

            # Iterate over all script tags in the HTML
            for script in soup.find_all("script"):
                if "eval(function(p,a,c,k,e,d)" in script.text:

                    # Execute the script using the run_node_script_api function
                    text_run_node_js = run_node_script_api(script.text)

                    # Extract the .m3u8 URL from the script's output
                    m3u8_match = re.search(r'src:"(https://.*?\.m3u8)"', text_run_node_js)

                    if m3u8_match:
                        self.m3u8_url = m3u8_match.group(1)
                        logging.info(f"M3U8 URL: {self.m3u8_url}")
                        break

            return self.m3u8_url

        except Exception as e:
            logging.error(f"Error executing the Node.js script: {e}")
            raise

    def get_playlist(self):
        """
        Executes the entire flow to obtain the final .m3u8 file URL.
        """
        self.get_redirect_url()
        self.get_maxstream_url()
        return self.get_m3u8_url()
