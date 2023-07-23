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

ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

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

    def add_transcript(self, text, image=None):
        
        label = ctk.CTkLabel(self, text=text, image=image, padx=5)
        textbox = ctk.CTkTextbox(self, corner_radius=10)
        textbox.insert("0.0", "Some example text!\n")
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

class App:
    def __init__(self, window, window_title, video_path="short.mp4"):
        self.window = window
        self.window.title(window_title)
        self.video_path = video_path
        self.frame_id = 0

        self.resize_frame =(320, 500)
        self.state = "Play"

        # open video
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

        for i in range(1, 10):
            self.themes.add_item(f"Police {i}")

        """all_font_path = fm.findSystemFonts()
        font_path = all_font_path[0]
        i = 0
        for path in all_font_path: 
            self.themes.add_item(path.split("\\")[-1].split(".")[0])
            i+= 1"""

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

        self.transcript_box = ctk.CTkFrame(self.right_frame,  height=200)
        self.transcript_box.pack(side='top', padx=10, pady=5, fill='both', expand=True)
        self.transcript = ScrollableTranscripts(self.transcript_box)
        self.transcript.pack(side='left', fill='both', padx=5,  pady=5, expand=True)
        
        for i in range(1, 20):
            self.transcript.add_transcript(f"This is a text {i}")
            
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
    """parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to the config file")
    parser.add_argument("--video_path", type=str, default=None, help="Path to the input video")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

        
    ### Get the filename
    video_path = sg.popup_get_file('Fichier à ouvrir') # TODO : replace pysimplegui with Tkinter
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

    
    all_font_path = fm.findSystemFonts()
    font_path = all_font_path[0]
    fonts = []
    for path in all_font_path:
        fonts.append(path.split("\\")[-1].split(".")[0])
    fonts.sort()
    font = ImageFont.truetype(font_path, 40)
    highlight_font = ImageFont.truetype(font_path, 44)"""

    App(ctk.CTk(), "OpenSubVoice", video_path="D:\Vidéos FINALES\Cette IA joue à minecraft seule.mp4")