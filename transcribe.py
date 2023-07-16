import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip
import whisper
import os
import pickle
import random
import PySimpleGUI as sg

def extract_word_timestamps(audio_path : str, whisper_size : str ="large", language : str = "French"):
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
            timestamps.append([(word['start'], word['end']), word['word'].replace(" ", "")])
    return timestamps

def process_words(word_timestamps):
    ### Put words with ' caracter together
    new_words = []
    i = 0
    nb_words = len(word_timestamps)
    while i < nb_words:
        timestamp, word = word_timestamps[i]
        timestamp = list(timestamp)
        if i > 0:
            if word_timestamps[i-1][1].replace(' ', '')[-1] == "'":
                word += word_timestamps[i-1][1]
                timestamp[0] = word_timestamps[i-1][0][0]
            elif i < nb_words-1 and word_timestamps[i+1][1].replace(' ', '')[0] == "'":
                word += word_timestamps[i+1][1]
                timestamp[1] = word_timestamps[i+1][0][1]
                i+=1
        new_words.append([tuple(timestamp), word])
        i+=1

    ### Extract words in 2 lines of few words  
    line_1 = []
    line_2 = []
    is_line_1 = True

    current_txt = ''
    start = 0
    j=0
    for timestamp, word in new_words:
        if j == 2:
            j=0
            if is_line_1:
                line_1.append(([start, timestamp[0]], current_txt[:-1]))
                is_line_1 = False
            else:
                line_2.append(([start, timestamp[0]], current_txt[:-1]))
                is_line_1 = True
            current_txt = ''
            start = timestamp[0]
        current_txt += word
        current_txt += " "
        j+=1

    ### Change the timesteps of the lines to be aligned
    for h in range(len(line_1)):
        if h < len(line_2):
            line_1[h][0][1] = line_2[h][0][1]
            line_2[h][0][0] = line_1[h][0][0]
    return line_1, line_2, new_words

def get_current_text(text_timestamps, frametime):
    for timestamp, text in text_timestamps:
        if frametime >= timestamp[0] and frametime < timestamp[1]:
            return text
    return ''

def get_current_word(word_timestamps, frametime):
    for timestamp, word in word_timestamps:
        if frametime >= timestamp[0] and frametime < timestamp[1]:
            return word
    return ''

# TODO : improve this function
def draw_text_on_image(
        text_timestamps, 
        draw, 
        current_time,
        font, 
        highlight_font,
        frame_width,
        word_timestamps,
        offset_top,
        pil_image,
        to_pil=True):
    
    text = get_current_text(text_timestamps, current_time)
    words = text.split()
    word_sizes = [draw.textsize(word, font=font) for word in words]
    text_width, text_height = draw.textsize(text, font=font)
    text_origin = ((frame_width - text_width) // 2,  text_height + offset_top)

    highlighted_word = get_current_word(word_timestamps, current_time)
    current_pos = text_origin[0]
    highlight_space = 0
    for word, size in zip(words, word_sizes):
        # Check if the word needs to be highlighted
        if highlighted_word.lower().replace(" ", "") == word.lower().replace(" ", ""):
            # Draw the highlighted word with a different color
            draw.text((current_pos-4, text_origin[1]-4), word, font=highlight_font, fill=highlight_color, stroke_width=stroke_width, stroke_fill=stroke_color)
            highlight_space = 10
        else:
            # Draw the regular word with the default color
            draw.text((current_pos+highlight_space, text_origin[1]), word, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color)

        # Update the starting position for the next word
        current_pos += (size[0] + 20) 

    if to_pil:
        return pil_image
    # Convert the PIL Image back to OpenCV format
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

def edit_video():
    # TODO : setup an argparse
    # Parameters 
    video_path = "short.mp4"
    temp_path = "temp.mp4"
    final_path = "final.mp4"
    transcript_path = "word_timestamps.txt"
    filename, ext = os.path.splitext(video_path)
    audio_path = f"{filename}.wav"
    #font_path = "C:\\Users\\alexc\\AppData\\Local\\Microsoft\\Windows\\Fonts\\built titling bd.ttf"
    font_path = "C:\\Users\\alexc\\AppData\\Local\\Microsoft\\Windows\\Fonts\\Montserrat-ExtraBold.otf"
    font_size = 70
    text_color = (255, 255, 255)
    highlight_color = (255, 255, 0)
    stroke_color = (0, 0, 0)
    stroke_width = 10
    counter_color_change = 0

    ################################
    #  Handle audio transcription  #  
    ################################
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path)

    # TODO : load text
    if transcript_path == None:
        temp_word_timestamp = extract_word_timestamps(audio_path)
        line_1, line_2, word_timestamps  = process_words(temp_word_timestamp)
        with open("new_word_timestamps.txt", "wb") as f:
            pickle.dump(word_timestamps, f)
    else:
        with open(transcript_path, "rb") as f:
            temp_word_timestamp = pickle.load(f)
        line_1, line_2, word_timestamps = process_words(temp_word_timestamp)
        
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
    font = ImageFont.truetype(font_path, font_size)
    highlight_font = ImageFont.truetype(font_path, font_size+4)

    old_text = get_current_text(line_1, 0) + ' ' + get_current_text(line_2, 0)

    # Process each frame of the video
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Convert the frame to PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(np.array(frame), cv2.COLOR_BGR2RGB))

        # Draw the text and prompt on the PIL Image
        draw = ImageDraw.Draw(pil_image)

        current_time = current_frame_id / fps

        frame_text_1 = draw_text_on_image(
            line_1, draw, current_time, font, highlight_font,
            frame_width, word_timestamps, 50, pil_image)
        frame_text_2 =draw_text_on_image(
            line_2, draw, current_time, font, highlight_font,
            frame_width, word_timestamps, 150, frame_text_1, to_pil=False)

        out.write(frame_text_2)

        # Display the frame (optional)
        imS = cv2.resize(frame_text_2, (450, 800))
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

if __name__ == '__main__':
    #edit_video()

    # TODO : use https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Font_String.py 
    # to handle fonts
    fonts = sg.Text.fonts_installed_list()

    sg.theme('Black')

    layout = [[sg.Text('My Text Element',
                    size=(20, 1),
                    click_submits=True,
                    relief=sg.RELIEF_GROOVE,
                    font='Courier` 25',
                    text_color='#FF0000',
                    background_color='white',
                    justification='center',
                    pad=(5, 3),
                    key='-text-',
                    tooltip='This is a text element',
                    )],
            [sg.Listbox(fonts, size=(30, 20), change_submits=True, key='-list-')],
            [sg.Input(key='-in-')],
            [sg.Button('Read', bind_return_key=True), sg.Exit()]]

    window = sg.Window('My new window', layout)

    while True:     # Event Loop
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        text_elem = window['-text-']
        print(event, values)
        if values['-in-'] != '':
            text_elem.update(font=values['-in-'])
        else:
            text_elem.update(font=(values['-list-'][0], 25))
    window.close()

