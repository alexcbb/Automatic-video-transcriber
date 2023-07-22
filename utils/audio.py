import whisper
from moviepy.editor import VideoFileClip, AudioFileClip
from .text import process_words
import pickle

def extract_word_timestamps(audio_path : str, whisper_size : str ="medium", language : str = "French"):
    """Function that takes the path of an audio to extract the transcription

        Args:
            audio_path : path to the audio to transcribe
            whisper_size : size of the whisper model to load (tiny, small, medium, ...)
            language : language of the input audio

        Returns:
            timestamps : an array in format [[(start_time, end_time), "Word1"], [(start_time, end_time), "Word2"], ...]
    """
    # load model and audio
    model = whisper.load_model(whisper_size)
    #model.to("cuda")
    audio = whisper.load_audio(audio_path)

    # decode the audio
    transcribe_options = dict(task="transcribe", language=language, word_timestamps=True)

    result =  model.transcribe(audio, **transcribe_options)
    segment = result["segments"]
    print(f"Text : {result['text']}")

    timestamps = []
    for el in segment:
        for word in el["words"]:
            timestamps.append([(word['start'], word['end']), word['word'].replace(" ", "")])
    return timestamps

def extract_transcripts(audio_path :str , video_path : str , transcript_path: str):
    # TODO : load the text properly
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path)

    if transcript_path == None:
        temp_word_timestamp = extract_word_timestamps(audio_path)
        line_1, line_2, word_timestamps  = process_words(temp_word_timestamp)
        with open("new_word_timestamps.txt", "wb") as f:
            pickle.dump(word_timestamps, f)
    else:
        with open(transcript_path, "rb") as f:
            temp_word_timestamp = pickle.load(f)
        line_1, line_2, word_timestamps = process_words(temp_word_timestamp)
    
    return line_1, line_2, word_timestamps
    