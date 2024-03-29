"""Text to Speech to audio track.

This script will open each DOCX file to extract text. It will split files based on section headings at a depth specified in the settings.json file. 

TODO
    Make toc_depth == -1 lump all files into a single track.  
    mp3 tag: chapter sections (as subsections/subheaders), but probably requires processing each then combining.
    Update gtts stream function to have pauses between each api call. Add time to json. Also add progress bar.
    linux: speed seems to compound if set each time, also seems to do nothing if only set once. 
    linux: Setting voice ID each time lib is reloaded seems to change voice to a different one. Setting only on first load seems to not be used by the next. Almost like each time it is set and reloaded the whole list is reordered.
    linux: expand pyttsx3 with festival and pico2wave, add json select
    Check if there are limits in processing the number of char/words and split input + combine output as needed
"""

import os
import json
import time
import math
import importlib
import logging
import eyed3
import pyttsx3
import pydub
from typing import Dict
from gtts import gTTS
from docx import Document

#eyed3.log.setLevel(logging.DEBUG)

os_name = os.name
track_count = 1

def get_title(paragraphs):
    """_summary_

    :param paragraphs: Paragraphs from docx document
    :type paragraphs: Paragraphs
    :return: Title paragraph
    :rtype: paragraph
    """
    for paragraph in iter_paragraphs(paragraphs):
        if paragraph[1].startswith('Title'):
            return paragraph
    return None

def iter_headings(paragraphs):
    """Generator to get headings in document
    
    source: https://stackoverflow.com/questions/40388763/extracting-headings-text-from-word-doc

    :param paragraphs: Paragraphs from docx document
    :type paragraphs: Paragraphs
    :yield: Tuple of paragraph, style, toc depth, is header
    :rtype: Tuple
    """
    for paragraph in iter_paragraphs(paragraphs):
        if paragraph[3]:
            yield paragraph

def iter_paragraphs(paragraphs):
    """Generator to get paragraphs in document

    :param paragraphs: Paragraphs from docx document
    :type paragraphs: Paragraphs
    :yield: Tuple of paragraph, style, toc depth, is header
    :rtype: Tuple
    """
    for paragraph in paragraphs:
        style = paragraph.style.name
        if style.startswith('Heading'):
            depth = heading_to_depth(style)
            is_header = True
        else:
            depth = None
            is_header = False
        yield (paragraph, paragraph.style.name, depth, is_header)

def heading_to_depth(style: str) -> int:
    """Convert heading style name to a heading ToC depth

    :param style: Header style name
    :type style: str
    :return: Header number depth
    :rtype: int
    """
    style = style.replace('Heading ', '')
    return int(style)

def get_max_header(paragraphs, depth: int):
    """Find out the max number of headers at each depth. Return as the number of digits needed to represent that depth, for use in leading zeros in track numbers.

    :param paragraphs: Paragraphs from docx document
    :type paragraphs: Paragraphs
    :param depth: Number of sub-sections to dive into
    :type depth: int
    :return: List of digit lengths for each heading depth
    :rtype: List[int]
    """
    maxes = [0]*(depth+1)
    counts = [0]*(depth+1)
    current_depth = 0

    for header in iter_headings(paragraphs):
        new_depth = header[2]
        if new_depth <= depth:
            if new_depth > current_depth:  # child heading
                current_depth = new_depth
            elif new_depth < current_depth:  # parent heading
                maxes[current_depth] = max(counts[current_depth], maxes[current_depth])
                counts[current_depth] = 1
                current_depth = new_depth
            counts[current_depth] = counts[current_depth] + 1

    return [len(str(x)) for x in maxes]

def replace_invalid_char(filename: str) -> str:
    """Replaces invalid characters in windows filenames with a comma, and invalid characters for some of the underlying linux commands, such as espeak.

    :param filename: input filename
    :type filename: str
    :return: fixed output filename
    :rtype: str
    """
    invalid = '<>:"/\|?*'  # invalid in win file name, and linux command
    for char in invalid:
        filename = filename.replace(char, ',')

    if os_name != "nt":
        invalid = '()'  # invalid in linux command
        for char in invalid:
            filename = filename.replace(char, ',')

    return filename

def more_wait(file: str):
    """Deal with other things returning before complete
    
    Source: https://github.com/nateshmbhat/pyttsx3/issues/219

    :param file: Filename to watch for
    :type file: str
    """
    while not os.path.exists(file):
        time.sleep(0.1)
    time.sleep(0.1)
    return

def do_export(settings: Dict, text: str, name: str):
    """Process exports

    :param settings: settings from json
    :type settings: Dict
    :param text: text to convert
    :type text: str
    :param name: track name to export to
    :type name: str
    """
    if text != "":

        text_ = " ".join(text.split())  # Remove excess whitespace

        if not settings["online"]["process"]:
            filename = settings["data_loc"] + name + settings["offline"]["file_name_suffix"] + ".wav"
            print(filename[0:-4], flush=True)
            tts = TTS(settings)
            tts.start(text_, filename)
            del(tts)
        else:
            filename = settings["data_loc"] + name + settings["online"]["file_name_suffix"] + ".wav"
            print(filename[0:-4], flush=True)
            audio = gTTS(text=text_, lang="en", slow=False)
            audio.save(filename)
            time.sleep(math.ceil(settings["online"]["cool_down"] * 60)+.001)
        do_tag(settings, name, filename, text)
    return

