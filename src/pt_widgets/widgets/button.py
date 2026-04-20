from typing import Callable

from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import AnyDimension, Container, FormattedTextControl, Window


class Button:
    def __init__(
        self,
        text: str,
        handler: Callable[[], None] | None = None,
        width: AnyDimension = None,
        height: AnyDimension = None,
        style: str = "class:pt_widget.button",
        focused_style: str = "class:pt_widget.button.focused",
    ) -> None:
        self.text = text
        self.handler = handler
        self.width = width
        self.height = height
        self.style = style
        self.focused_style = focused_style
        self._focused = False

        self.control = Window(
            content=FormattedTextControl(
                self._get_formatted_text,
                key_bindings=self._get_key_bindings(),
                focusable=True,
            ),
            width=width,
            height=height,
            style=self._get_style,
        )
    
    # Focusable
    def is_focusable(self) -> bool:
        return True

    def focus(self) -> None:
        self._focused = True
        get_app().layout.focus(self.control)

    def unfocus(self) -> None:
        self._focused = False
    
    # MagicContainer
    def __pt_container__(self) -> Container:
        return self.control

    def _get_formatted_text(self):
        pass

    def _get_style(self) -> str:
        if self._focused:
            return self.focused_style
        return self.style

    def _get_key_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("enter")
        @kb.add(" ")
        def _(event):
            if self.handler:
                self.handler()

        return kb


