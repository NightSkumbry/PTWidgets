from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, Window, FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings
import sys
import os
import asyncio

# Add src to sys.path to import pt_widgets
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from pt_widgets.layout.navigation import HorizontalLayout, VerticalLayout, Focusable

class SelectableWindow(Focusable):
    def __init__(self, text, style="", focusable=True):
        self.text = text
        self.style = style
        self.control = FormattedTextControl(self._get_text)
        self.window = Window(content=self.control, height=1, style=self._get_style)
        self.active = False
        self.focusable=focusable

    def _get_text(self):
        if self.active:
            return [("reverse", f"> {self.text} <")]
        return f"  {self.text}  "

    def _get_style(self):
        if self.active:
            return "class:focused"
        return self.style

    def is_focusable(self) -> bool:
        return self.focusable

    def focus(self) -> None:
        from prompt_toolkit.application import get_app
        self.active = True
        get_app().layout.focus(self.window)
    
    def unfocus(self) -> None:
        self.active = False

    def __pt_container__(self):
        return self.window

async def create_app():
    # Outer layout with shift_point=True
    # It contains some items and a sub-menu
    
    sub_menu = HorizontalLayout(
        children=[
            SelectableWindow("Sub Item 1"),
            SelectableWindow("Sub Item 2"),
            SelectableWindow("vew", focusable=False),
            SelectableWindow("Sub Item 3"),
        ],
        style="bg:#444400",
        shift_point=False, # Sub menu itself doesn't catch shift-up/down
        cyclic=True,
    )

    root_layout = HorizontalLayout(
        children=[
            SelectableWindow("cwj", focusable=False),
            SelectableWindow("Outer Item 1"),
            sub_menu,
            SelectableWindow("Outer Item 2"),
            SelectableWindow("vew", focusable=False),
            SelectableWindow("Outer Item 3"),
            SelectableWindow("vew", focusable=False),
        ],
        padding=1,
        shift_point=True, # Root catches shift-up/down to move between its children
    )

    kb = KeyBindings()

    @kb.add("c-c")
    @kb.add("q")
    def _(event):
        event.app.exit()

    app = Application(
        layout=Layout(root_layout),
        key_bindings=kb,
        full_screen=True,
    )
    
    return app, root_layout


async def main():
    app, root_layout = await create_app()
    
    app.pre_run_callables.append(lambda: root_layout.focus())
    
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
    
