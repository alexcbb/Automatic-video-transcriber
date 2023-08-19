import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip
import os
import PySimpleGUI as sg
import matplotlib.font_manager as fm

from utils.audio import extract_transcripts
from utils.text import get_current_text, process_words, update_timestamps
from utils.draw import draw_text_on_image, draw_progress_bar, update_frame
from utils.video import update_video
from utils.ui import make_window, display_notification

import argparse
import yaml

import json
import argparse


def edit_video(font, 
               highlight_font, 
               line_1, 
               line_2, 
               word_timestamps,
               cap,
               final_path,
               audio_path):
    temp_path = "temp.mp4"

    ### Set back to first frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    ### Define the output video codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    totalFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
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

        current_time = current_frame_id / fps

        frame_text_1 = draw_text_on_image(
            line_1, draw, current_time, font, highlight_font,
            frame_width, word_timestamps, 50, pil_image)
        frame_text_2 =draw_text_on_image(
            line_2, draw, current_time, font, highlight_font,
            frame_width, word_timestamps, 150, frame_text_1, to_pil=False)
        
        out.write(frame_text_2)

        # Display the frame 
        imS = cv2.resize(frame_text_2, (450, 800))
        complete = current_frame_id / totalFrames

        ### Draw a progress bar
        draw_progress_bar(complete, imS)

        cv2.imshow('En cours d\'exportation...', imS)
        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('En cours d\'exportation...', 0) < 0:
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

def open_file_popup():
    file_types = [("MP4", "*.mp4"), ("All Files", "*.*")]
    file_path = sg.popup_get_file("Ouvrir fichier", file_types=file_types, keep_on_top=True)
    
    if file_path:
        return file_path
    return None

