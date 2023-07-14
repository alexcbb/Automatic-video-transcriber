from moviepy.editor import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
import moviepy.editor as mp
import whisper
import os


def extract_word_timestamps(audio_path):
    # load model
    model = whisper.load_model("medium")
    model.to("cuda")

    # load audio 
    audio = whisper.load_audio(audio_path)

    # decode the audio
    transcribe_options = dict(task="transcribe", language="French", word_timestamps=True)

    result =  model.transcribe(audio, **transcribe_options)
    segment = result["segments"]
    print(f"Text : {result['text']}")

    timestamps = []
    for el in segment:
        for word in el["words"]:
            timestamps.append([(word['start'], word['end']), word['word']])
    return timestamps

def extract_text_timestamps(audio_path):
    # load model
    model = whisper.load_model("small")
    model.to("cuda")

    # load audio 
    audio = whisper.load_audio(audio_path)

    # decode the audio
    transcribe_options = dict(task="transcribe", language="French", word_timestamps=True)

    result =  model.transcribe(audio, **transcribe_options)
    segment = result["segments"]
    print(f"Text : {result['text']}")

    timestamps = []
    for el in segment:
        timestamps.append([(el['start'], el['end']), el['text']])
    return timestamps

def process_words(word_timestamps):
    stamp_texts = []
    current_txt = ''
    start = 0
    for timestamp, word in word_timestamps:
        if len(current_txt) > 0 and current_txt[-2:] == "' ":
            current_txt = current_txt[:-1]
            current_txt += word
        elif len(current_txt) + len(word) < 20:
            current_txt += word
        else: 
            stamp_texts.append(((start, timestamp[1]), current_txt))
            start = timestamp[1]
            current_txt = word
        current_txt += " "
    return stamp_texts

def add_shadow(txt_clip, shadow_color='black', shadow_opacity=0.7, shadow_offset=(5, 5)):
    shadow = txt_clip.set_position((txt_clip.w + shadow_offset[0], txt_clip.h + shadow_offset[1]))
    shadow = shadow.set_duration(txt_clip.duration)
    shadow = shadow.set_opacity(shadow_opacity)
    shadow.color = shadow_color
    return mp.CompositeVideoClip([shadow, txt_clip])

def add_text_to_video(video_path, text_timestamps):
    video = VideoFileClip(video_path)
    video_duration = video.duration
    print(f'Durée vidéo {video_duration}')

    # Create an empty list to store text clips
    text_clips = []
    current_timestamp = 0
    for timestamp, text in text_timestamps:
        timestamp_seconds = timestamp[1] - timestamp[0]
        
        current_timestamp += timestamp_seconds
        if current_timestamp <= video_duration:
            text_clip = TextClip(text, fontsize=40, font='Arial', 
                                 stroke_color="Black", stroke_width=1.5, 
                                 color='white', align='center',
                                 method='caption')
            text_clip = text_clip.set_duration(timestamp_seconds)
            text_clips.append(text_clip)
    final_video = concatenate_videoclips([video] + text_clips)

    final_video.write_videofile('output.mp4', codec='libx264')

def add_text_with_zoom(clip, timestamp, text):
    # Define the start and end time of the clip where the text will be shown
    start_time = timestamp[0]
    end_time = timestamp[1]

    # Set the duration of the zoom animation (in seconds)
    duration = end_time - start_time
    def resize_func(t):
        if t < duration/2:
            return 1 + 0.4*t
    # Create a subclip from the original clip for the specified duration
    #subclip = clip.subclip(start_time, end_time)

    # Add the text to the subclip
    txt = mp.TextClip(text, fontsize=150, 
                      color='White', 
                      stroke_color="Black", 
                      font="C:\\Users\\alexc\\AppData\\Local\\Microsoft\\Windows\\Fonts\\built titling sb.ttf",
                      stroke_width=2).set_position(('center', 'center')).set_start(start_time).set_duration(duration)
    txt_with_shadow = add_shadow(txt)

    return txt_with_shadow

def write_timestamps_to_file(text_timestamp):
    # TODO : create 
    pass

# TODO : create a GUI
if __name__ == '__main__':
    video_path = "short.mp4"
    transcript_path = None
    filename, ext = os.path.splitext(video_path)
    audio_path = f"{filename}.wav"

    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path)

    # TODO : load text
    if transcript_path == None:
        #word_timestamps = extract_word_timestamps(audio_path)
        text_timestamps = extract_text_timestamps(audio_path)
        #text_timestamps = process_words(word_timestamps)
    else:
        with open(transcript_path, "r") as f:
            text_timestamps = f.readlines()

    clips = []
    for timestamp, text in text_timestamps:
        clips.append(add_text_with_zoom(clip, timestamp, text))
    
    clip = mp.CompositeVideoClip([clip] + clips)
    clip.write_videofile("ouput.mp4", codec='libx264', audio_codec="aac")

    #add_text_to_video(video_path, word_timestamps)
