import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import math
import os

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
    words = text.split()
    word_sizes = [draw.textsize(word, font=font) for word in words]
    text_width, text_height = draw.textsize(text, font=font)
    text_origin = ((frame_width - text_width) // 2,  text_height + offset_top)
    highlight_color = (0, 255, 255)
    stroke_color = (0, 0, 0)
    stroke_width = 10
    text_color = (255, 255, 255)

    highlighted_word, word_id = get_current_word(word_timestamps, current_time)
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

def check_font_path(name):
    for ext in ["ttf", "otf"]:
        font_file = f"{name}.{ext}"
        if os.path.isfile(font_file):
            new_name = font_file
            break
    return new_name

class VideoOpenCv:
    def __init__(self, font, highlight_font, font_dir="", video_path="short.mp4"):
        self.vid = cv2.VideoCapture(video_path)

        # Open the video source
        if not self.vid.isOpened():
            raise ValueError("Unable to open video path", video_path)
        
        # Get video source width and height
        self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.vid.get(cv2.CAP_PROP_FPS)
        self.num_frames = self.vid.get(cv2.CAP_PROP_FRAME_COUNT)
        self.font = font
        self.highlight_font = highlight_font
        self.ratio = self.height / self.width
        self.font_dir = font_dir

    def update_frame(self, frame, frame_id, line_1, line_2, word_timestamps):
        # Convert the frame to PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(np.array(frame), cv2.COLOR_BGR2RGB))

        # Draw the text and prompt on the PIL Image
        draw = ImageDraw.Draw(pil_image)

        current_time = frame_id / self.fps
        frame_text_1 = draw_text_on_image(
            line_1, draw, current_time, self.font, self.highlight_font,
            self.width, word_timestamps, 50, pil_image)
        frame_text_2 = draw_text_on_image(
            line_2, draw, current_time, self.font, self.highlight_font,
            self.width, word_timestamps, 150, frame_text_1, to_pil=False)

        return frame_text_2

    def change_font_size(self, size):
        name = self.font.getname()[0]
        name = self.font_dir + name
        name = name.lower()
        name = check_font_path(name)
        self.font = ImageFont.truetype(name, size)
        self.highlight_font = ImageFont.truetype(name, size+5)

    def change_font_name(self, size, name):
        name = self.font_dir + name
        name = check_font_path(name)
        self.font = ImageFont.truetype(name, int(size.get()))
        self.highlight_font = ImageFont.truetype(name, int(size.get())+5)
 
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
 