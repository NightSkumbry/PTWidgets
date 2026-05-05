from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.styles import Style
from pt_widgets.widgets.button import Button
from pt_widgets.widgets.label import Label
from pt_widgets.widgets.switch import Switch, SwitchType
from pt_widgets.layout.navigation import VerticalLayout, HorizontalLayout
from pt_widgets.widgets.common import WidgetState, WidgetStyle

def run():
    # Определяем стили для виджетов
    style = Style.from_dict({
        # Кнопки
        "pt_widget.button": "fg:ansiblue bg:ansigray",
        "pt_widget.button.focused": "fg:ansiyellow bg:ansiblue",
        "pt_widget.button.disabled": "fg:ansigray bg:ansiblack",
        # Метки
        "pt_widget.label": "fg:ansiwhite",
        "pt_widget.label.focused": "fg:ansiblack bg:ansiwhite",
        "pt_widget.label.disabled": "fg:ansigray",
        # Переключатели (Текст)
        "pt_widget.switch.text": "fg:ansiwhite",
        "pt_widget.switch.text.focused": "fg:ansiblack bg:ansiyellow",
        "pt_widget.switch.text.disabled": "fg:ansigray",
        "pt_widget.switch.text.on": "fg:ansigreen bold",
        "pt_widget.switch.text.on.focused": "fg:ansiyellow bg:ansigreen",
        "pt_widget.switch.text.on.disabled": "fg:ansidarkgreen nobold",
        # Переключатели (Тумблер)
        "pt_widget.switch.toggle": "fg:ansired",
        "pt_widget.switch.toggle.focused": "fg:ansired bg:ansiyellow",
        "pt_widget.switch.toggle.disabled": "fg:ansidarkred",
        "pt_widget.switch.toggle.on": "fg:ansibrightgreen",
        "pt_widget.switch.toggle.on.focused": "fg:ansibrightgreen bg:ansiyellow",
        "pt_widget.switch.toggle.on.disabled": "fg:ansigreen",
        # Скобки
        "pt_widget.brackets": "fg:ansicyan",
        "pt_widget.brackets.focused": "fg:ansiwhite bg:ansiblue",
        "pt_widget.brackets.disabled": "fg:ansicyan",
    })

    # Состояния для кнопок, чтобы они могли отключать друг друга
    state1 = WidgetState(focusable=True, disabled=False)
    state2 = WidgetState(focusable=True, disabled=False)
    state3 = WidgetState(focusable=True, disabled=False)
    
    state4 = WidgetState(True, False, checked=True)

    def toggle_2_3():
        state2.disabled = not state2.disabled
        state3.disabled = not state3.disabled
        state4.disabled = not state4.disabled
        

    btn1 = Button(
        "Toggle Buttons 2 & 3",
        handler=toggle_2_3,
        with_left_bracket=True,
        with_right_bracket=True,
        state=state1
    )
    
    btn2 = Button(
        "Disable Me",
        handler=lambda: setattr(state2, 'disabled', True),
        with_left_bracket=True,
        with_right_bracket=True,
        state=state2
    )
    
    btn3 = Button(
        "I am Button 3",
        handler=lambda: setattr(btn3, 'text', "Ouch! You clicked me!"),
        with_left_bracket=True,
        with_right_bracket=True,
        state=state3
    )
    
    def reset_handler():
        setattr(state1, 'disabled', False)
        setattr(state2, 'disabled', False)
        setattr(state3, 'disabled', False)
        setattr(btn3, 'text', "I am Button 3")

    btn_reset = Button(
        "Reset All",
        handler=reset_handler,
        with_left_bracket=True,
        with_right_bracket=True
    )

    layout = VerticalLayout([
        Label("=== PTWidgets Manual Test ===", style=WidgetStyle(base="fg:ansiyellow bold")),
        
        Label("Buttons:"),
        HorizontalLayout([btn1, btn2, btn3, btn_reset], padding=1),

        Label("Switches:"),
        Switch("Dark Mode", state=state4),
        Switch("Notifications", switch_type=SwitchType.TICK_IN_BOX, switch_before_text=True),
        Switch("Feature X", text_on="Feature X (ENABLED)", switch_type=SwitchType.BOX),
        
        HorizontalLayout([
            Label("Volume:"),
            Switch("Mute", switch_type=("( )", "(#)"), with_left_bracket=False, with_right_bracket=False),
        ], padding=1),

        Label("Focusable label:"),
        Label("[ Focus me! ]", state=WidgetState(focusable=True, disabled=False)),
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
