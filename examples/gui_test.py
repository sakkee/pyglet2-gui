import pyglet
from pyglet.gl import *
from pyglet2_gui.theme import ThemeFromPath
from pyglet2_gui.manager import Manager
from pyglet2_gui.constants import *
from pyglet2_gui.gui import Frame, Label
from pyglet2_gui.option_selectors import Dropdown
from pyglet2_gui.buttons import HighlightedButton, Checkbox, Button, OneTimeButton, FocusButton
from pyglet2_gui.extra import PopupInput, PopupConfirm, PopupMessage
from pyglet2_gui.document import Document
from pyglet2_gui.scrollable import Scrollable
from pyglet2_gui.sliders import HorizontalSlider
from pyglet2_gui.containers import VerticalContainer, HorizontalContainer, GridContainer
import random

default_theme_path = "theme/default"
dark_theme_path = "theme/dark"
window = pyglet.window.Window(width=1024, height=768, resizable=True)
glClearColor(1, 1, 1, 1)
batch = pyglet.graphics.Batch()


@window.event
def on_draw():
    window.clear()
    batch.draw()


class Gui:
    def __init__(self, window: pyglet.window.Window, batch: pyglet.graphics.Batch):
        self.click_counter = 0
        self.tmp_object = None
        self.window = window
        self.batch = batch
        self.group0 = pyglet.graphics.Group(order=0)
        self.group1 = pyglet.graphics.Group(order=1)
        self.default_theme = ThemeFromPath(default_theme_path)
        self.dark_theme = ThemeFromPath(dark_theme_path)
        self.using_theme = self.default_theme
        self.left_manager = self.create_left_manager("Label")
        self.right_option_container = VerticalContainer(
            self.create_right_option_content("Label"))
        select_container = VerticalContainer(content=[
            Label(text="Options"),
            Dropdown(options=["Label", "Button", "Theme", "Popups", "Document", "Containers",
                              "Frame", "Scrollbars", "Sliders"], on_select=self.on_select),
            self.right_option_container
        ])

        self.right_manager = Manager(
            Frame(select_container),
            window=self.window,
            batch=self.batch,
            theme=self.using_theme,
            is_movable=True,
            anchor=ANCHOR_RIGHT,
            offset=(-50, 0),
            group=self.group0
        )

    def create_right_option_content(self, type: str) -> list:
        content = []
        if type == "Label":
            def to_italic(checked: bool):
                if checked:
                    self.tmp_object.italic = True
                    self.tmp_object.refresh()
                else:
                    self.tmp_object.italic = False
                    self.tmp_object.refresh()
            content.append(Checkbox("Italic", on_press=to_italic))

            def to_bold(checked: bool):
                if checked:
                    self.tmp_object.bold = True
                    self.tmp_object.refresh()
                else:
                    self.tmp_object.bold = False
                    self.tmp_object.refresh()
            content.append(Checkbox("Bold", on_press=to_bold))

            def increase_opacity(_):
                self.tmp_object.opacity += 0.1
                self.tmp_object.refresh()
            def reduce_opacity(_):
                self.tmp_object.opacity -= 0.1
                self.tmp_object.refresh()
            content.append(HorizontalContainer(content=[
                HighlightedButton("-", on_press=reduce_opacity),
                Label("Opacity"),
                HighlightedButton("+", on_press=increase_opacity)
            ]))

            def random_color(_):
                self.tmp_object.color = tuple([random.randrange(0, 256) for x in range(0, 3)]) + (self.tmp_object.alpha,)
                self.tmp_object.refresh()
            content.append(HighlightedButton("Random color", on_press=random_color))

            def increase_size(_):
                self.tmp_object.font_size += 1
                self.tmp_object.refresh()
            def reduce_size(_):
                self.tmp_object.font_size -= 1
                self.tmp_object.refresh()
            content.append(HorizontalContainer(content=[
                HighlightedButton("-", on_press=reduce_size),
                Label("Font size"),
                HighlightedButton("+", on_press=increase_size)
            ]))

            def to_multiline(checked: bool):
                if checked:
                    self.tmp_object.multiline = True
                    self.tmp_object.w = 100  # must be set when multiline
                    self.tmp_object.refresh()
                else:
                    self.tmp_object.multiline = False
                    self.tmp_object.w = None  # must be set when multiline
                    self.tmp_object.refresh()
            content.append(Checkbox("Multiline", on_press=to_multiline))

        elif type == "Button":
            def change_button(btn_type: str):
                self.left_manager.delete()
                self.left_manager = self.create_left_manager(btn_type, False)

            content.append(Label("Button type:"))
            content.append(Dropdown(["Highlighted", "NormalBtn", "OneTime", "FocusBtn", "Graphic Btn",
                                     "Graphic Outline"], on_select=change_button))

        elif type == "Theme":
            def dark_selected(is_dark: bool):
                self.using_theme = self.dark_theme if is_dark else self.default_theme

                if is_dark:
                    glClearColor(0, 0, 0, 1)
                else:
                    glClearColor(1, 1, 1, 1)
                self.right_manager.update_theme(self.using_theme)
                self.left_manager.update_theme(self.using_theme)
                self.tmp_object.set_text("This is default theme." if self.using_theme == self.default_theme else \
                                 "This is dark theme.")
            content.append(Checkbox("Dark Theme", on_press=dark_selected, is_pressed=self.using_theme == self.dark_theme))

        elif type == "Popups":
            self.left_manager.delete()
            def popup_message(_):
                if self.left_manager:
                    self.left_manager.delete()
                self.left_manager = PopupMessage("This is a popup message!", theme=self.using_theme, window=self.window,
                                                 batch=self.batch, group=self.group1)
            def popup_confirm(_):
                if self.left_manager:
                    self.left_manager.delete()
                def on_ok(_):
                    if self.left_manager:
                        self.left_manager.delete()
                    self.left_manager = PopupMessage("You like this lol", theme=self.using_theme,
                                                     window=self.window,
                                                     batch=self.batch, group=self.group1)
                def on_cancel(_):
                    if self.left_manager:
                        self.left_manager.delete()
                    self.left_manager = PopupMessage("you dont like this!", theme=self.using_theme,
                                                     window=self.window,
                                                     batch=self.batch, group=self.group1)
                self.left_manager = PopupConfirm("Do you like this GUI?", ok="Yes!", cancel="No, f* this", theme=self.using_theme, window=self.window,
                                                 batch=self.batch, group=self.group1, on_ok=on_ok, on_cancel=on_cancel)

            def popup_input(_):
                if self.left_manager:
                    self.left_manager.delete()
                def on_ok(text: str):
                    if self.left_manager:
                        self.left_manager.delete()
                    self.left_manager = PopupMessage(f"The reason why you don't like this is: {text}", theme=self.using_theme,
                                                     window=self.window,
                                                     batch=self.batch, group=self.group1)
                def on_cancel(text: str):
                    if self.left_manager:
                        self.left_manager.delete()
                    self.left_manager = PopupMessage("ok...", theme=self.using_theme,
                                                     window=self.window,
                                                     batch=self.batch, group=self.group1)
                self.left_manager = PopupInput("What do you think about this GUI", theme=self.using_theme, window=self.window,
                                                 batch=self.batch, group=self.group1, on_ok=on_ok, on_cancel=on_cancel,
                                               placeholder="Your opinion")

            content.append(HighlightedButton("PopupMessage", on_press=popup_message))
            content.append(HighlightedButton("PopupConfirm", on_press=popup_confirm))
            content.append(HighlightedButton("PopupInput", on_press=popup_input))

        elif type == "Document":
            def vert_scrollbar(is_vert: bool):
                if self.left_manager:
                    self.left_manager.delete()
                document_text = '{font_size 16}{background_color (255,255,255,255)}{wrap_lines True}{wrap True}This is ' + \
                                '{bold True}a document{bold False}.\n' + \
                                '{background_color (200, 200, 200, 255)}{color (0,100,100,255)}You can add different styles in the text\n' + \
                                '{background_color (0, 0, 0, 0)}{color (0,0,0,255)}Please read pyglet formatting text documentation ' + \
                                'for further info.'
                formatted_document = pyglet.text.decode_attributed(document_text)
                self.tmp_object = Document(formatted_document, width=150, height=150 if is_vert else 0)
                self.left_manager = Manager(Frame(self.tmp_object),
                                            theme=self.using_theme, window=self.window, batch=self.batch,
                                            group=self.group1)
            content.append(Checkbox("Vertical Scrollbar", on_press=vert_scrollbar))

        elif type == "Containers":
            def vertical_container(_):
                if self.left_manager:
                    self.left_manager.delete()
                self.left_manager = Manager(Frame(VerticalContainer([
                    Label("Text 1"), Label("Text 2"), Label("Text 3")
                ])), theme=self.using_theme, window=self.window, batch=self.batch,
                                            group=self.group1)
            content.append(HighlightedButton("Vertical Container", on_press=vertical_container))

            def horizontal_container(_):
                if self.left_manager:
                    self.left_manager.delete()
                self.left_manager = Manager(Frame(HorizontalContainer([
                    Label("Text 1"), Label("Text 2"), Label("Text 3")
                ])), theme=self.using_theme, window=self.window, batch=self.batch,
                                            group=self.group1)
            content.append(HighlightedButton("Horizontal Container", on_press=horizontal_container))

            def grid_container(_):
                if self.left_manager:
                    self.left_manager.delete()
                self.left_manager = Manager(Frame(GridContainer([
                    [Label("Text 1.1"), Label("Text 1.2"), Label("Text 1.3")],
                    [Label("Text 2.1"), Label("Text 2.2"), Label("Text 2.3")],
                    [Label("Text 3.1"), Label("Text 3.2"), Label("Text 3.3")]
                ])), theme=self.using_theme, window=self.window, batch=self.batch,
                                            group=self.group1)
            content.append(HighlightedButton("Grid Container", on_press=grid_container))

        elif type == "Frame":
            def no_frame(_):
                if self.left_manager:
                    self.left_manager.delete()
                self.left_manager = Manager(Label("This Manager has no Frame"),
                                            theme=self.using_theme, window=self.window, batch=self.batch,
                    group=self.group1)
            content.append(HighlightedButton("No Frame", on_press=no_frame))

            def normal_frame(_):
                if self.left_manager:
                    self.left_manager.delete()
                self.left_manager = Manager(Frame(Label("This Manager has normal Frame")),
                                            theme=self.using_theme, window=self.window, batch=self.batch,
                    group=self.group1)
            content.append(HighlightedButton("Normal Frame", on_press=normal_frame))

            def title_frame(_):
                if self.left_manager:
                    self.left_manager.delete()
                self.left_manager = Manager(TitleFrame("This is the title.",
                                                                       Label("This is the content.")),
                                            theme=self.using_theme, window=self.window, batch=self.batch,
                    group=self.group1)
            content.append(HighlightedButton("Title Frame", on_press=title_frame))

        elif type == "Scrollbars":
            def vertical_scrollbar(_):
                if self.left_manager:
                    self.left_manager.delete()
                self.left_manager = Manager(
                    Scrollable(height=200,
                               content=VerticalContainer(content=[HighlightedButton(str(x)) for x in range(15)])),
                    theme=self.using_theme, window=self.window, batch=self.batch, group=self.group1,
                    is_movable=False
                )
            content.append(HighlightedButton("Vertical Scrollbar", on_press=vertical_scrollbar))

            def horizontal_scrollbar(_):
                if self.left_manager:
                    self.left_manager.delete()
                self.left_manager = Manager(
                    Scrollable(width=150,
                               content=HorizontalContainer(content=[HighlightedButton(str(x)) for x in range(15)])),
                    theme=self.using_theme, window=self.window, batch=self.batch, group=self.group1,
                    is_movable=False
                )
            content.append(HighlightedButton("Horizontal Scrollbar", on_press=horizontal_scrollbar))

        return content

    def create_left_frame(self, type: str) -> Frame:
        content = []
        if type == "Label":
            self.tmp_object = Label("This is a label.")
            content.append(self.tmp_object)

        elif type == "Highlighted":
            self.click_counter = 0
            def on_release(_):
                self.click_counter += 1
                self.tmp_object.set_text(f"You have clicked {self.click_counter} times!")
            content.append(HighlightedButton(label="This is a highlighted button.", on_release=on_release))
            self.tmp_object = Label(f"You have clicked {self.click_counter} times!")
            content.append(self.tmp_object)

        elif type == "NormalBtn":
            self.click_counter = 0
            def on_press(_):
                self.click_counter += 1
                self.tmp_object.set_text(f"You have clicked {self.click_counter} times!")
            content.append(Button(label="This is a normal button.", on_press=on_press))
            self.tmp_object = Label(f"You have clicked {self.click_counter} times!")
            content.append(self.tmp_object)

        elif type == "OneTime":
            self.click_counter = 0
            def on_release(_):
                self.click_counter += 1
                self.tmp_object.set_text(f"You have clicked {self.click_counter} times!")

            content.append(OneTimeButton(label="This is a one time button.", on_release=on_release))
            self.tmp_object = Label(f"You have clicked {self.click_counter} times!")
            content.append(self.tmp_object)

        elif type == "FocusBtn":
            content.append(FocusButton(label="This is a focus button."))
            content.append(Label("Try to press TAB and ENTER."))

        elif type == "Graphic Btn":
            def on_press(_):
                self.tmp_object.set_text("Shop opened!")
            content.append(HighlightedButton(path="bag", width=64, height=64, on_press=on_press))
            self.tmp_object = Label("Open shop.")
            content.append(self.tmp_object)

        elif type == "Graphic Outline":
            def on_press(_):
                self.tmp_object.set_text("Shop opened!")
            content.append(HighlightedButton(texture=pyglet.resource.image("data/gui/default/bag.png"), width=64, height=64, on_press=on_press, outline_path='outline'))
            self.tmp_object = Label("Open shop.")
            content.append(self.tmp_object)

        elif type == "Theme":
            self.tmp_object = Label(f"This is default theme." if self.using_theme == self.default_theme else \
                                 "This is dark theme.")
            content.append(self.tmp_object)

        elif type == "Document":
            document_text = '{font_size 16}{background_color (255,255,255,255)}{wrap_lines True}{wrap True}This is ' + \
                            '{bold True}a document{bold False}.\n' + \
                            '{background_color (200, 200, 200, 255)}{color (0,100,100,255)}You can add different styles in the text\n' + \
                '{background_color (0, 0, 0, 0)}{color (0,0,0,255)}Please read pyglet formatting text documentation ' + \
                    'for further info.'
            formatted_document = pyglet.text.decode_attributed(document_text)
            self.tmp_object = Document(formatted_document, width=150)
            content.append(self.tmp_object)

        elif type == "Containers":
            return Frame(VerticalContainer([
                Label("Text 1"), Label("Text 2"), Label("Text 3")
            ]))

        elif type == "Frame":
            content.append(Label("This Manager has normal Frame"))

        elif type == "Scrollbars":
            content.append(Scrollable(height=200,
                       content=VerticalContainer(content=[HighlightedButton(str(x)) for x in range(15)])))

        elif type == "Sliders":
            self.tmp_object = Label("Value: 0")
            content.append(self.tmp_object)
            def change_value(value):
                self.tmp_object.set_text(f"Value: {value}")
            content.append(HorizontalSlider(on_set=change_value))
            content.append(HorizontalSlider(steps=10, on_set=change_value))

        return Frame(VerticalContainer(content=content))

    def create_left_manager(self, type: str, ignore_btn: bool = True):
        type = "Highlighted" if type == "Button" and ignore_btn else type
        return Manager(
            self.create_left_frame(type),
            window=self.window, batch=self.batch, theme=self.using_theme, is_movable=False, anchor=ANCHOR_CENTER,
            group=self.group1
        )

    def on_select(self, type: str):
        self.left_manager.delete()
        self.left_manager = self.create_left_manager(type)
        self.right_option_container.delete_contents()
        for x in self.create_right_option_content(type):
            self.right_option_container.add(x)


gui = Gui(window, batch)
pyglet.app.run()
