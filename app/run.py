"""Text to Speech to audio track.

This script will open each DOCX file to extract text. It will split files based on section headings at a depth specified in the settings.json file. 

TODO
    Add a speed setting. Probably requires another lib to adjust playback speed of the mp3.
    Consider changing to `pyttsx3` for more options (ie. speed and voice).
"""

import os
import json
from gtts import gTTS
from docx import Document

def iter_headings(paragraphs):
    """Generator to get headings in document

    :param paragraphs: Paragraphs from docx document
    :type paragraphs: Paragraphs
    :yield: Tuple of paragraph, style, toc depth, is header
    :rtype: Tuple
    """
    for paragraph in paragraphs:
        style = paragraph.style.name
        if style.startswith('Heading'):
            depth = heading_to_depth(style)
            yield (paragraph, paragraph.style.name, depth, True)

def iter_paragraphs(paragraphs):
    """Generator to get paragraphs in document

    :param paragraphs: Paragraphs from docx document
    :type paragraphs: Paragraphs
    :yield: Tuple of paragraph, style, toc depth, is header
    :rtype: Tuple
    """
    depth = 0
    for paragraph in paragraphs:
        style = paragraph.style.name
        if style.startswith('Heading'):
            depth = heading_to_depth(style)
            is_header = True
        else:
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
        name = str(file_count).zfill(digits[0]) + ". - " + file[0:-5]  # Create name

        for paragraph in iter_paragraphs(paragraphs):
            if paragraph[3]: # Is header
                current_depth = paragraph[2]  # Set current depth
            if paragraph[3] and current_depth <= depth:  # Is header & less than max (parent header)
                # Export Last
                if text != "":
                    audio = gTTS(text=text, lang="en", slow=False)  # process exiting
                    audio.save(data + name + ".mp3")  # export exiting
                # Setup current level
                counts[current_depth+1:-1] = [0] * (len(counts) - (current_depth+1))  # Reset counts below
                counts[current_depth] = counts[current_depth] + 1  # Increment current depth count
                outline = [str(x).zfill(digits[i]) for i,x in enumerate(counts[0:current_depth+1])]  # counts to text with leading zero
                name = ".".join(outline) + ". - " + paragraph[0].text  # Create name
                text = ""  # Clear text

            text = text + "\n" + paragraph[0].text

        audio = gTTS(text=text, lang="en", slow=False)  # process final
        audio.save(data + name + ".mp3")  # export final


if __name__ == "__main__":
    main()
