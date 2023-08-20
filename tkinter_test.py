import customtkinter as ctk
import cv2
import PIL.Image, PIL.ImageTk
import argparse
import yaml
import os
import PySimpleGUI as sg
from PIL import ImageFont

from widgets.font_button import ScrollableLabelButtonFrame
from widgets.transcripts import ScrollableTranscripts
from widgets.video_frame import VideoOpenCv
from utils.audio import extract_transcripts

ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

# TODO : adapt this to get right font
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

        ### Handle audio transcription 
        self.line_1, self.line_2, self.word_timestamps = extract_transcripts(audio_path, video_path, transcript_path, use_api=False)

        # Create three frames
        self.setup_left_frame(window, config) # Frame for fonts 
        self.setup_center_frame(window) # Frame for videos
        self.setup_right_frame(window) # Frame for transcriptions

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 15
        self.update()

        self.window.mainloop()

    def setup_left_frame(self, window, config):
        theme_name = config["path"]["theme"]

        self.font_dir = "./assets/fonts/"
        all_font_path = os.listdir(self.font_dir)
        theme_path = "./assets/themes/" + theme_name + ".yaml"
        with open(theme_path) as f:
            theme_config = yaml.load(f, Loader=yaml.FullLoader)
        font_path = self.font_dir + theme_config["font"]

        font = ImageFont.truetype(font_path, 40)
        highlight_font = ImageFont.truetype(font_path, 44)
        self.vid = VideoOpenCv(font, highlight_font, self.font_dir, self.video_path)

        self.left_frame =  ctk.CTkFrame(window,  width=100,  height=  400)
        self.left_frame.pack(side='left',  fill='both',  padx=10,  pady=5,  expand=True)

        self.lbl = ctk.CTkLabel(self.left_frame, width=30, text=f"Edition:")
        self.lbl.pack(side='top',  padx=5,  pady=5)
        #### Setup fonts list
        self.themes = ScrollableLabelButtonFrame(self.left_frame, width=200, command=self.vid.change_font_name)
        self.themes.pack(side='top', padx=10, pady=5)

        # Get all fonts
        fonts = []
        for path in all_font_path:
            fonts.append(path.split("\\")[-1].split(".")[0])
        fonts.sort()

        #### Size fonts
        self.lbl_font = ctk.CTkLabel(self.left_frame, width=30, text=f"Taille police : 50")
        self.lbl_font.pack(side='top', padx=5, pady=5)
        self.font_size = ctk.CTkSlider(self.left_frame, from_=30, to=120, command=self.update_font_size)
        self.font_size.set(50)
        self.font_size.pack(side='top', padx=5, pady=5)

        # TODO : only have a selection of fonts + tutorial to add more
        for font in fonts:
            self.themes.add_item(font, self.font_size)

    def setup_center_frame(self, window):
        self.center_frame =  ctk.CTkFrame(window,  width=600,  height=  400)
        self.center_frame.pack(side='left',  fill='both',  padx=10,  pady=5,  expand=True)
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
    
    def setup_right_frame(self, window):
        self.right_frame  =  ctk.CTkFrame(window,  height=400)
        self.right_frame.pack(side='left',  fill='both',  padx=10,  pady=5,  expand=True)


        self.lbl = ctk.CTkLabel(self.right_frame, width=30, text=f"Transcriptions:")
        self.lbl.pack(side='top',  padx=5,  pady=5)

        # Create the box containing the transcripts
        self.transcript_box = ctk.CTkFrame(self.right_frame,  height=200)
        self.transcript_box.pack(side='top', padx=10, pady=5, fill='both', expand=True)
        self.transcript = ScrollableTranscripts(self.transcript_box, self.update_timestamp)
        self.transcript.pack(side='left', fill='both', padx=5,  pady=5, expand=True)
        text_id = 1
        for l1, l2 in zip(self.line_1, self.line_2):
            self.transcript.add_transcript(text=l1[1], label=f"Ligne 1 de {l1[0][0]}s à {l1[0][1]}s", text_id=text_id)
            text_id += 1
            self.transcript.add_transcript(text=l2[1], label=f"Ligne 2 de {l2[0][0]}s à {l2[0][1]}s", text_id=text_id)
            text_id += 1
            
        self.export_button=ctk.CTkButton(self.right_frame, width=30, text="Exporter", command=window.quit)
        self.export_button.pack(side='top',  padx=5,  pady=5)
    
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
        self.vid.change_font_size(int(value))

    def update_timestamp(self, textbox, text_id=1):
        # TODO : change timestep according to the line and word timestamps
        new_text = textbox.get("1.0", "end-1c")
        line_id = 1 if text_id % 2 else 2
        timestep_id = int(text_id / 2) - line_id + 1
        if line_id == 1:
            self.line_1[timestep_id] = (self.line_1[timestep_id][0], new_text, self.line_1[timestep_id][2])
        else:
            self.line_2[timestep_id] = (self.line_2[timestep_id][0], new_text, self.line_1[timestep_id][2])

    def update_frame_id(self, frame_id):
        self.frame_id = frame_id
        frame = self.vid.new_frame(frame_id=frame_id)[1]
        new_frame = self.vid.update_frame(frame, self.frame_id, self.line_1, self.line_2, self.word_timestamps)
        self.change_frame(new_frame)

    def update(self):
        if self.state == "Pause":
            # Get a frame from the video source
            ret, frame, self.frame_id = self.vid.new_frame(self.frame_id-1)
        elif self.state == "Play":
            # Get a frame from the video source
            ret, frame, self.frame_id = self.vid.get_frame()
        if ret:
            self.change_frame(frame)
            self.video_frame_slider.set(self.frame_id)
        new_frame = self.vid.update_frame(frame, self.frame_id, self.line_1, self.line_2, self.word_timestamps)
        self.change_frame(new_frame)
        self.window.after(self.delay, self.update)

    def change_frame(self, frame):
        imS = cv2.resize(frame, self.resize_frame)
        self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(imS))
        self.canvas.create_image(self.resize_frame[0]/2, self.resize_frame[1]/2, image = self.photo)


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