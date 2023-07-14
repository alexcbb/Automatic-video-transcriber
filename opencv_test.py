import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pydub import AudioSegment
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

    #################################################################
    #################################################################
    #################################################################
    #################################################################

    # Load the video
    video_path = 'short.mp4'
    cap = cv2.VideoCapture(video_path)
    audio = AudioSegment.from_file(video_path)


    # Define the output video codec and create a VideoWriter object
    output_path = 'output_video.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    # Define text properties
    text = 'CECI EST UN TEXTE'
    font_path = "C:\\Users\\alexc\\AppData\\Local\\Microsoft\\Windows\\Fonts\\built titling sb.ttf"  # Replace with the actual path to your font file
    font_size = 50
    text_color = (255, 255, 255)  # White color
    stroke_color = (0, 0, 0)  # Red color
    stroke_width = 5

    # Process each frame of the video
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Convert the frame to PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(np.array(frame), cv2.COLOR_BGR2RGB))

        # Draw the text and prompt on the PIL Image
        draw = ImageDraw.Draw(pil_image)
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = draw.textsize(text, font=font)

        text_origin = (text_width + 10, text_height+10)


        draw.text(text_origin, text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color)
        #draw.text(text_origin, text, font=font, fill=text_color)

        # Convert the PIL Image back to OpenCV format
        frame_with_text = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        out.write(frame_with_text)

        # Display the frame (optional)
        cv2.imshow('Rendering', frame_with_text)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture and writer objects
    cap.release()
    out.release()

    # Destroy any remaining windows
    cv2.destroyAllWindows()