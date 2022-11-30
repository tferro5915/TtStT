# Text to Speech to Track (TtStT)

This project converts MS Word document text, to speech then exports audio track files. Essentially it turns your documents into audio books, using computer generated voices. It will loop through multiple documents too. 

- [Text to Speech to Track (TtStT)](#text-to-speech-to-track-ttstt)
- [Running](#running)
  - [Settings](#settings)
  - [Docker Hub](#docker-hub)
  - [Docker Compose: Build \& Run](#docker-compose-build--run)
  - [Docker: Build \& Run](#docker-build--run)
  - [Conda \& Python](#conda--python)

# Running

1. Place your MS Word `.DOCX` files in `data` directory. This is not intended to work with legacy `.DOC` files. 
2. Update `settings.json`. 
3. Run the script with options below, with multiple Docker or non-Docker options. 
4. Harvest your audio track files. Track titles start with document and header numbers separated by periods for easy sorting, and followed by the document name or header text. 

## Settings

Descriptions of parameters in `settings.json`.

- toc_depth: How many layers deep to split files out into separate tracks. This matches the heading depth in MS Word.
  1. `-1` will lump all documents into one track... someday (not implemented yet).
  2. `0` will split tracks per document. 
  3. `1` will split tracks per documents & the first heading level.
  4. `2` will split tracks per document and each heading level down to the second.
  5. etc. ...
- trailing_zero: Add zero to the end of toc outline numbers. Turns out some systems sort space after numbers, not the normal space before numbers, this fixes it by adding a zero to the end.
- data_loc: Location of your documents.
- playlist: weather or not to make a playlist from the tracks.
- extension: Export audio file extensions, (`".mp3"`, `".wav"`).
- tag: Contains settings for MP3 ID3 tags.
  - artist: Artist name.
  - album_artist: Album artist.
  - year: Year created (int).
  - album: Album name.
  - cover_art: Filename for image.
  - cover_art_mime: Image MIME type (`"image/jpeg"`, `"image/png"`).
  - text: Whether or not to include the processed text in lyrics (`true`, `false`).
- online: Settings for processing TTS online. 
  - process: Whether or not to process online (`true`, `false`).
  - cool_down: API cool down minutes between sections to prevent getting [blocked](https://stackoverflow.com/questions/65980562/gtts-tts-gttserror-429-too-many-requests-from-tts-api-probable-cause-unknow).
  - pause: API pause seconds between api tokens call to prevent getting [blocked](https://stackoverflow.com/questions/65980562/gtts-tts-gttserror-429-too-many-requests-from-tts-api-probable-cause-unknow).
  - file_name_suffix: Apply file suffix to online processed files.
- offline: Settings for processing TTS offline. 
  - volume: Volume.
  - rate: Voice speed.
  - voice_idx: System voice index.
  - file_name_suffix: Apply file suffix to offline processed files.

*Notes*: 
- Setting `data_loc` should only be changed if you are not using the Docker options or you change the location of data in the Docker container. 
- Each OS treats `offline` settings differently so the settings will not match across OS's.

## Docker Hub

*TODO*: Upload to docker hub for quick use once build image is working

## Docker Compose: Build & Run

1. Open terminal in the root directory of the project. 
2. Run `docker-compose -p ttstt up --build`.

## Docker: Build & Run

1. Open terminal in app directory of the project. 
2. Run `docker build -t local/ttstt_app:latest .`.
3. Move to the root directory of the project.
4. Run `docker run -v ./app:/app -v ./data:/data -it --rm local/ttstt_app`

## Conda & Python

1. Change `data_loc` as needed to point to where your data is located, probably `../data/`. 
2. navigate to `app` folder or co-locate `settings.json` and `run.py`.
3. Install dependencies & setup environment. Use the `environmen.yml` and `requirments.txt` files to create your Conda environment `conda env create -f environment.yml`.
4. Activate Conda environment and run the python script as you normally would.
