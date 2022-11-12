# Text to Speech to Track (TtStT)

This project converts MS Word document text, to speech then exports audio track files. Essentially it turns your documents into audio books, using computer generated voices. 

- [Text to Speech to Track (TtStT)](#text-to-speech-to-track-ttstt)
- [Running](#running)
  - [Docker Hub](#docker-hub)
  - [Docker Compose: Build & Run](#docker-compose-build--run)
  - [Docker: Build & Run](#docker-build--run)
  - [Python / Conda](#python--conda)

# Running

1. Place your MS Word `.DOCX` files in `data` directory. This does not work with legacy `.DOC` files.
2. Update `settings.json` for how many layers deep to split files out into separate tracks. This matches the heading depth in MS Word.
3. Run the script. 
4. Harvest your audio track files. 

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
3. Use the `environmen.yml` file to create your Conda environment or `requirments.txt` file to install the required pip dependencies. 
4. Run the python script as you normally would.