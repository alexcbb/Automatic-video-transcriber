import customtkinter as ctk

class ScrollableTranscripts(ctk.CTkScrollableFrame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.label_list = []
        self.text_list = []

    def add_transcript(self, label, text, text_id, image=None):
        label = ctk.CTkLabel(self, text=label, image=image, padx=5)
        textbox = ctk.CTkTextbox(self, corner_radius=10, height=20)
        if self.command is not None:
            textbox.bind("<KeyRelease>", command=lambda event:self.command(textbox, text_id))
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