def do_tag(settings: Dict, name: str, filename: str, text: str = None):
    """Convert wav to mp3 and add id3 tags.

    :param settings: settings from json
    :type settings: Dict
    :param name: track name to export to
    :type name: str
    :param filename: file name to export to
    :type filename: str
    :param text: text being converted, defaults to None
    :type text: str, optional
    """
    global track_count
    #importlib.reload(eyed3)

    if settings["extension"] == ".mp3":
        sound = pydub.AudioSegment.from_wav(filename)
        os.remove(filename)
        filename = filename[0:-3] + "mp3"
        sound.export(filename, format="mp3")
        file = eyed3.load(filename)

        if file:
            if not file.tag:
                file.initTag(eyed3.id3.ID3_V2_3)

            file.tag.title = name
            file.tag.artist = settings["tag"]["artist"]
            file.tag.album = settings["tag"]["album"]
            file.tag.album_artist = settings["tag"]["album_artist"]
            file.tag.recording_date = settings["tag"]["year"]
            file.tag.track_num = track_count
            file.tag.genre = "Audiobook"

            if settings["tag"]["cover_art"]:
                with open(settings["data_loc"] + settings["tag"]["cover_art"], "rb") as cover_art:
                    file.tag.images.set(3, cover_art.read(), settings["tag"]["cover_art_mime"])

            if settings["tag"]["text"] and text:
                file.tag.lyrics.set(text)

            file.tag.save()
            del(file)
            track_count = track_count + 1
        

class TTS:
    """Deal with some bugs in pyttsx3.
    
    Source: https://stackoverflow.com/questions/27338298/workaround-for-pyttsx-engine-runandwait-not-returning-on-yosemite
    """

    def __init__(self, settings):
        importlib.reload(pyttsx3)
        self.engine = pyttsx3.init()
        #voices = self.engine.getProperty('voices') 
        #self.engine.setProperty('voice', voices[settings["offline"]["voice_idx"]].id)
        #self.engine.setProperty('volume', settings["offline"]["volume"])
        #self.engine.setProperty('rate', settings["offline"]["rate"])

    def start(self, text, filename):
        filename_ = filename.replace(' ','\ ') if os_name != "nt" else filename
        self.engine.save_to_file(text, filename_)
        self.engine.runAndWait()
        more_wait(filename)
        return


def main():
    """Main script
    """

    with open("settings.json", "r") as f:
        settings = json.load(f)
    depth = max(0, settings["toc_depth"])
    data = settings["data_loc"]

    files = os.listdir(data)
    files = list(filter(lambda x: x.endswith(".docx") and not x.startswith("~$"), files))
    file_count = 0
    
    # if not settings["online"]["process"]:
    #     engine = pyttsx3.init()
    #     voices = engine.getProperty('voices') 
    #     print("Using Voice #" + str(settings["offline"]["voice_idx"] + 1) + " of " + str(len(voices)), flush=True)

    for file in files:
        file_count = file_count + 1
        counts = [0]*(depth+1)
        counts[0] = file_count
        current_depth = 0
        text = ""

        document = Document(data + file)
        paragraphs = document.paragraphs
        digits = get_max_header(paragraphs, depth)
        digits[0] = len(str(len(files)))
        title = get_title(paragraphs)
        title = title[0].text if title is not None else file[0:-5]
        junction = ".0. - " if settings["trailing_zero"] else ". - "
        name = replace_invalid_char(str(file_count).zfill(digits[0]) + junction + title)  # Create name

        for paragraph in iter_paragraphs(paragraphs):
            if paragraph[3]: # Is header
                current_depth = paragraph[2]  # Set current depth
            if paragraph[3] and current_depth <= depth:  # Is header & less than max (parent header)
                do_export(settings, text, name) # Export Last
                # Setup current level
                counts[current_depth+1:-1] = [0] * (len(counts) - (current_depth+1))  # Reset counts below
                counts[current_depth] = counts[current_depth] + 1  # Increment current depth count
                outline_depth = current_depth + 2 if settings["trailing_zero"] and current_depth < depth else current_depth + 1
                outline = [str(x).zfill(digits[i]) for i,x in enumerate(counts[0:outline_depth])]  # counts to text with leading zero
                name = replace_invalid_char(".".join(outline) + ". - " + paragraph[0].text)  # Create name
                text = ""  # Clear text

            text = text + "\n" + paragraph[0].text

        do_export(settings, text, name)

    if settings["playlist"] and settings["extension"] == ".mp3":
        files = os.listdir(data)
        files = list(filter(lambda x: x.endswith(settings["extension"]), files))
        with open(data + "Playlist.m3u", "w") as f:
            f.write("\n".join(files))
        

if __name__ == "__main__":
    main()
