# Text to Speech to Track (TtStT)

This project converts MS Word document text, to speech then exports audio track files. Essentially it turns your documents into audio books, using computer generated voices. It will loop through multiple documents too. 

- [Text to Speech to Track (TtStT)](#text-to-speech-to-track-ttstt)
- [Running](#running)
  - [Docker Hub](#docker-hub)
  - [Docker Compose: Build & Run](#docker-compose-build--run)
  - [Docker: Build & Run](#docker-build--run)
  - [Python / Conda](#python--conda)

# Running

1. Place your MS Word `.DOCX` files in `data` directory. This is not intended to work with legacy `.DOC` files. 
2. Update `settings.json` for how many layers deep to split files out into separate tracks, and weather or not to make a playlist from the tracks. This matches the heading depth in MS Word. 
     1. `-1` will lump all documents into one track... someday (not implemented yet).
     2. `0` will split tracks per document. 
     3. `1` will split tracks per documents & the first heading level.
     4. `2` will split tracks per document and each heading level down to the second.
     5. etc. ...
3. Update `settings.json` for offline voice, volume, and speech rate, etc. as needed. Also set if files should be processed offline. Note each OS treats these differently so the settings will not match across OS's. 
4. Update `settings.json` for online API cool down minutes between sections, and pause seconds between api tokens call to prevent getting [blocked](https://stackoverflow.com/questions/65980562/gtts-tts-gttserror-429-too-many-requests-from-tts-api-probable-cause-unknow). Also set if files should be processed online. 
5. Run the script with options below. 
6. Harvest your audio track files. Track titles start with document and header numbers separated by periods for easy sorting, and followed by the document name or header text. 

*Note*: Setting `data_loc` should only be changed if you are not using the Docker options or you change the location of data in the Docker container. 

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

## Python / Conda

1. Change `data_loc` as needed to point to where your data is located. 
2. Co-locate `settings.json` and `run.py`.
3. Install dependencies & setup environment.
   1. Conda: Use the `environmen.yml` file to create your Conda environment `conda env create -f environment.yml` or
   2. PiP: add the dependencies from `environmen.yml` to `requirments.txt` then use pip with `requirments.txt` file to install the required pip dependencies `pip install -r requirements.txt`. 
4. Run the python script as you normally would.