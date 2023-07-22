
def process_words(word_timestamps):
    """
    Given the words and their associated timestamps, extract them in two lines 
    to be shown on screen and apply some processing.
    """
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
    """
    Returns the current sentence said associated with the given frame
    """
    for timestamp, text in text_timestamps:
        if frametime >= timestamp[0] and frametime < timestamp[1]:
            return text
    return ''

def get_current_word(word_timestamps, frametime):
    """
    Returns the current word said associated with the given frame
    """
    for timestamp, word in word_timestamps:
        if frametime >= timestamp[0] and frametime < timestamp[1]:
            return word
    return ''
