from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from pt_widgets.widgets.button import Button
from pt_widgets.widgets.label import Label
from pt_widgets.widgets.switch import Switch, SwitchType
from pt_widgets.layout.navigation import VerticalLayout, HorizontalLayout
from pt_widgets.widgets.common import WidgetState, WidgetStyle
from shared_styles import get_shared_style

def run():
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
        style=get_shared_style(),
        full_screen=True,
        mouse_support=True,
    )
    
    # Фокусируем первый фокусируемый элемент перед запуском
    app.pre_run_callables.append(lambda: layout.focus())
    
    app.run()

if __name__ == "__main__":
    run()
