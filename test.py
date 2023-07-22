#!/bin/python

import readline
import os
import subprocess
import random
import string
import time
import concurrent.futures


def getSelection():
    # fonts pulled from v3.02
    valid_fonts = [
        "3270", "Agave", "AnonymousPro", "Arimo", "AurulentSansMono", "BigBlueTerminal", "BitstreamVeraSansMono", 
        "CascadiaCode", "CodeNewRoman", "ComicShannsMono", "Cousine", "DaddyTimeMono", "DejaVuSansMono", "DroidSansMono", 
        "EnvyCodeR", "FantasqueSansMono", "FiraCode", "FiraMono", "Go-Mono", "Gohu", "Hack", "Hasklig", "HeavyData", 
        "Hermit", "iA-Writer", "IBMPlexMono", "Inconsolata", "InconsolataGo", "InconsolataLGC", "Iosevka", "IosevkaTerm", 
        "JetBrainsMono", "Lekton", "LiberationMono", "Lilex", "Meslo", "Monofur", "Monoid", "Mononoki", "MPlus", 
        "NerdFontsSymbolsOnly", "Noto", "OpenDyslexic", "Overpass", "ProFont", "ProggyClean", "RobotoMono", 
        "ShareTechMono", "SourceCodePro", "SpaceMono", "Terminus", "Tinos", "Ubuntu", "UbuntuMono", "VictorMono"
        ]

    def completer(text, state):
        options = [item for item in valid_fonts if item.startswith(text)]
        return options[state] if state < len(options) else None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

    # Make sure the selected fronts are valid

    while True:
        selected_fonts = input("Select your fonts: ").split()
        if not selected_fonts: continue

        valid_selected_fonts = [
            font for font in selected_fonts
                if font in valid_fonts
        ]

        invalid_selected_fonts = ' '.join([font for font in selected_fonts if font not in valid_fonts])

        # Don't fail on an invalid font
        if invalid_selected_fonts:
            print(f"Unknown fonts: {invalid_selected_fonts}")

        if valid_selected_fonts:
            return valid_selected_fonts
    

def downloadAndExtract(font_name, global_fonts_flag):

    # Check if fonts already exist
    path = '' 
    if global_fonts_flag:
        path = '/usr/share/fonts'
    else:
        path = '~/.local/share/fonts'
        
    if (os.path.exists(f"{path}/{font_name}")):
        if (input(f"{font_name} already exists. Would you like to override it? (y/N)")):
            if (global_fonts_flag):
                subprocess.run(["sudo", "mkdir", f"{path}/.bkp/", "2>", "/dev/null"])
                subprocess.run(["sudo", "mv", f"{path}/{font_name}", f"{path}/.bkp/{font_name}"])
            else:
                os.makedirs(f"{path}/.bkp/", exist_ok=True)
                subprocess.run(["mv", f"{path}/{font_name}", f"{path}/.bkp/{font_name}"])
        else:
            return

    max_retries = 3
    current_retry = 0

    while current_retry < max_retries:
        temp_file_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        temp_file_path = f"/tmp/{temp_file_name}"
        url = f"https://github.com/ryanoasis/nerd-fonts/releases/download/v3.0.2/{font_name}.tar.xz"

        os.makedirs(temp_file_path, exist_ok=True)

        try:
            wget_process = subprocess.Popen(
                ["wget", "-qO-", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            tar_process = subprocess.Popen(
                ["tar", "-xJ", "-C", temp_file_path],
                stdin=wget_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            wget_process.stdout.close()
            out, err = tar_process.communicate(timeout=10)

            if tar_process.returncode == 0:
                print(f"Font {font_name} download & extraction successful")
                if global_fonts_flag:
                    subprocess.run(["sudo", "mv", temp_file_path, f"/usr/share/fonts/{font_name}"])
                else:
                    subprocess.run(["mv", temp_file_path, os.path.expanduser(f"~/.local/share/fonts/{font_name}")])
                break
            else:
                print("Download and extraction failed. Retrying...")
                print("Error message:", err)
                current_retry += 1
                time.sleep(1)
        except subprocess.TimeoutExpired:
            print("Timeout while downloading or extracting. Retrying...")
            current_retry += 1
            time.sleep(1)

    if current_retry == max_retries:
        print("Maximum number of retries reached. Download and extraction failed.")
    

def init_local_fonts():
    # Make sure that local fonts folder exists, if not make it
    fonts_dir = os.path.expanduser("~/.local/share/fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    
    # Create config file for fc-cache. May not be necessary due to auto-detect.

    font_config_dir = os.path.expanduser("~/.config/fontconfig/conf.d")
    os.makedirs(font_config_dir, exist_ok=True)

    config = """<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>~/.local/share/fonts</dir>
</fontconfig>
""".format(font_dir=os.path.expanduser("~/.local/share/fonts"))

    font_config_file = os.path.join(font_config_dir, "61-user-fonts.conf")

    with open(font_config_file, "w") as f:
        f.write(config)




max_thread = 5

global_fonts_flag_input = input("Do you want to save the fonts globally (across entire system) (y/N)? : ")
global_fonts_flag = global_fonts_flag_input and global_fonts_flag_input[0] == 'y'

if not global_fonts_flag_input:
    init_local_fonts()
else:
    # Authorize the program for extraction
    subprocess.run(['sudo', 'true'])

with concurrent.futures.ThreadPoolExecutor(max_thread) as executor:

    futures = {executor.submit(downloadAndExtract, font, global_fonts_flag) for font in getSelection()}
    
    concurrent.futures.wait(futures)

subprocess.Popen(
    ["fc-cache"],
)

print ("Download, extraction, and install successful!")