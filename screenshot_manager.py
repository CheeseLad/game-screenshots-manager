import json
import os
import subprocess
import send2trash
import requests
import shutil
from dotenv import load_dotenv

load_dotenv()

STEAM_USER_ID = os.getenv("STEAM_USER_ID")

RECYCLE_THUMBNAILS = True
MAKE_GAME_FOLDERS = True
COPY_MINECRAFT_SCREENSHOTS = True
NETWORK_DRIVE_COPY = True
HIDE_SKIP_MESSAGES = True

STEAM_SCREENSHOTS_PATHS = [
    f"C:\\Program Files (x86)\\Steam\\userdata\\{STEAM_USER_ID}\\760\\remote",
    f"H:\\Program Files (x86)\\Steam\\userdata\\{STEAM_USER_ID}\\760\\remote",
]

MINECRAFT_INSTALLS_PATHS = [
    "E:\\Minecraft Installs",
    "D:\\Minecraft Installs",
]

NETWORK_DRIVE_PATH = "Z:\\Photos & Videos\\Game Screenshots"


def create_app_id_cache():
    if not os.path.exists("app_id_cache.json"):
        with open("app_id_cache.json", "w") as f:
            json.dump({}, f)


def recycle_thumbnails():
    print("Recycling thumbnail directories...")
    for dir in os.listdir("."):
        if os.path.isdir(dir):
            for subdir in os.listdir(dir):
                if os.path.isdir(os.path.join(dir, subdir)) and subdir.startswith(
                    "thumbnail"
                ):
                    print(f"Recycling {os.path.join(dir, subdir)}")
                    send2trash.send2trash(os.path.join(dir, subdir))


def make_game_folders():

    create_app_id_cache()

    with open("app_id_cache.json", "a+") as cache_file:
        cache_file.seek(0)
        app_id_cache = json.load(cache_file)

    for steam_screenshots_path in STEAM_SCREENSHOTS_PATHS:
        print(f"Processing screenshots in {steam_screenshots_path}...")
        for app_id_dir in os.listdir(steam_screenshots_path):
            app_id = int(app_id_dir)
            url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"

            if str(app_id) not in app_id_cache:
                try:
                    print(f"Fetching game name for App ID: {app_id}")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    app_data = data.get(str(app_id))
                    if app_data and app_data.get("success"):
                        game_name = app_data["data"]["name"]
                        app_id_cache[str(app_id)] = game_name
                        with open("app_id_cache.json", "w") as cache_file:
                            json.dump(app_id_cache, cache_file, indent=4)
                    else:
                        print(f"Failed to retrieve data for App ID: {app_id}")
                        continue

                except requests.RequestException as e:
                    print(f"Request failed: {e}")
            else:
                print(f"Using cached game name for App ID: {app_id}")
                game_name = app_id_cache[str(app_id)]

            parsed_game_name = (
                game_name.replace(":", " -")
                .replace("™", "")
                .replace("®", "")
                .replace("?", "")
                .replace("!", "")
                .strip()
            )
            print(f"Creating folder for {parsed_game_name} (App ID: {app_id})")
            os.makedirs(parsed_game_name, exist_ok=True)

            source_dir = os.path.join(steam_screenshots_path, app_id_dir, "screenshots")

            for file in os.listdir(source_dir):
                source_file = os.path.join(source_dir, file)
                dest_file = os.path.join(parsed_game_name, file)

                if os.path.isfile(source_file):
                    if not os.path.exists(dest_file):
                        print(f"Copying {file} to {parsed_game_name}")
                        shutil.copy2(source_file, dest_file)
                    else:
                        if not HIDE_SKIP_MESSAGES:
                            print(f"Skipping {file} (already exists)")


def copy_minecraft_screenshots_folder(screenshots_path, install_dir):
    dest_dir = os.path.join("Minecraft Installs", install_dir)
    if len(os.listdir(screenshots_path)) == 0:
        print(
            f"{len(os.listdir(screenshots_path))} files in {screenshots_path}, skipping..."
        )
        return
    os.makedirs(dest_dir, exist_ok=True)
    for file in os.listdir(screenshots_path):
        source_file = os.path.join(screenshots_path, file)
        dest_file = os.path.join(dest_dir, file)
        if os.path.isfile(source_file):
            if not os.path.exists(dest_file):
                print(f"Copying {file} to {dest_dir}")
                shutil.copy2(source_file, dest_file)
            else:
                if not HIDE_SKIP_MESSAGES:
                    print(f"Skipping {file} (already exists)")


def copy_minecraft_screenshots():
    os.makedirs("Minecraft Installs", exist_ok=True)
    for path in MINECRAFT_INSTALLS_PATHS:
        print(f"Processing Minecraft installs in {path}...")
        for install_dir in os.listdir(path):
            install_path = os.path.join(path, install_dir)
            if os.path.isdir(install_path):
                screenshots_path = os.path.join(
                    install_path, "minecraft", "screenshots"
                )
                if os.path.exists(screenshots_path):
                    print(f"Found screenshots for {install_dir}, copying...")
                    copy_minecraft_screenshots_folder(screenshots_path, install_dir)
                else:
                    print(
                        f"No screenshots found for {install_dir}, trying .minecraft folder..."
                    )
                    screenshots_path = os.path.join(
                        install_path, ".minecraft", "screenshots"
                    )
                    if os.path.exists(screenshots_path):
                        print(
                            f"Found screenshots in .minecraft for {install_dir}, copying..."
                        )
                        copy_minecraft_screenshots_folder(screenshots_path, install_dir)
                    else:
                        print(f"No screenshots found for {install_dir}, skipping...")
                        continue


def network_drive_copy():

    command = [
        "rclone",
        "sync",
        r"D:\Game Screenshots",
        r"Z:\Photos & Videos\Game Screenshots",
        "-v",
        "--checkers",
        "16",
        "--exclude",
        ".git/**",
    ]

    subprocess.run(command)


if __name__ == "__main__":
    if MAKE_GAME_FOLDERS:
        make_game_folders()
    if RECYCLE_THUMBNAILS:
        recycle_thumbnails()
    if COPY_MINECRAFT_SCREENSHOTS:
        copy_minecraft_screenshots()
    if NETWORK_DRIVE_COPY:
        network_drive_copy()
