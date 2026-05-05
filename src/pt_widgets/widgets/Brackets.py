from enum import Enum
from typing import Any

from prompt_toolkit.formatted_text import StyleAndTextTuples

from pt_widgets.layout import ContentGenerator, ExpandableControl


class ParenthesisSymbols(Enum):
    SINGLE = ("(", ")")
    TOP = ("⎛", "⎞")
    MIDDLE = ("⎜", "⎟")
    BOTTOM = ("⎝", "⎠")

class SquareSymbols(Enum):
    SINGLE = ("[", "]")
    TOP = ("⎡", "⎤")
    MIDDLE = ("⎢", "⎥")
    BOTTOM = ("⎣", "⎦")

class CurlySymbols(Enum):
    SINGLE = ("{", "}")
    TOP = ("⎧", "⎫")
    MIDDLE = ("⎪", "⎪")
    CENTER = ("⎨", "⎬")
    BOTTOM = ("⎩", "⎭")
    INTERMEDIATE = ("⎰", "⎱")


class BaseBracketContentGenerator(ContentGenerator):
    def __init__(self, is_right: bool):
        self.is_right = is_right
        self.width = 1
        self.height = 0
        self.style = ""

    def init(self, width: int, height: int, style: str) -> None:
        super().init(width, height, style)


class SimpleBracketContentGenerator(BaseBracketContentGenerator):
    symbols: Any

    def get_line(self, y: int) -> StyleAndTextTuples:
        match (self.height, y):
            case (1, _): char = self.symbols.SINGLE.value[self.is_right]
            case (_, 0): char = self.symbols.TOP.value[self.is_right]
            case (h, y) if y == h - 1: char = self.symbols.BOTTOM.value[self.is_right]
            case _: char = self.symbols.MIDDLE.value[self.is_right]
        return [(self.style, char)]


class ParenthesisContentGenerator(SimpleBracketContentGenerator):
    symbols = ParenthesisSymbols


class SquareBracketsContentGenerator(SimpleBracketContentGenerator):
    symbols = SquareSymbols


class CurlyBracketsContentGenerator(BaseBracketContentGenerator):
    def get_line(self, y: int) -> StyleAndTextTuples:
        mid = self.height // 2
        match (self.height, y):
            case (1, _): char = CurlySymbols.SINGLE.value[self.is_right]
            case (2, _): char = CurlySymbols.INTERMEDIATE.value[y - self.is_right]
            case (_, 0): char = CurlySymbols.TOP.value[self.is_right]
            case (h, y) if y == h - 1: char = CurlySymbols.BOTTOM.value[self.is_right]
            case (h, y) if h % 2 and y == mid: char = CurlySymbols.CENTER.value[self.is_right]
            case (h, y) if not h % 2 and y == mid: char = CurlySymbols.TOP.value[1 - self.is_right]
            case (h, y) if not h % 2 and y == mid - 1: char = CurlySymbols.BOTTOM.value[1 - self.is_right]
            case _: char = CurlySymbols.MIDDLE.value[self.is_right]
        return [(self.style, char)]
        


