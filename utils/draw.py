import cv2
import math
import numpy as np
from .text import get_current_word, get_current_text

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
    highlight_color = (255, 255, 0)
    stroke_color = (0, 0, 0)
    stroke_width = 10
    text_color = (255, 255, 255)

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
