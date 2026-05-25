
"""
sliders:

A.
┣━━━●┈┈┈┈┈┈┨

┯
┊
┊
●
┃
┃
┻

B.
┠━━━╉┈┈┈┈┈┈┨

┯
┊
┊
╈
┃
┃
┻

С.
◀═══◈──────▶

▲
│
│
◈
║
║
▼

progress bars:
Пока не реализовывай, ибо они будут требовать асинхронной отрисовки, что я ещё не делал.

A.
Для этого используются символы частичных блоков (`▏▎▍▌▋▊▉█`), что позволяет делать прогресс попиксельно плавным даже в текстовом режиме.
[██████▊   ] 68%

B.
[●●●●○○○○○○] 40%

С.
[■■■■■■····]

ScrollBars:

A.
Регулировка при помощи оттенков цвета (белый (где надо) + серый)
◀███████▶

▲
█
█
█
▼

B.
├────══════────┤

┬
│
║
║
│
┴

"""

from enum import Enum
from typing import Callable

from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import AnyFormattedText, StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import AnyDimension, Container, FormattedTextControl, Window
from prompt_toolkit.layout.dimension import Dimension

from pt_widgets.widgets.common import WidgetState, WidgetStyle, combine_styles
from pt_widgets.layout.controls import ContentGenerator, ExpandableControl


class FillMode(Enum):
    BEFORE = "before"
    AFTER = "after"
    NONE = "none"


class Slider(ContentGenerator):
    def __init__(
        self,
        value: float = 0,
        min_val: float = 0,
        max_val: float = 100,
        step: float = 1,
        width: AnyDimension = None,
        height: AnyDimension = None,
        fill_mode: FillMode = FillMode.BEFORE,
        on_change: Callable[[float], None] | None = None,
        style: WidgetStyle | None = None,
        bar_style: WidgetStyle | None = None,
        fill_style: WidgetStyle | None = None,
        track_style: WidgetStyle | None = None,
        left_edge_style: WidgetStyle | None = None,
        right_edge_style: WidgetStyle | None = None,
        state: WidgetState | None = None,
        track_char: str = "┈",
        bar_char: str = "●",
        fill_char: str = "━",
        left_edge_char: str = "",
        right_edge_char: str = "",
    ) -> None:
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.width = width
        self.height = height
        self.fill_mode = fill_mode
        self.on_change = on_change
        
        self.track_char = track_char
        self.bar_char = bar_char
        self.fill_char = fill_char
        self.left_edge_char = left_edge_char
        self.right_edge_char = right_edge_char

        # Base style for the whole window
        self.style = combine_styles(style, WidgetStyle(
            base="class:pt_widget.slider",
            focused="class:pt_widget.slider.focused",
            disabled="class:pt_widget.slider.disabled"
        ))
        
        # Specific styles for parts
        self.bar_style = combine_styles(bar_style, WidgetStyle(
            base="class:pt_widget.slider.bar",
            focused="class:pt_widget.slider.bar.focused",
            disabled="class:pt_widget.slider.bar.disabled"
        ))
        self.fill_style = combine_styles(fill_style, WidgetStyle(
            base="class:pt_widget.slider.fill",
            focused="class:pt_widget.slider.fill.focused",
            disabled="class:pt_widget.slider.fill.disabled"
        ))
        self.track_style = combine_styles(track_style, WidgetStyle(
            base="class:pt_widget.slider.track",
            focused="class:pt_widget.slider.track.focused",
            disabled="class:pt_widget.slider.track.disabled"
        ))
        self.left_edge_style = combine_styles(left_edge_style, WidgetStyle(
            base="class:pt_widget.slider.edge",
            focused="class:pt_widget.slider.edge.focused",
            disabled="class:pt_widget.slider.edge.disabled"
        ))
        self.right_edge_style = combine_styles(right_edge_style, WidgetStyle(
            base="class:pt_widget.slider.edge",
            focused="class:pt_widget.slider.edge.focused",
            disabled="class:pt_widget.slider.edge.disabled"
        ))
        
        self._focused = False
        self.state = state if state is not None else WidgetState(focusable=True, disabled=False)

        self._current_width = 20
        self.control = ExpandableControl(
            self,
            key_bindings=self._get_key_bindings(),
            focusable=True,
        )
        
        win_width = width
        if win_width is None:
            win_width = Dimension(min=1, preferred=20)
            
        self.window = Window(
            content=self.control,
            width=win_width,
            height=height,
            dont_extend_height=True,
            style=self._get_style,
        )

    def init(self, width: int, height: int, style: str) -> None:
        self._current_width = width

    def get_line(self, y: int) -> StyleAndTextTuples:
        if y > 0:
            return []
            
        width = self._current_width
        
        # Calculate available content width
        left_len = len(self.left_edge_char)
        right_len = len(self.right_edge_char)
        content_width = width - left_len - right_len
        
        if content_width < 1:
            # Fallback for very small widths: just show edges or nothing
            result = []
            if left_len > 0 and width >= left_len:
                result.append((self._get_part_style(self.left_edge_style), self.left_edge_char))
            if right_len > 0 and width >= left_len + right_len:
                result.append((self._get_part_style(self.right_edge_style), self.right_edge_char))
            return result
            
        range_val = self.max_val - self.min_val
        if range_val == 0:
            percent = 0
        else:
            percent = (self.value - self.min_val) / range_val
        
        # Clamp percent and calculate position
        percent = max(0, min(1, percent))
        slots = content_width - 1
        bar_pos = int(round(percent * slots))
        
        result = []
        
        if self.left_edge_char:
            result.append((self._get_part_style(self.left_edge_style), self.left_edge_char))

        for i in range(content_width):
            if i == bar_pos:
                result.append((self._get_part_style(self.bar_style), self.bar_char))
            elif i < bar_pos:
                if self.fill_mode == FillMode.BEFORE:
                    result.append((self._get_part_style(self.fill_style), self.fill_char))
                else:
                    result.append((self._get_part_style(self.track_style), self.track_char))
            else: # i > bar_pos
                if self.fill_mode == FillMode.AFTER:
                    result.append((self._get_part_style(self.fill_style), self.fill_char))
                else:
                    result.append((self._get_part_style(self.track_style), self.track_char))

        if self.right_edge_char:
            result.append((self._get_part_style(self.right_edge_style), self.right_edge_char))
            
        return result

    def _get_part_style(self, style_obj: WidgetStyle) -> str:
        if self.state.disabled:
            return style_obj.disabled
        if self._focused:
            return style_obj.focused
        return style_obj.base

    def _get_style(self) -> str:
        if self.state.disabled:
            return self.style.disabled
        if self._focused:
            return self.style.focused
        return self.style.base

    def _get_key_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("left")
        def _(event):
            self.value = max(self.min_val, self.value - self.step)
            if self.on_change:
                self.on_change(self.value)

        @kb.add("right")
        def _(event):
            self.value = min(self.max_val, self.value + self.step)
            if self.on_change:
                self.on_change(self.value)

        return kb

    # Focusable
    def is_focusable(self) -> bool:
        return self.state.focusable and not self.state.disabled

    def focus(self) -> None:
        self._focused = True
        get_app().layout.focus(self.window)

    def unfocus(self) -> None:
        self._focused = False

    # MagicContainer
    def __pt_container__(self) -> Container:
        return self.window



