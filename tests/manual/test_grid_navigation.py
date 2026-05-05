from prompt_toolkit.application import Application
from prompt_toolkit.layout import D, Layout, Window, FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings
import sys
import os
import asyncio

# Ensure src is in sys.path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from pt_widgets.layout.navigation import GridLayout, VerticalLayout, Focusable

class SelectableWindow(Focusable):
    def __init__(self, text, focusable=True, style=""):
        self.text = text
        self.style = style
        self.control = FormattedTextControl(self._get_text)
        self.window = Window(content=self.control, height=D(min=3), width=D(min=3), style=self._get_style)
        self.active = False
        self.focusable = focusable

    def _get_text(self):
        if self.active:
            return [("reverse", f"  [ {self.text} ]  ")]
        return f"    {self.text}    "

    def _get_style(self):
        if self.active:
            return "bg:#880000 #ffffff"
        return self.style

    def is_focusable(self) -> bool:
        return self.focusable

    def focus(self) -> None:
        from prompt_toolkit.application import get_app
        self.active = True
        try:
            get_app().layout.focus(self.window)
        except ValueError:
            # Might happen if layout is not yet fully initialized
            pass

    def unfocus(self) -> None:
        self.active = False

    def __pt_container__(self):
        return self.window

async def create_app():
    # Inner 2x2 grid
    inner_grid = GridLayout(
        children=[
            [SelectableWindow("Inner 0,0"), SelectableWindow("Inner 1,0")],
            [SelectableWindow("Inner 0,1"), SelectableWindow("Inner 1,1 uf", focusable=False)],
        ],
        style="bg:#222222",
        shift_point=False, # We want Shift+Arrows to bubble to outer
        padding_width=1,
        padding_height=1,
        cyclic_horizontal=True,
    )

    # Outer 3x3 grid
    outer_grid = GridLayout(
        children=[
            [SelectableWindow("Outer 0,0"), SelectableWindow("Outer 1,0"), SelectableWindow("Outer 2,0")],
            [SelectableWindow("Outer 0,1"), inner_grid,                   SelectableWindow("Outer 2,1")],
            [SelectableWindow("Outer 0,2 uf", focusable=False), SelectableWindow("Outer 1,2"), SelectableWindow("Outer 2,2")],
        ],
        style="bg:#000000",
        shift_point=True, # Catches Shift+Arrows
        padding_width=2,
        padding_height=1,
        cyclic_vertical=True,
    )

    # Wrap in a title and instructions
    help_text = (
        "GridLayout & shift_point test\n"
    )
    
    root_container = VerticalLayout(
        children=[
            Window(FormattedTextControl(help_text), height=1, style="bg:#444444"),
            outer_grid
        ],
        focusable=False
    )

    kb = KeyBindings()

    @kb.add("c-c")
    @kb.add("q")
    def _(event):
        event.app.exit()

    app = Application(
        layout=Layout(root_container),
        key_bindings=kb,
        full_screen=True,
    )

    return app, outer_grid


async def main():
    app, outer_grid = await create_app()

    # Delay focusing until app is starting
    app.pre_run_callables.append(lambda: outer_grid.focus())

    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
