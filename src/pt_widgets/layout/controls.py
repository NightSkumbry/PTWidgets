
from abc import ABC, abstractmethod
from prompt_toolkit.layout.controls import UIControl, UIContent, StyleAndTextTuples, GetLinePrefixCallable
from prompt_toolkit.formatted_text import to_formatted_text


class ContentGenerator(ABC):
    def init(self, width: int, height: int, style: str) -> None:
        self.width = width
        self.height = height
        self.style = style
    
    @abstractmethod
    def get_line(self, y: int) -> StyleAndTextTuples:
        pass


from prompt_toolkit.key_binding import KeyBindingsBase

class ExpandableControl(UIControl):
    def __init__(
        self,
        content_generator: ContentGenerator,
        style: str = "",
        min_width: int = 1,
        min_height: int = 1,
        key_bindings: KeyBindingsBase | None = None,
        focusable: bool = False,
    ):
        self.content_generator = content_generator
        self.min_width = min_width
        self.min_height = min_height
        self.style = style
        self.key_bindings = key_bindings
        self._focusable = focusable
    

    def create_content(self, width: int, height: int) -> UIContent:
        self.content_generator.init(width, height, self.style)

        return UIContent(
            get_line=self.content_generator.get_line,
            line_count=height,
            show_cursor=False
        )

    def is_focusable(self) -> bool:
        return self._focusable

    def get_key_bindings(self) -> KeyBindingsBase | None:
        return self.key_bindings

    def preferred_width(self, max_available_width: int) -> int:
        return self.min_width
    
    def preferred_height(
        self,
        width: int,
        max_available_height: int,
        wrap_lines: bool,
        get_line_prefix: GetLinePrefixCallable | None,
    ) -> int | None:
        return self.min_height