class SliderA(Slider):
    def __init__(
        self,
        value: float = 0,
        min_val: float = 0,
        max_val: float = 100,
        step: float = 1,
        width: AnyDimension = None,
        height: AnyDimension = None,
        fill_mode: FillMode = FillMode.BEFORE,
        on_change: Callable[[float], None] | None = None,
        style: WidgetStyle | None = None,
        bar_style: WidgetStyle | None = None,
        fill_style: WidgetStyle | None = None,
        track_style: WidgetStyle | None = None,
        left_edge_style: WidgetStyle | None = None,
        right_edge_style: WidgetStyle | None = None,
        state: WidgetState | None = None,
    ) -> None:
        defaults = {
            "left_edge_char": "┣",
            "fill_char": "━",
            "bar_char": "●",
            "track_char": "┈",
            "right_edge_char": "┨",
        }
        super().__init__(
            value=value,
            min_val=min_val,
            max_val=max_val,
            step=step,
            width=width,
            height=height,
            fill_mode=fill_mode,
            on_change=on_change,
            style=style,
            bar_style=bar_style,
            fill_style=fill_style,
            track_style=track_style,
            left_edge_style=left_edge_style,
            right_edge_style=right_edge_style,
            state=state,
            **defaults,
        )


class SliderB(Slider):
    def __init__(
        self,
        value: float = 0,
        min_val: float = 0,
        max_val: float = 100,
        step: float = 1,
        width: AnyDimension = None,
        height: AnyDimension = None,
        fill_mode: FillMode = FillMode.BEFORE,
        on_change: Callable[[float], None] | None = None,
        style: WidgetStyle | None = None,
        bar_style: WidgetStyle | None = None,
        fill_style: WidgetStyle | None = None,
        track_style: WidgetStyle | None = None,
        left_edge_style: WidgetStyle | None = None,
        right_edge_style: WidgetStyle | None = None,
        state: WidgetState | None = None,
    ) -> None:
        defaults = {
            "left_edge_char": "┠",
            "fill_char": "━",
            "bar_char": "╉",
            "track_char": "┈",
            "right_edge_char": "┨",
        }
        super().__init__(
            value=value,
            min_val=min_val,
            max_val=max_val,
            step=step,
            width=width,
            height=height,
            fill_mode=fill_mode,
            on_change=on_change,
            style=style,
            bar_style=bar_style,
            fill_style=fill_style,
            track_style=track_style,
            left_edge_style=left_edge_style,
            right_edge_style=right_edge_style,
            state=state,
            **defaults,
        )


