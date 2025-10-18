from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw
import json
import tempfile
import urllib.parse as urlparse
import pytesseract
import argparse
import sys
import os
import traceback
from textwrap import shorten


def main(start_url, follow_length):
    video_id = get_youtube_id(start_url)

    output_path = Path(f"./output/{datetime.now():%Y-%m-%d-%H%M%S}-{video_id}")
    output_path.mkdir(parents=True)
    (output_path / "descriptions").mkdir()
    (output_path / "screenshots").mkdir()
    (output_path / "annotated_screenshots").mkdir()

    try:
        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch(
                headless=False,
                slow_mo=50,
                args=["--disable-web-security"],
            )
            context = browser.new_context(bypass_csp=True)
            page = context.new_page()
            page.set_viewport_size({"width": 1280, "height": 960})
            page.goto(start_url)

            try:
                for i in range(0, follow_length + 1):
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(1000)
                    screenshot_path = output_path / "screenshots" / "screenshot-{i:05d}.png"
                    page.screenshot(path=screenshot_path)
                    check_sponsors(screenshot_path)
                    get_metadata(page, i, output_path)
                    page.keyboard.press("Shift+N")

            except Exception as e:
                print(e)
                print(traceback.format_exc())

            browser.close()
    except Exception as e:
        print("It broke")
        print(e)


def get_metadata(page, i, output_path):
    with open(output_path / "data.csv", "a") as csv:
        vid_id = get_youtube_id(page.url)
        if i == 0:
            csv.write("number,id,title,channel,views,likes,genre,thumbnail_url\n")

        try:
            raw_data = page.locator("css=.playerMicroformatRendererHost > script")
            data = json.loads(raw_data.inner_text())

            views = [
                a["userInteractionCount"]
                for a in data["interactionStatistic"]
                if "WatchAction" in a["interactionType"]
            ][0]
            likes = [
                a["userInteractionCount"]
                for a in data["interactionStatistic"]
                if "LikeAction" in a["interactionType"]
            ][0]
            title = data["name"]
            channel = data["author"]
            genre = data["genre"]
            thumbnailUrl = data["thumbnailUrl"][0]
            description = data["description"]

            print(f"{i:04d}: {shorten(title, width=50, placeholder='...'):<50} - {shorten(channel, width=40, placeholder='...'):<40} / {genre} / {views}|{likes}")
            csv.write(f'{i},{vid_id},"{title}","{channel}",{views},{likes},{genre},{thumbnailUrl}\n')

            with open(output_path / "descriptions" / f"{i:05d}-{vid_id}.txt", "x") as desc_file:
                desc_file.write(description)

        except Exception as e:
            print(f"{i:04d}: ERROR - {str(e)[0:100]}")
            csv.write(f"{i},{vid_id},Unable to get data\n")


def get_youtube_id(video_url):
    url_data = urlparse.urlparse(video_url)
    query = urlparse.parse_qs(url_data.query)
    video = query["v"][0]
    return video


def check_sponsors(path):
    im = Image.open(path)
    if "sponsored" in pytesseract.image_to_string(im).lower():
        d = pytesseract.image_to_data(im, output_type="dict")
        draw = ImageDraw.Draw(im)
        for i in range(len(d["text"])):
            if d["conf"][i] > 50 and "sponsored" in d["text"][i].lower():
                (x, y, w, h) = (d["left"][i], d["top"][i], d["width"][i], d["height"][i])
                draw.rectangle(((x - 2, y - 2), (x + w + 2, y + h + 2)), outline="green")
        im.save(path.parent.parent / "annotated_screenshots" / path.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Follow the trail of youtube recommendations')
    parser.add_argument('start_url', help='The youtube url to start on')
    parser.add_argument('--max-follow','-f', help='The maximum number of URLs to follow (default 1000)', default=1000, type=int)
    args = vars(parser.parse_args())
    main(args['start_url'], args['max_follow'])
