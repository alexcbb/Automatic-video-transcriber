import PySimpleGUI as sg

"""
    Demonstrates how to use the Window.layout_extend method.
    Layouts can be extended at the Window level or within any container element such as a Column.
    This demo shows how to extend both.
    Note that while you can extend, add to, a layout, you cannot delete items from a layout.  Of course you
    can make them invisible after adding them.
    
    When using scrollable Columns be sure and call Column.visibility_changed so that the scrollbars will
        be correctly reposititioned
        
    Copyright 2020, 2022 PySimpleGUI
"""

layout = [  [sg.Text('My Window')],
            [sg.Text('Click to add a row inside the Column'), sg.B('+', key='-ADD COL-')],
            [sg.Col([[sg.T('Column')]], scrollable=True, key='-COL-', s=(400,400))],
            [sg.Button('Button'), sg.Button('Exit')]  ]

window = sg.Window('Window Title', layout)

i = 0

while True:             # Event Loop
    event, values = window.read()
    print(event, values)
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    elif event == '-ADD COL-':
        window.extend_layout(window['-COL-'], [[sg.T('A New Input Line'), sg.I(key=f'-IN-{i}-')]])
        window.visibility_changed()
        window['-COL-'].contents_changed()
        i += 1
window.close()