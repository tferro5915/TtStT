"""Text to Speech to audio track.

This script will open each DOCX file to extract text. It will split files based on section headings at a depth specified in the settings.json file. 

TODO
    Make toc_depth == -1 lump all files into a single track.  
    mp3 meta data & cover art could be neat
    Update gtts stream function to have pauses between each api call. Add time to json. Also add progress bar.
    remove excess whitespace to reduce char count
    remove "("")" from filenames for linux
    speed seems to compound if set each time, also seems to do nothing if only set once. 
    expand pyttsx3 with festival and pico2wave, add json select
    fix lingering string "data" to var
    if os.name == nt then do not escape spaces in filename
    collapse filter to just one
    make m3u playlist from audio files
"""

import os
import json
import time
import math
import importlib
from gtts import gTTS
from typing import Dict
#from slugify import slugify
#from tempfile import NamedTemporaryFile
import pyttsx3
from docx import Document

ext = ".mp3"

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
    """Replaces invalid characters in windows filenames to a comma.

    :param filename: input filename
    :type filename: str
    :return: fixed output filename
    :rtype: str
    """
    invalid = '<>:"/\|?*'
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
    return

def do_export(settings: Dict, text: str, filename: str):
    """Process exports

    :param settings: settings from json
    :type settings: Dict
    :param text: text to convert
    :type text: str
    :param filename: filename to export to
    :type filename: str
    """
    if text != "":
        
        if settings["offline"]["process"]:
            filename_ = filename.replace(ext, settings["offline"]["file_name_suffix"] + ext)
            print(filename_, flush=True)
            tts = TTS(settings)
            tts.start(text, filename_)
            del(tts)
            
        if settings["online"]["process"]:
            filename_ = filename.replace(ext, settings["online"]["file_name_suffix"] + ext)
            print(filename_, flush=True)
            audio = gTTS(text=text, lang="en", slow=False)
            audio.save(filename_)
            time.sleep(math.ceil(settings["online"]["cool_down"] * 60)+.001)
    return

class TTS:
    """Deal with some bugs in pyttsx3.
    
    Source: https://stackoverflow.com/questions/27338298/workaround-for-pyttsx-engine-runandwait-not-returning-on-yosemite
    """

    def __init__(self, settings):
        importlib.reload(pyttsx3)
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices') 
        self.engine.setProperty('voice', voices[settings["offline"]["voice_idx"]].id)
        self.engine.setProperty('volume', settings["offline"]["volume"])
        self.engine.setProperty('rate', settings["offline"]["rate"])

    def start(self, text, filename):
        self.engine.save_to_file(text, filename.replace(' ','\ '))
        self.engine.runAndWait()
        more_wait(filename)
        return


def main():
    """Main script
    """

    files = os.listdir("/data")
    files = list(filter(lambda x: x.endswith(".docx"), files))
    files = list(filter(lambda x: not x.startswith("~$"), files))
    file_count = 0

    with open("settings.json", "r") as f:
        settings = json.load(f)
    depth = max(0, settings["toc_depth"])
    data = settings["data_loc"]
    
    if settings["offline"]["process"]:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices') 
        engine.setProperty('voice', voices[settings["offline"]["voice_idx"]].id)
        engine.setProperty('volume', settings["offline"]["volume"])
        engine.setProperty('rate', settings["offline"]["rate"])
        print("Using Voice #" + str(settings["offline"]["voice_idx"]) + " of " + str(len(voices)), flush=True)

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
        name = replace_invalid_char(str(file_count).zfill(digits[0]) + ". - " + title)  # Create name

        for paragraph in iter_paragraphs(paragraphs):
            if paragraph[3]: # Is header
                current_depth = paragraph[2]  # Set current depth
            if paragraph[3] and current_depth <= depth:  # Is header & less than max (parent header)
                do_export(settings, text, data + name + ext) # Export Last
                # Setup current level
                counts[current_depth+1:-1] = [0] * (len(counts) - (current_depth+1))  # Reset counts below
                counts[current_depth] = counts[current_depth] + 1  # Increment current depth count
                outline = [str(x).zfill(digits[i]) for i,x in enumerate(counts[0:current_depth+1])]  # counts to text with leading zero
                name = replace_invalid_char(".".join(outline) + ". - " + paragraph[0].text)  # Create name
                text = ""  # Clear text

            text = text + "\n" + paragraph[0].text

        do_export(settings, text, data + name + ext)


if __name__ == "__main__":
    main()