if __name__ == '__main__':
    ################################
    #       Parse arguments        #  
    ################################
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to the config file")
    parser.add_argument("--llama_model", type=str, default="../Llama/models/7B/ggml-model.bin")
    parser.add_argument("--video_path", type=str, default=None, help="Path to the input video")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    ### Get the filename
    video_path = sg.popup_get_file('Fichier à ouvrir')
    if video_path is None:
        exit()

    ### Prepare parameters
    temp_path = config["path"]["temp_path"]
    final_path = config["path"]["final_path"]
    transcript_path = config["path"]["transcript_path"]
    filename, ext = os.path.splitext(video_path)
    audio_path = f"{filename}.wav"
    counter_color_change = 0
    cur_frame = 0

    ### Handle audio transcription 
    line_1, line_2, word_timestamps = extract_transcripts(audio_path, video_path, transcript_path, use_api=False)

    ### Get the list of installed font on the computer and initialize fonts
    all_font_path = fm.findSystemFonts()
    font_path = all_font_path[0]
    fonts = []
    for path in all_font_path:
        fonts.append(path.split("\\")[-1].split(".")[0])
    fonts.sort()
    font = ImageFont.truetype(font_path, 40)
    highlight_font = ImageFont.truetype(font_path, 44)

    cap, fps, num_frames, frame_width, frame_height = update_video(video_path)
    ratio = frame_height / frame_width

    ### Get Layout and create the window
    window = make_window(fonts, num_frames)

    image_elem = window['-image-']
    slider_elem = window['-vid_slider-']
    error_elem = window['-error-']
    transcripts = window['-transcripts-']
    print(word_timestamps)

    event, values = window.read(timeout=0)
    timestep = 0
    for current_line_1, current_line_2 in zip(line_1, line_2):
        time_value = current_line_1[0]
        window.extend_layout(transcripts, 
                             [[sg.Text(f'De {time_value[0]}s à {time_value[1]}s'), 
                               sg.Input(default_text=current_line_1[1], key=f'-timestep-{timestep}-line1-', size=20, change_submits=True),
                               sg.Input(default_text=current_line_2[1], key=f'-timestep-{timestep}-line2-', size=20, change_submits=True)]])
        window.visibility_changed()
        transcripts.contents_changed()
        timestep += 1

    w_width, w_height = window.size
    update_frame(cap, cur_frame, fps, line_1, line_2, word_timestamps, font, highlight_font,
            frame_width, w_height, ratio, image_elem)
    is_opening_video = False
    while True:     
        ### Read the events
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Quitter'):
            break
        # TODO : only update frame when needed ? 
        
        ### Check values
        if int(values['-vid_slider-']) != cur_frame-1:
            cur_frame = int(values['-vid_slider-'])
            cap.set(cv2.CAP_PROP_POS_FRAMES, cur_frame)
            update_frame(cap, cur_frame, fps, line_1, line_2, word_timestamps, font, highlight_font,
                    frame_width, w_height, ratio, image_elem)
        slider_elem.update(cur_frame)
        if values['-list-']:
            for path in all_font_path:
                if values['-list-'][0] == path.split("\\")[-1].split(".")[0]:
                    font_path = path
                    cap.set(cv2.CAP_PROP_POS_FRAMES, cur_frame)
                    update_frame(cap, cur_frame, fps, line_1, line_2, word_timestamps, font, highlight_font,
                            frame_width, w_height, ratio, image_elem)
        if values['-font_size-']:
            font_size = int(values['-font_size-'])
            font = ImageFont.truetype(font_path, font_size)
            highlight_font = ImageFont.truetype(font_path, font_size+4)
            cap.set(cv2.CAP_PROP_POS_FRAMES, cur_frame)
            update_frame(cap, cur_frame, fps, line_1, line_2, word_timestamps, font, highlight_font,
                    frame_width, w_height, ratio, image_elem)
        else:
            font_size = 80
            font = ImageFont.truetype(font_path, font_size)
            highlight_font = ImageFont.truetype(font_path, font_size+4)
            cap.set(cv2.CAP_PROP_POS_FRAMES, cur_frame)   
            update_frame(cap, cur_frame, fps, line_1, line_2, word_timestamps, font, highlight_font,
                    frame_width, w_height, ratio, image_elem)
        ### Check events
        if event == '-export-' or event == 'Exporter':
            edit_video(font, highlight_font, line_1, line_2, 
                        word_timestamps, cap, final_path, audio_path)
            break
        elif event == 'Ouvrir':
            tmp_path = open_file_popup()
            if tmp_path:
                video_path = tmp_path
                filename, ext = os.path.splitext(video_path)
                audio_path = f"{filename}.wav"
                line_1, line_2, word_timestamps = extract_transcripts(audio_path, video_path)
                cap, fps, num_frames, frame_width, frame_height = update_video(video_path)
                update_frame(cap, cur_frame, fps, line_1, line_2, word_timestamps, font, highlight_font,
                        frame_width, w_height, ratio, image_elem)
                
                timestep = 0
                for current_line_1, current_line_2 in zip(line_1, line_2):
                    if f"-timestep-{timestep}-line1-" in window.key_dict.keys():
                        window[f"-timestep-{timestep}-line1-"].update(current_line_1[1])
                        window[f"-timestep-{timestep}-line2-"].update(current_line_2[1])
                    else:
                        time_value = current_line_1[0]
                        window.extend_layout(transcripts, 
                                            [[sg.Text(f'De {time_value[0]}s à {time_value[1]}s'), 
                                            sg.Input(default_text=current_line_1[1], key=f'-timestep-{timestep}-line1-', size=20, change_submits=True),
                                            sg.Input(default_text=current_line_2[1], key=f'-timestep-{timestep}-line2-', size=20, change_submits=True)]])
                    timestep += 1
                window.visibility_changed()
                transcripts.contents_changed()
        if "timestep" in event:
            split_event = event.split("-")
            line_id = int(split_event[3][-1])
            timestep_id = int(split_event[2])
            text = values[event]
            if line_id == 1:
                line_1[timestep_id] = (line_1[timestep_id][0], text, line_1[timestep_id][2])
            else:
                line_2[timestep_id] = (line_2[timestep_id][0], text, line_1[timestep_id][2])
            update_timestamps(line_1, line_2, word_timestamps)
            update_frame(cap, cur_frame, fps, line_1, line_2, word_timestamps, font, highlight_font,
                    frame_width, w_height, ratio, image_elem)
    window.close()

