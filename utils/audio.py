import whisper
from moviepy.editor import VideoFileClip, AudioFileClip
from .text import process_words
import pickle
import os
import requests
import json

# TODO : check API_token for user 
API_TOKEN = "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" 
headers = {"Authorization": f"Bearer {API_TOKEN}"}
API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large"

def query(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.request("POST", API_URL, headers=headers, data=data)
    return json.loads(response.content.decode("utf-8"))

def extract_word_timestamps(audio_path : str, whisper_size : str ="medium", language : str = "French", use_api=False):
    """Function that takes the path of an audio to extract the transcription

        Args:
            audio_path : path to the audio to transcribe
            whisper_size : size of the whisper model to load (tiny, small, medium, ...)
            language : language of the input audio

        Returns:
            timestamps : an array in format [[(start_time, end_time), "Word1"], [(start_time, end_time), "Word2"], ...]
    """
    if use_api:
        result = query(audio_path)
    else:
        # load model and audio
        model = whisper.load_model(whisper_size)
        #model.to("cuda")
        audio = whisper.load_audio(audio_path)

        model.eval()
        # decode the audio
        transcribe_options = dict(task="transcribe", language=language, word_timestamps=True)
        result =  model.transcribe(audio, **transcribe_options)

    segment = result["segments"]

    timestamps = []
    for el in segment:
        for word in el["words"]:
            timestamps.append([(word['start'], word['end']), word['word'].replace(" ", "")])
    return timestamps

def extract_transcripts(audio_path :str , video_path : str , transcript_path: str=None, use_api=False):
    # TODO : load the text properly
    # TODO : add a progress bar while loading text
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path)
    
    filename, ext = os.path.splitext(video_path)

    if transcript_path == None:
        transcript_path = f"{filename}.txt"
        if os.path.exists(transcript_path):
            with open(transcript_path, "rb") as f:
                temp_word_timestamp = pickle.load(f)
            line_1, line_2, word_timestamps = process_words(temp_word_timestamp)
        else:
            temp_word_timestamp = extract_word_timestamps(audio_path, use_api=use_api)
            line_1, line_2, word_timestamps  = process_words(temp_word_timestamp)
            with open(transcript_path, "wb") as f:
                pickle.dump(word_timestamps, f)        
    else:
        with open(transcript_path, "rb") as f:
            temp_word_timestamp = pickle.load(f)
        line_1, line_2, word_timestamps = process_words(temp_word_timestamp)
    
    return line_1, line_2, word_timestamps
    