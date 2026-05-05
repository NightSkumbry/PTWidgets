from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.styles import Style
from pt_widgets.widgets.brackets import BracketType
from pt_widgets.widgets.button import Button
from pt_widgets.widgets.label import Label
from pt_widgets.layout.navigation import VerticalLayout, HorizontalLayout
from pt_widgets.widgets.common import WidgetState, WidgetStyle

def run():
    # Определяем стили для виджетов
    style = Style.from_dict({
        "pt_widget.button": "fg:white bg:blue",
        "pt_widget.button.focused": "fg:black bg:yellow",
        "pt_widget.button.disabled": "fg:gray bg:black",

        "pt_widget.label": "fg:green",
        "pt_widget.label.focused": "fg:black bg:green",
        
        "pt_widget.brackets": "fg:cyan bg:blue",
        "pt_widget.brackets.focused": "fg:red bg:yellow",
        "pt_widget.brackets.disabled": "fg:gray bg:black",
    })

    # Состояния для кнопок, чтобы они могли отключать друг друга
    state1 = WidgetState(focusable=True, disabled=False)
    state2 = WidgetState(focusable=True, disabled=False)
    state3 = WidgetState(focusable=True, disabled=False)

    def toggle_2_3():
        state2.disabled = not state2.disabled
        state3.disabled = not state3.disabled

    def disable_self(state):
        state.disabled = True

    btn1 = Button(
        "Toggle\n Buttons 2 & 3",
        handler=toggle_2_3,
        with_left_bracket=True,
        with_right_bracket=True,
        state=state1,
        bracket_type=BracketType.CURLY
    )
    
    btn2 = Button(
        "Disable\n Me",
        handler=lambda: disable_self(state2),
        with_left_bracket=True,
        with_right_bracket=True,
        state=state2,
        bracket_type=BracketType.PARENTHESIS
    )
    
    # Кнопка, меняющая свой текст
    btn3 = Button(
        "I am Button 3",
        with_left_bracket=True,
        with_right_bracket=True,
        state=state3
    )
    
    def btn3_handler():
        btn3.text = "Ouch! You clicked me!"
    
    btn3.handler = btn3_handler

    def reset_handler():
        state1.disabled = False
        state2.disabled = False
        state3.disabled = False
        btn3.text = "I am Button 3"

    btn_reset = Button(
        "Reset All",
        handler=reset_handler,
        with_left_bracket=True,
        with_right_bracket=True
    )

    layout = VerticalLayout([
        Label("=== PTWidgets Manual Test ===", style=WidgetStyle(base="fg:ansiyellow bold")),
        Label("This is a simple non-focusable label."),
        btn1,
        btn2,
        btn3,
        btn_reset,
        HorizontalLayout([
            Button("Left", with_left_bracket=True),
            Label("|", style=WidgetStyle(base="fg:gray")),
            Button("Right", with_right_bracket=True),
        ], padding=1),
        Label("Focusable label (rare, but possible):"),
        Label("[ Focus me! ]", state=WidgetState(focusable=True, disabled=False), with_left_bracket=True, with_right_bracket=True),
    ], padding=1)

    kb = KeyBindings()
    @kb.add("c-c")
    def _(event):
        event.app.exit()

    app = Application(
        layout=Layout(layout),
        key_bindings=kb,
        style=style,
        full_screen=True,
        mouse_support=True,
    )
    
    # Фокусируем первый фокусируемый элемент перед запуском
    app.pre_run_callables.append(lambda: layout.focus())
    
    app.run()

if __name__ == "__main__":
    run()