class SliderC(Slider):
    def __init__(
        self,
        value: float = 0,
        min_val: float = 0,
        max_val: float = 100,
        step: float = 1,
        width: AnyDimension = None,
        height: AnyDimension = None,
        fill_mode: FillMode = FillMode.BEFORE,
        on_change: Callable[[float], None] | None = None,
        style: WidgetStyle | None = None,
        bar_style: WidgetStyle | None = None,
        fill_style: WidgetStyle | None = None,
        track_style: WidgetStyle | None = None,
        left_edge_style: WidgetStyle | None = None,
        right_edge_style: WidgetStyle | None = None,
        state: WidgetState | None = None,
    ) -> None:
        defaults = {
            "left_edge_char": "◀",
            "fill_char": "═",
            "bar_char": "◈",
            "track_char": "─",
            "right_edge_char": "▶",
        }
        super().__init__(
            value=value,
            min_val=min_val,
            max_val=max_val,
            step=step,
            width=width,
            height=height,
            fill_mode=fill_mode,
            on_change=on_change,
            style=style,
            bar_style=bar_style,
            fill_style=fill_style,
            track_style=track_style,
            left_edge_style=left_edge_style,
            right_edge_style=right_edge_style,
            state=state,
            **defaults,
        )


class Orientation(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Scrollbar:
    def __init__(
        self,
        orientation: Orientation = Orientation.VERTICAL,
        width: AnyDimension = None,
        height: AnyDimension = None,
        style: WidgetStyle | None = None,
        bar_style: WidgetStyle | None = None,
        track_style: WidgetStyle | None = None,
        edge_style: WidgetStyle | None = None,
        track_char: str | None = None,
        bar_char: str = "█",
        top_edge_char: str = "",
        bottom_edge_char: str = "",
        left_edge_char: str = "",
        right_edge_char: str = "",
    ) -> None:
        self.orientation = orientation
        self.width = width
        self.height = height
        
        if track_char is None:
            self.track_char = "│" if orientation == Orientation.VERTICAL else "━"
        else:
            self.track_char = track_char
            
        self.bar_char = bar_char
        self.top_edge_char = top_edge_char
        self.bottom_edge_char = bottom_edge_char
        self.left_edge_char = left_edge_char
        self.right_edge_char = right_edge_char

        self.style = combine_styles(style, WidgetStyle(
            base="class:pt_widget.scrollbar",
            disabled="class:pt_widget.scrollbar.disabled"
        ))
        
        self.bar_style = combine_styles(bar_style, WidgetStyle(
            base="class:pt_widget.scrollbar.bar",
            focused="class:pt_widget.scrollbar.bar.focused",
            disabled="class:pt_widget.scrollbar.bar.disabled"
        ))
        self.track_style = combine_styles(track_style, WidgetStyle(
            base="class:pt_widget.scrollbar.track",
            focused="class:pt_widget.scrollbar.track.focused",
            disabled="class:pt_widget.scrollbar.track.disabled"
        ))
        self.edge_style = combine_styles(edge_style, WidgetStyle(
            base="class:pt_widget.scrollbar.edge",
            focused="class:pt_widget.scrollbar.edge.focused",
            disabled="class:pt_widget.scrollbar.edge.disabled"
        ))

        self.position = 0
        self.total_items = 0
        self.visible_items = 0
        self.current_length = 0
        self._focused = False

        self.control = FormattedTextControl(
            self._get_formatted_text,
            focusable=False,
            show_cursor=False,
        )
        self.window = Window(
            content=self.control,
            width=width,
            height=height,
            style=self._get_style,
        )

    def update_state(self, position: int, total_items: int, visible_items: int, length: int | None = None) -> None:
        self.position = position
        self.total_items = total_items
        self.visible_items = visible_items
        if length is not None:
            self.current_length = length

    def _get_part_style(self, style_obj: WidgetStyle) -> str:
        if self._focused:
            return style_obj.focused
        return style_obj.base

    def _get_formatted_text(self) -> AnyFormattedText:
        if self.total_items <= self.visible_items or self.total_items == 0:
            return ""

        length = self.current_length
        if length == 0:
            if self.orientation == Orientation.VERTICAL:
                if isinstance(self.height, int):
                    length = self.height
            else: # HORIZONTAL
                if isinstance(self.width, int):
                    length = self.width
        
        if length == 0:
            return ""

        if self.orientation == Orientation.VERTICAL:
            start_edge = self.top_edge_char
            end_edge = self.bottom_edge_char
        else:
            start_edge = self.left_edge_char
            end_edge = self.right_edge_char
            
        content_length = length - len(start_edge) - len(end_edge)
        if content_length < 1:
            return ""

        bar_len = max(1, round(content_length * (self.visible_items / self.total_items)))
        
        total_scroll = max(1, self.total_items - self.visible_items)
        track_space = max(1, content_length - bar_len)
        exact_pos = (self.position / total_scroll) * track_space
        
        base_pos = int(exact_pos)
        frac = exact_pos - base_pos
        
        current_bar_len = bar_len
        if frac > 0.3 and (base_pos + bar_len < content_length):
            current_bar_len += 1
            
        result = []
        
        if start_edge:
            result.append((self._get_part_style(self.edge_style), start_edge))
            if self.orientation == Orientation.VERTICAL:
                result.append(("", "\n"))
        
        for i in range(content_length):
            if base_pos <= i < base_pos + current_bar_len:
                result.append((self._get_part_style(self.bar_style), self.bar_char))
            else:
                result.append((self._get_part_style(self.track_style), self.track_char))
            
            if self.orientation == Orientation.VERTICAL and i < content_length - 1:
                result.append(("", "\n"))
        
        if end_edge:
            if self.orientation == Orientation.VERTICAL:
                result.append(("", "\n"))
            result.append((self._get_part_style(self.edge_style), end_edge))
            
        return result

    def _get_style(self) -> str:
        if self._focused:
            return self.style.focused
        return self.style.base

    # MagicContainer
    def __pt_container__(self) -> Container:
        return self.window


class ScrollbarA(Scrollbar):
    def __init__(
        self,
        orientation: Orientation = Orientation.VERTICAL,
        width: AnyDimension = None,
        height: AnyDimension = None,
        style: WidgetStyle | None = None,
        bar_style: WidgetStyle | None = None,
        track_style: WidgetStyle | None = None,
        edge_style: WidgetStyle | None = None,
    ) -> None:
        if orientation == Orientation.VERTICAL:
            defaults = {
                "top_edge_char": "▲",
                "bottom_edge_char": "▼",
                "bar_char": "█",
                "track_char": " ",
            }
        else:
            defaults = {
                "left_edge_char": "◀",
                "right_edge_char": "▶",
                "bar_char": "█",
                "track_char": " ",
            }
        super().__init__(
            orientation=orientation,
            width=width,
            height=height,
            style=style,
            bar_style=bar_style,
            track_style=track_style,
            edge_style=edge_style,
            **defaults,
        )


class ScrollbarB(Scrollbar):
    def __init__(
        self,
        orientation: Orientation = Orientation.VERTICAL,
        width: AnyDimension = None,
        height: AnyDimension = None,
        style: WidgetStyle | None = None,
        bar_style: WidgetStyle | None = None,
        track_style: WidgetStyle | None = None,
        edge_style: WidgetStyle | None = None,
    ) -> None:
        if orientation == Orientation.VERTICAL:
            defaults = {
                "top_edge_char": "┬",
                "bottom_edge_char": "┴",
                "bar_char": "║",
                "track_char": "│",
            }
        else:
            defaults = {
                "left_edge_char": "├",
                "right_edge_char": "┤",
                "bar_char": "═",
                "track_char": "─",
            }
        super().__init__(
            orientation=orientation,
            width=width,
            height=height,
            style=style,
            bar_style=bar_style,
            track_style=track_style,
            edge_style=edge_style,
            **defaults,
        )
