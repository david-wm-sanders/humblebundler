"""Gets a Humble Bundle

Usage:
    get_bundle.py <htmlpath> <outputdir>
"""

import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from docopt import docopt


if __name__ == '__main__':
    args = docopt(__doc__)

    # Load and parse the html file
    html_p = Path(args["<htmlpath>"])
    with html_p.open(mode="r", encoding="utf-8") as html_f:
        html_doc = html_f.read()
    soup = BeautifulSoup(html_doc, "html.parser")

    # Find all download button divs, exit fast if zero found
    download_btn_divs = soup.find_all("div", class_="flexbtn active noicon js-start-download")
    if not download_btn_divs:
        print("No download button divs found in provided HTML file... exiting.")
        sys.exit(1)

    # Filter out buttons for PDF and video (Download) files, exit fast if zero found
    valid_span_values = ["PDF", "Download"]
    links = []
    for dl_btn_div in download_btn_divs:
        if dl_btn_div.span.text in valid_span_values:
            links.append(dl_btn_div.a["href"])
    if not links:
        print(f"No download links for {valid_span_values}... exiting.")
        sys.exit(1)

    # Setup output directory
    dir_p = Path(args["<outputdir>"])
    dir_torrents_p = dir_p / "torrents"
    if not dir_torrents_p.exists():
        dir_torrents_p.mkdir(parents=True, exist_ok=True)

    # Download the .torrent files with requests, exit fast if zero downloaded
    torrent_paths = []
    for link in links:
        # Extract the filename from the link URL
        filename = urlparse(link).path.split("/")[-1]
        torrent_p = dir_torrents_p / filename
        if torrent_p.exists():
            print(f"Skipping '{filename}' as it exists already")
        else:
            # Make a get request for the torrent file
            print(f"Downloading '{filename}'...")
            r = requests.get(link, stream=True)
            with torrent_p.open(mode='wb') as f:
                for chunk in r.iter_content(chunk_size=128):
                    f.write(chunk)
        torrent_paths.append((filename, str(torrent_p)))
    if not torrent_paths:
        print("No torrents download... exiting.")
        sys.exit(1)

    # Fire up deluged
    print("Firing up deluged...")
    subprocess.run(["deluged"])

    # Add torrents to deluge
    deluge_add_command = ["deluge-console", "add", "-p", str(dir_p)]
    deluge_add_command.extend([torrent_path[1] for torrent_path in torrent_paths])
    print("Adding torrents to deluge...")
    subprocess.run(deluge_add_command, stdout=subprocess.PIPE)

    # Start (/resume) all the torrents that were just added
    print("Starting torrents...")
    deluge_resume_command = ["deluge-console", "resume"]
    deluge_resume_command.extend([torrent_path[0].rstrip(".torrent") for torrent_path in torrent_paths])
    subprocess.run(deluge_resume_command)
