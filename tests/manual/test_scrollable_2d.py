
import os
import sys

# Add src to sys.path to allow importing pt_widgets without installation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

from pt_widgets.layout.scrollable import Scrollable
from pt_widgets.layout.navigation import GridLayout, VerticalLayout
from pt_widgets.widgets.button import Button
from pt_widgets.widgets.label import Label
from shared_styles import get_shared_style

def main():
    # Create a 20x20 grid of buttons
    buttons = []
    for y in range(20):
        row = []
        for x in range(20):
            row.append(Button(f"B{x},{y}", width=10))
        buttons.append(row)
    
    grid = GridLayout(buttons)
    
    scrollable = Scrollable(
        grid,
        width=40,
        height=10,
        scroll_vertical=True,
        scroll_horizontal=True,
        show_scrollbar_v=True,
        show_scrollbar_h=True,
    )
    
    root = VerticalLayout([
        Label("=== Scrollable 2D Test ==="),
        Label("Use arrow keys to navigate and scroll."),
        scrollable,
        Label("Press 'q' to exit.")
    ])

    kb = KeyBindings()
    @kb.add("c-c")
    @kb.add("q")
    def _(event):
        event.app.exit()

    app = Application(
        layout=Layout(root),
        key_bindings=kb,
        style=get_shared_style(),
        full_screen=True,
        mouse_support=True,
    )
    
    # Initial focus
    app.pre_run_callables.append(lambda: scrollable.focus())
    
    app.run()

if __name__ == "__main__":
    main()
