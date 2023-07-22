import PySimpleGUI as sg
import textwrap

### Simple material theme inspired : https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Simple_Material_Feel.py
USE_FADE_IN = True
WIN_MARGIN = 60

# colors
WIN_COLOR = "#282828"
TEXT_COLOR = "#ffffff"

DEFAULT_DISPLAY_DURATION_IN_MILLISECONDS = 10000

# Base64 Images to use as icons in the window
img_error = b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAA3NCSVQICAjb4U/gAAAACXBIWXMAAADlAAAA5QGP5Zs8AAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAIpQTFRF////20lt30Bg30pg4FJc409g4FBe4E9f4U9f4U9g4U9f4E9g31Bf4E9f4E9f4E9f4E9f4E9f4FFh4Vdm4lhn42Bv5GNx5W575nJ/6HqH6HyI6YCM6YGM6YGN6oaR8Kev9MPI9cbM9snO9s3R+Nfb+dzg+d/i++vt/O7v/fb3/vj5//z8//7+////KofnuQAAABF0Uk5TAAcIGBktSYSXmMHI2uPy8/XVqDFbAAAA8UlEQVQ4y4VT15LCMBBTQkgPYem9d9D//x4P2I7vILN68kj2WtsAhyDO8rKuyzyLA3wjSnvi0Eujf3KY9OUP+kno651CvlB0Gr1byQ9UXff+py5SmRhhIS0oPj4SaUUCAJHxP9+tLb/ezU0uEYDUsCc+l5/T8smTIVMgsPXZkvepiMj0Tm5txQLENu7gSF7HIuMreRxYNkbmHI0u5Hk4PJOXkSMz5I3nyY08HMjbpOFylF5WswdJPmYeVaL28968yNfGZ2r9gvqFalJNUy2UWmq1Wa7di/3Kxl3tF1671YHRR04dWn3s9cXRV09f3vb1fwPD7z9j1WgeRgAAAABJRU5ErkJggg=='
img_success = b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAA3NCSVQICAjb4U/gAAAACXBIWXMAAAEKAAABCgEWpLzLAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAHJQTFRF////ZsxmbbZJYL9gZrtVar9VZsJcbMRYaMZVasFYaL9XbMFbasRZaMFZacRXa8NYasFaasJaasFZasJaasNZasNYasJYasJZasJZasJZasJZasJZasJYasJZasJZasJZasJZasJaasJZasJZasJZasJZ2IAizQAAACV0Uk5TAAUHCA8YGRobHSwtPEJJUVtghJeYrbDByNjZ2tvj6vLz9fb3/CyrN0oAAADnSURBVDjLjZPbWoUgFIQnbNPBIgNKiwwo5v1fsQvMvUXI5oqPf4DFOgCrhLKjC8GNVgnsJY3nKm9kgTsduVHU3SU/TdxpOp15P7OiuV/PVzk5L3d0ExuachyaTWkAkLFtiBKAqZHPh/yuAYSv8R7XE0l6AVXnwBNJUsE2+GMOzWL8k3OEW7a/q5wOIS9e7t5qnGExvF5Bvlc4w/LEM4Abt+d0S5BpAHD7seMcf7+ZHfclp10TlYZc2y2nOqc6OwruxUWx0rDjNJtyp6HkUW4bJn0VWdf/a7nDpj1u++PBOR694+Ftj/8PKNdnDLn/V8YAAAAASUVORK5CYII='

