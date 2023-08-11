import customtkinter as ctk
import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import argparse
import yaml
import os
import PySimpleGUI as sg
import matplotlib.font_manager as fm
from PIL import Image, ImageDraw, ImageFont
from tkinter import ttk
from utils.audio import extract_transcripts
import numpy as np
import math

ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

def get_current_text(text_timestamps, frametime):
    """
    Returns the current sentence said associated with the given frame
    """
    for timestamp, text, ids in text_timestamps:
        if frametime >= timestamp[0] and frametime < timestamp[1]:
            return text, ids
    return '', -1

def get_current_word(word_timestamps, frametime):
    """
    Returns the current word said associated with the given frame
    """
    for timestamp, word, id in word_timestamps:
        if frametime >= timestamp[0] and frametime < timestamp[1]:
            return word, id
    return '', -1

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
    
    text, ids = get_current_text(text_timestamps, current_time)
    print(f"Current text : {text}")
    words = text.split()
    word_sizes = [draw.textsize(word, font=font) for word in words]
    text_width, text_height = draw.textsize(text, font=font)
    text_origin = ((frame_width - text_width) // 2,  text_height + offset_top)
    highlight_color = (255, 255, 0)
    stroke_color = (0, 0, 0)
    stroke_width = 10
    text_color = (255, 255, 255)

    highlighted_word, word_id = get_current_word(word_timestamps, current_time)
    print(f"Highlighted word : {highlighted_word}")
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

def draw_progress_bar(completion, img):
    line_thickness = 10
    y = math.ceil(img.shape[1] - img.shape[1]/25)
    x = 0
    w = img.shape[0] // 3
    cv2.putText(img, f"Progression {int(completion*100)}%", org=(20, y + 30), fontFace=cv2.FONT_HERSHEY_SIMPLEX, 
                fontScale=0.7, color=(255, 255, 255), thickness = 10, lineType=cv2.LINE_AA)
    cv2.putText(img, f"Progression {int(completion*100)}%", org=(20, y + 30), fontFace=cv2.FONT_HERSHEY_SIMPLEX, 
                fontScale=0.7, color=(0, 0, 255), thickness = 2, lineType=cv2.LINE_AA)
    cv2.line(img, (x, y), (w, y), (255,255,255), line_thickness)
    cv2.line(img, (x, y), (math.ceil(w*completion), y), (0,0,255), line_thickness)

def update_frame(cap, cur_frame, fps, line_1, line_2, word_timestamps, font, highlight_font,
        frame_width, w_height, ratio, image_elem):
    ret, frame = cap.read()
            
    # Convert the frame to PIL Image
    pil_image = Image.fromarray(cv2.cvtColor(np.array(frame), cv2.COLOR_BGR2RGB))

    # Draw the text and prompt on the PIL Image
    draw = ImageDraw.Draw(pil_image)

    current_time = cur_frame / fps
    frame_text_1 = draw_text_on_image(
        line_1, draw, current_time, font, highlight_font,
        frame_width, word_timestamps, 50, pil_image)
    frame_text_2 = draw_text_on_image(
        line_2, draw, current_time, font, highlight_font,
        frame_width, word_timestamps, 150, frame_text_1, to_pil=False)

    # Display the frame
    imS = cv2.resize(frame_text_2, (int((w_height-200)//ratio), w_height-200))
    imgbytes = cv2.imencode('.png', imS)[1].tobytes()  
    image_elem.update(data=imgbytes)

# TODO : adapt this to get right font
class ScrollableLabelButtonFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.command = command
        self.radiobutton_variable = ctk.StringVar()
        self.label_list = []
        self.button_list = []

    def add_item(self, item, image=None):
        label = ctk.CTkLabel(self, text=item, image=image, compound="left", padx=5, anchor="w")
        button = ctk.CTkButton(self, text="Command", width=100, height=24)
        if self.command is not None:
            button.configure(command=lambda: self.command(item))
        label.grid(row=len(self.label_list), column=0, pady=(0, 10), sticky="w")
        button.grid(row=len(self.button_list), column=1, pady=(0, 10), padx=5)
        self.label_list.append(label)
        self.button_list.append(button)

    def remove_item(self, item):
        for label, button in zip(self.label_list, self.button_list):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
                return

class ScrollableTranscripts(ctk.CTkScrollableFrame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.label_list = []
        self.text_list = []

    def add_transcript(self, label, text, image=None):
        label = ctk.CTkLabel(self, text=label, image=image, padx=5)
        textbox = ctk.CTkTextbox(self, corner_radius=10, height=20)
        textbox.insert("0.0", text)
        label.pack(side='top', pady=(0, 10))
        textbox.pack(side='top',  fill='x', pady=(0, 10), padx=5)
        self.label_list.append(label)
        self.text_list.append(textbox)

    def remove_transcript(self, item):
        for label, button in zip(self.label_list, self.button_list):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
                return
            
    def change_transcript(self, label, text, id):
        old_label = self.label_list[id]
        self.label_list[id].destroy()
        self.label_list[id].remove(old_label)
        self.text_list[id] = ctk.CTkLabel(self, text=label, padx=5)

        self.text_list[id].delete("0.0", "end")
        self.text_list[id].insert("0.0", text)

class App:
    def __init__(self, window, window_title, config,  video_path="short.mp4"):
        self.window = window
        self.window.title(window_title)
        self.video_path = video_path
        self.frame_id = 0

        self.resize_frame =(320, 500)
        self.state = "Play"

        temp_path = config["path"]["temp_path"]
        final_path = config["path"]["final_path"]
        transcript_path = config["path"]["transcript_path"]
        filename, ext = os.path.splitext(video_path)
        audio_path = f"{filename}.wav"
        counter_color_change = 0
        cur_frame = 0

        ### Handle audio transcription 
        line_1, line_2, word_timestamps = extract_transcripts(audio_path, video_path, transcript_path, use_api=False)

        # Open video
        self.vid = VideoOpenCv(self.video_path)

        # Create three frames
        self.left_frame =  ctk.CTkFrame(window,  width=100,  height=  400)
        self.left_frame.pack(side='left',  fill='both',  padx=10,  pady=5,  expand=True)

        self.center_frame =  ctk.CTkFrame(window,  width=600,  height=  400)
        self.center_frame.pack(side='left',  fill='both',  padx=10,  pady=5,  expand=True)

        self.right_frame  =  ctk.CTkFrame(window,  height=400)
        self.right_frame.pack(side='left',  fill='both',  padx=10,  pady=5,  expand=True)

        ################### 
        # Left frame
        ################### 
        self.lbl = ctk.CTkLabel(self.left_frame, width=30, text=f"Edition:")
        self.lbl.pack(side='top',  padx=5,  pady=5)
        #### Setup fonts list
        self.themes = ScrollableLabelButtonFrame(self.left_frame, width=200)
        self.themes.pack(side='top', padx=10, pady=5)

        # Get all fonts
        all_font_path = fm.findSystemFonts()
        font_path = all_font_path[0]
        fonts = []
        for path in all_font_path:
            fonts.append(path.split("\\")[-1].split(".")[0])
        fonts.sort()
        font = ImageFont.truetype(font_path, 40)
        highlight_font = ImageFont.truetype(font_path, 44)

        for font in fonts:
            self.themes.add_item(font)

        #### Size fonts
        self.lbl_font = ctk.CTkLabel(self.left_frame, width=30, text=f"Taille police : 50")
        self.lbl_font.pack(side='top', padx=5, pady=5)
        self.font_size = ctk.CTkSlider(self.left_frame, from_=30, to=120, command=self.update_font_size)
        self.font_size.set(50)
        self.font_size.pack(side='top', padx=5, pady=5)

        ################### 
        ### Center frame
        ################### 
        self.lbl_video = ctk.CTkLabel(self.center_frame, width=30, text=f"Chemin vers la vidéo: {video_path}")
        self.lbl_video.pack(side='top',  padx=5,  pady=5)
        self.canvas = ctk.CTkCanvas(self.center_frame, width = self.resize_frame[0], height = self.resize_frame[1])
        self.canvas.pack(side='top',  padx=5,  pady=5)

        #### Setup video slider
        self.video_frame_slider = ctk.CTkSlider(self.center_frame, from_=0, to=self.vid.num_frames, command=self.update_frame_id)
        self.video_frame_slider.pack(side='top',  padx=5,  pady=5)

        #### Setup buttons play/pause
        self.backward_button=ctk.CTkButton(self.center_frame, width=20, text="Backward", command=self.backward_frame)
        self.backward_button.pack(side='left',  padx=5,  pady=5)
        self.play_button=ctk.CTkButton(self.center_frame, width=20, text="Play", command=self.switch_pause)
        self.play_button.pack(side='left',  fill='x', padx=100,  pady=5, expand=True)
        self.forward_button=ctk.CTkButton(self.center_frame, width=20, text="Forward", command=self.forward_frame)
        self.forward_button.pack(side='right',  padx=5,  pady=5)

        ################### 
        ### Right frame
        ################### 
        self.lbl = ctk.CTkLabel(self.right_frame, width=30, text=f"Transcriptions:")
        self.lbl.pack(side='top',  padx=5,  pady=5)

        # Create the box containing the transcripts
        self.transcript_box = ctk.CTkFrame(self.right_frame,  height=200)
        self.transcript_box.pack(side='top', padx=10, pady=5, fill='both', expand=True)
        self.transcript = ScrollableTranscripts(self.transcript_box)
        self.transcript.pack(side='left', fill='both', padx=5,  pady=5, expand=True)
        
        for l1, l2 in zip(line_1, line_2):
            self.transcript.add_transcript(text=l1[1], label=f"Ligne 1 de {l1[0][0]}s à {l1[0][1]}s")
            self.transcript.add_transcript(text=l2[1], label=f"Ligne 2 de {l2[0][0]}s à {l2[0][1]}s")
            
        self.export_button=ctk.CTkButton(self.right_frame, width=30, text="Exporter", command=window.quit)
        self.export_button.pack(side='top',  padx=5,  pady=5)

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 15
        self.update()

        self.window.mainloop()

    def switch_pause(self):
        if self.state == "Play":
            self.state = "Pause"
        else:
            self.state = "Play"

    def forward_frame(self, num_frame=3):
        new_frame = min(self.vid.num_frames, self.frame_id + num_frame)
        ret, frame, self.frame_id = self.vid.new_frame(new_frame)
        self.change_frame(frame)

    def backward_frame(self, num_frame=3):
        new_frame = max(0, self.frame_id - num_frame)
        ret, frame, self.frame_id = self.vid.new_frame(new_frame)
        self.change_frame(frame)

    def update_font_size(self, value):
        self.lbl_font.configure(text = f"Taille police : {int(value)}")

    def update_frame_id(self, frame_id):
        new_frame = self.vid.new_frame(frame_id=frame_id)[1]
        self.change_frame(new_frame)

    def update(self):
        if self.state == "Pause":
            pass
        elif self.state == "Play":
            # Get a frame from the video source
            ret, frame, self.frame_id = self.vid.get_frame()
            if ret:
                self.change_frame(frame)
                self.video_frame_slider.set(self.frame_id)

        self.window.after(self.delay, self.update)

    def change_frame(self, frame):
        imS = cv2.resize(frame, self.resize_frame)
        self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(imS))
        self.canvas.create_image(self.resize_frame[0]/2, self.resize_frame[1]/2, image = self.photo)

class VideoOpenCv:
    def __init__(self, video_path="short.mp4"):
        self.vid = cv2.VideoCapture(video_path)

        # Open the video source
        if not self.vid.isOpened():
            raise ValueError("Unable to open video path", video_path)
        
        # Get video source width and height
        self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.vid.get(cv2.CAP_PROP_FPS)
        self.num_frames = self.vid.get(cv2.CAP_PROP_FRAME_COUNT)
 
    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), self.vid.get(cv2.CAP_PROP_POS_FRAMES))
            else:
                return (ret, None, None)
        else:
            return (ret, None, None)
    
    def new_frame(self, frame_id):
        self.vid.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        return self.get_frame()

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
 
if __name__ == '__main__':
    ################################
    #       Parse arguments        #  
    ################################
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to the config file")
    parser.add_argument("--video_path", type=str, default=None, help="Path to the input video")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

        
    ### Get the filename
    # TODO : Need to be changed to get path another way
    video_path = None
    """video_path = sg.popup_get_file('Fichier à ouvrir') # TODO : replace pysimplegui with Tkinter
    if video_path is None:
        exit()"""

    App(ctk.CTk(), 
        "OpenSubVoice", 
        video_path=video_path if video_path is not None else "D:\Vidéos FINALES\Cette IA joue à minecraft seule.mp4",
        config=config)