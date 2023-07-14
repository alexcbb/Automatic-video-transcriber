import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip
import whisper
import os

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
    model.to("cuda")
    audio = whisper.load_audio(audio_path)

    # decode the audio
    transcribe_options = dict(task="transcribe", language=language, word_timestamps=True)

    result =  model.transcribe(audio, **transcribe_options)
    segment = result["segments"]
    print(f"Text : {result['text']}")

    timestamps = []
    for el in segment:
        for word in el["words"]:
            timestamps.append([(word['start'], word['end']), word['word']])
    return timestamps

def process_words(word_timestamps):
    stamp_texts = []
    current_txt = ''
    start = 0
    for timestamp, word in word_timestamps:
        if "lya" in word.lower() or "lia" in word.lower():
            word = "L'IA"
        if len(current_txt) > 0 and current_txt[-2:] == "' ":
            current_txt = current_txt[:-1]
            current_txt += word
        elif len(current_txt) + len(word) < 20:
            current_txt += word
        else: 
            stamp_texts.append(((start, timestamp[0]), current_txt))
            start = timestamp[0]
            current_txt = word
    return stamp_texts

def get_current_text(text_timestamps, frametime):
    for timestamp, text in text_timestamps:
        if frametime > timestamp[0] and frametime < timestamp[1]:
            return text
    return 'ERREUR TEXTE'

if __name__ == '__main__':
    # TODO : setup an argparse
    # Parameters 
    video_path = "short.mp4"
    temp_path = "temp.mp4"
    final_path = "final.mp4"
    transcript_path = None
    filename, ext = os.path.splitext(video_path)
    audio_path = f"{filename}.wav"
    #font_path = "C:\\Users\\alexc\\AppData\\Local\\Microsoft\\Windows\\Fonts\\built titling bd.ttf"
    font_path = "C:\\Users\\alexc\\AppData\\Local\\Microsoft\\Windows\\Fonts\\BurbankBigCondensed-Black.otf"
    font_size = 200
    text_color = (255, 255, 255)
    stroke_color = (0, 0, 0)
    stroke_width = 20

    ################################
    #  Handle audio transcription  #  
    ################################
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path)

    # TODO : load text
    if transcript_path == None:
        word_timestamps = extract_word_timestamps(audio_path)
        text_timestamps = process_words(word_timestamps)
        """print(f"Word timestamps : {word_timestamps}")
        print("\n \n \n \n")
        print(f"Text timestamps : {text_timestamps}")"""
    else:
        with open(transcript_path, "r") as f:
            text_timestamps = f.readlines()
    ################################
    #   Draw text back to video    #  
    ################################
    cap = cv2.VideoCapture(video_path)

    # Define the output video codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(temp_path, fourcc, fps, (frame_width, frame_height))

    current_frame_id = 0
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

        current_time = current_frame_id / fps
        text = get_current_text(text_timestamps, current_time)

        text_width, text_height = draw.textsize(text, font=font)
        text_origin = ((frame_width - text_width) // 2,  text_height + 100)

        draw.text(text_origin, text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color)
        #draw.text(text_origin, text, font=font, fill=text_color)

        # Convert the PIL Image back to OpenCV format
        frame_with_text = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        out.write(frame_with_text)

        # Display the frame (optional)
        imS = cv2.resize(frame_with_text, (450, 800))                # Resize image
        cv2.imshow('Overview...', imS)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        current_frame_id += 1

    # Release the video capture and writer objects
    cap.release()
    out.release()

    # Destroy any remaining windows
    cv2.destroyAllWindows()

    final_clip = VideoFileClip(temp_path)
    audio_clip = AudioFileClip(audio_path)
    final_clip = final_clip.set_audio(audio_clip)
    final_clip.write_videofile(final_path)

