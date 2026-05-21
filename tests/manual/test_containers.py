from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, DynamicContainer
from prompt_toolkit.filters import Condition

from pt_widgets.widgets.button import Button
from pt_widgets.widgets.label import Label
from pt_widgets.widgets.switch import Switch, SwitchState
from pt_widgets.layout.navigation import GridLayout, VerticalLayout
from pt_widgets.layout.containers import ConditionalContainer
from pt_widgets.widgets.common import WidgetState, WidgetStyle
from shared_styles import get_shared_style

def run():
    # State for toggling
    show_secret_state = SwitchState(focusable=True, disabled=False, checked=False)
    switch_content_state = SwitchState(focusable=True, disabled=False, checked=False)
    
    # State for DynamicContainer
    dynamic_counter = [0]
    
    def increment_dynamic():
        dynamic_counter[0] += 1
        
    but = Button(
        f"Dynamic Button: {dynamic_counter[0]}",
        handler=increment_dynamic,
        style=WidgetStyle(base="fg:ansicyan")
    )
    
    def get_dynamic_content():
        # Returning a Button makes it focusable and interactive
        but.text = f"Dynamic Button: {dynamic_counter[0]}"
        return but

    # Toggle switches
    secret_toggle = Switch("Show Focusable Secret", state=show_secret_state)
    content_toggle = Switch("Switch Between Buttons", state=switch_content_state)

    # ConditionalContainer: Show/Hide focusable content
    secret_button = ConditionalContainer(
        content=Button("!!! SECRET BUTTON !!!", handler=lambda: None, style=WidgetStyle(base="fg:ansired bold")),
        filter=Condition(lambda: show_secret_state.checked)
    )

    # ConditionalContainer: Alternative Focusable Content
    alternative_demo = ConditionalContainer(
        content=Button("Primary Button (A)", handler=lambda: None, style=WidgetStyle(base="fg:ansigreen")),
        filter=Condition(lambda: not switch_content_state.checked),
        alternative_content=Button("Alternative Button (B)", handler=lambda: None, style=WidgetStyle(base="fg:ansiblue"))
    )

    # DynamicContainer
    dynamic_demo = DynamicContainer(get_dynamic_content)

    # GridLayout demo with multiple buttons
    grid_demo = GridLayout([
        [Button("G 1,1"), Button("G 1,2")],
        [Button("G 2,1"), Button("G 2,2")],
        [Button("G 3,1"), Button("G 3,2")]
    ], padding_width=2, padding_height=1, padding_char='.', padding_style="fg:ansigray")

    layout = VerticalLayout([
        Label("=== PTWidgets Containers Focus Test ===", style=WidgetStyle(base="fg:ansiyellow bold")),
        
        Label("1. Conditional (Show/Hide Button):"),
        secret_toggle,
        secret_button,

        Label("2. Conditional (Swap Buttons):"),
        content_toggle,
        alternative_demo,

        Label("3. Dynamic (Focusable Content):"),
        dynamic_demo,

        Label("4. GridLayout (Button Matrix):"),
        grid_demo,

        Label("[ Arrows: Navigate | Enter: Action/Toggle | Ctrl+C: Exit ]", 
              style=WidgetStyle(base="fg:ansigray italic")),
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
    
    app.pre_run_callables.append(lambda: layout.focus())
    
    app.run()

if __name__ == "__main__":
    run()