def display_notification(title, message, is_success=True, display_duration_in_ms=DEFAULT_DISPLAY_DURATION_IN_MILLISECONDS, use_fade_in=True, alpha=0.9, location=None):
    """
    Function that will create, fade in and out, a small window that displays a message with an icon
    The graphic design is similar to other system/program notification windows seen in Windows / Linux
    :param title: (str) Title displayed at top of notification
    :param message: (str) Main body of the noficiation
    :param icon: (str) Base64 icon to use. 2 are supplied by default
    :param display_duration_in_ms: (int) duration for the window to be shown
    :param use_fade_in: (bool) if True, the window will fade in and fade out
    :param alpha: (float) Amount of Alpha Channel to use.  0 = invisible, 1 = fully visible
    :param location: Tuple[int, int] location of the upper left corner of window. Default is lower right corner of screen
    """

    # Compute location and size of the window
    message = textwrap.fill(message, 50)
    win_msg_lines = message.count("\n") + 1

    screen_res_x, screen_res_y = sg.Window.get_screen_size()
    win_margin = WIN_MARGIN  # distance from screen edges
    win_width, win_height = 364, 66 + (14.8 * win_msg_lines)
    win_location = location if location is not None else (screen_res_x - win_width - win_margin, screen_res_y - win_height - win_margin)

    layout = [[sg.Graph(canvas_size=(win_width, win_height), graph_bottom_left=(0, win_height), graph_top_right=(win_width, 0), key="-GRAPH-",
                        background_color=WIN_COLOR, enable_events=True)]]

    window = sg.Window(title, layout, background_color=WIN_COLOR, no_titlebar=True,
                       location=win_location, keep_on_top=True, alpha_channel=0, margins=(0, 0), element_padding=(0, 0),
                       finalize=True)

    window["-GRAPH-"].draw_rectangle((win_width, win_height), (-win_width, -win_height), fill_color=WIN_COLOR, line_color=WIN_COLOR)
    if is_success:
        window["-GRAPH-"].draw_image(data=img_success, location=(20, 20))
    else:
        window["-GRAPH-"].draw_image(data=img_error, location=(20, 20))
    window["-GRAPH-"].draw_text(title, location=(64, 20), color=TEXT_COLOR, font=("Arial", 12, "bold"), text_location=sg.TEXT_LOCATION_TOP_LEFT)
    window["-GRAPH-"].draw_text(message, location=(64, 44), color=TEXT_COLOR, font=("Arial", 9), text_location=sg.TEXT_LOCATION_TOP_LEFT)

    # change the cursor into a "hand" when hovering over the window to give user hint that clicking does something
    window['-GRAPH-'].set_cursor('hand2')

    if use_fade_in == True:
        for i in range(1,int(alpha*100)):               # fade in
            window.set_alpha(i/100)
            event, values = window.read(timeout=20)
            if event != sg.TIMEOUT_KEY:
                window.set_alpha(1)
                break
        event, values = window(timeout=display_duration_in_ms)
        if event == sg.TIMEOUT_KEY:
            for i in range(int(alpha*100),1,-1):       # fade out
                window.set_alpha(i/100)
                event, values = window.read(timeout=20)
                if event != sg.TIMEOUT_KEY:
                    break
    else:
        window.set_alpha(alpha)
        event, values = window(timeout=display_duration_in_ms)

    window.close()

def make_window(fonts, num_frames, line_1, line_2, light_mode=False):
    if light_mode:
        sg.theme('light grey')
    else:
        sg.theme('black')

    BLUE = '#2196f2'
    DARK_GRAY = '#212021'
    LIGHT_GRAY = '#e0e0e0'
    BLUE_BUTTON_COLOR = '#FFFFFF on #2196f2'
    GREEN_BUTTON_COLOR ='#FFFFFF on #00c851'
    LIGHT_GRAY_BUTTON_COLOR = f'#212021 on #e0e0e0'
    DARK_GRAY_BUTTON_COLOR = '#e0e0e0 on #212021'

    menu_def = [['Fichier', ['Nouveau', 'Ouvrir', 'Enregistrer', 'Exporter','Quitter', ]],  ['Aide', 'A propos...']]
    ### Prepare the layout 
    layout = [
            [sg.MenubarCustom(menu_def, pad=(0,0), k='-cust_menubar-')],
            [sg.Column(
                [
                [sg.Listbox(fonts, size=(30, 20), change_submits=True, key='-list-')],
                [sg.Text("Taille de la police :")],
                [sg.Slider(range=(30, 130), size=(15, 10), orientation='h', key='-font_size-', change_submits=True)],
                [sg.Button('Exporter', size=(10, 2), key='-export-', button_color=LIGHT_GRAY_BUTTON_COLOR if light_mode else DARK_GRAY_BUTTON_COLOR)]
                ], 
                element_justification='c'
            ),
            sg.Column(
                [
                    [sg.Image(key='-image-')],
                    [sg.Text(text="", key='-error-', text_color="Red", font=('Arial Bold', 10))],
                    [sg.Slider(range=(0, num_frames), size=(30, 10), orientation='h', key='-vid_slider-', change_submits=True)],
                ], 
                element_justification='c'
            ),
            sg.Column([[sg.Text('Transcriptions')]], scrollable=True, key='-transcripts-', s=(500,400))],
            ]
    
    window = sg.Window('OpenSubVoice', 
                    layout, 
                    size=(1280, 720), 
                    use_custom_titlebar=True,
                    titlebar_icon="assets/icon_2.png",
                    titlebar_background_color=LIGHT_GRAY if light_mode else DARK_GRAY,
                    titlebar_text_color=DARK_GRAY if light_mode else LIGHT_GRAY,
                    resizable=True,
                    button_color=LIGHT_GRAY_BUTTON_COLOR)
    return window