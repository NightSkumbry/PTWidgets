from enum import Enum
from re import A
from typing import Callable, Union

from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import AnyDimension, Container, FormattedTextControl, HSplit, VSplit, VerticalAlign, Window

from pt_widgets.layout.containers import ConditionalContainer
from pt_widgets.widgets.brackets import BracketType, BracketsControl
from pt_widgets.widgets.common import BoolOrCallable, WidgetState, WidgetStyle, combine_styles, to_bool


class SwitchType(Enum):
    CHECK = (' ', '✓')
    CIRCLE = ('○', '●')
    SLIDING_CIRCLE = ('(○-)', '(-●)')
    TICK_IN_BOX = ('☐', '☑')
    CROSS_IN_BOX = ('☐', '☒')
    FULL_BLOCK = ('[□]', '[■]')
    HALF_BLOCK = ('[▌]', '[▐]')


class Switch:
    def __init__(
        self,
        text: AnyFormattedText = "",
        text_on: AnyFormattedText | None = None,
        handler: Callable[[bool], None] | None = None,
        switch_type: Union[SwitchType, tuple[str, str]] = SwitchType.SLIDING_CIRCLE,
        switch_before_text: bool = False,
        width: AnyDimension = None,
        height: AnyDimension = None,
        style: WidgetStyle | None = None,
        style_on: WidgetStyle | None = None,
        switch_style: WidgetStyle | None = None,
        switch_style_on: WidgetStyle | None = None,
        brackets_style: WidgetStyle | None = None,
        state: WidgetState | None = None,
        with_left_bracket: BoolOrCallable = True,
        with_right_bracket: BoolOrCallable = True,
        bracket_type: BracketType = BracketType.SQUARE,
    ) -> None:
        self.text = text
        self.text_on = text_on if text_on is not None else text
        self.handler = handler
        self.switch_type = switch_type
        self.switch_before_text = switch_before_text
        self.width = width
        self.height = height

        # Styles for text
        self.style_off = combine_styles(style, WidgetStyle(
            base="class:pt_widget.switch.text",
            focused="class:pt_widget.switch.text.focused",
            disabled="class:pt_widget.switch.text.disabled"
        ))
        self.style_on = combine_styles(style_on, WidgetStyle(
            base="class:pt_widget.switch.text.on",
            focused="class:pt_widget.switch.text.on.focused",
            disabled="class:pt_widget.switch.text.on.disabled"
        ))
        
        # Styles for toggle
        self.switch_style_off = combine_styles(switch_style, WidgetStyle(
            base="class:pt_widget.switch.toggle",
            focused="class:pt_widget.switch.toggle.focused",
            disabled="class:pt_widget.switch.toggle.disabled"
        ))
        self.switch_style_on = combine_styles(switch_style_on, WidgetStyle(
            base="class:pt_widget.switch.toggle.on",
            focused="class:pt_widget.switch.toggle.on.focused",
            disabled="class:pt_widget.switch.toggle.on.disabled"
        ))

        self.brackets_style = combine_styles(brackets_style, WidgetStyle(
            base="class:pt_widget.brackets",
            focused="class:pt_widget.brackets.focused",
            disabled="class:pt_widget.brackets.disabled"
        ))

        self._focused = False
        self.state = state if state is not None else WidgetState(focusable=True, disabled=False, checked=False)
        self.with_left_bracket = with_left_bracket
        self.with_right_bracket = with_right_bracket

        # Controls
        self.text_control = Window(
            content=FormattedTextControl(
                self._get_formatted_text,
                focusable=True,
                show_cursor=False,
                key_bindings=self._get_key_bindings(),
            ),
            dont_extend_height=True,
            dont_extend_width=True,
            style=self._get_text_style,
        )

        self.switch_control = HSplit([Window(
            content=FormattedTextControl(
                self._get_switch_text,
                focusable=False,
            ),
            # dont_extend_height=True,
            dont_extend_width=True,
            style=self._get_switch_style,
        )], align=VerticalAlign.CENTER,)

        def get_bracket_layout(is_right: bool):
            if not is_right:
                return VSplit([
                    Window(
                        BracketsControl(bracket_type.value(is_right=False)),
                        style=self.get_brackets_style,
                        dont_extend_width=True,
                    ),
                    Window(width=1, dont_extend_width=True, style=self.get_brackets_style)
                ])
            else:
                return VSplit([
                    Window(width=1, dont_extend_width=True, style=self.get_brackets_style),
                    Window(
                        BracketsControl(bracket_type.value(is_right=True)),
                        style=self.get_brackets_style,
                        dont_extend_width=True,
                    )
                ])

        inner_content = [self.text_control]
        spacer = Window(width=1, dont_extend_width=True, style=self._get_switch_style)
        
        if self.switch_before_text:
            inner_content = [self.switch_control, spacer] + inner_content
        else:
            inner_content = inner_content + [spacer, self.switch_control]

        self.layout = VSplit(
            [
                ConditionalContainer(
                    content=get_bracket_layout(False),
                    filter=Condition(self._with_left_bracket),
                ),
                VSplit(inner_content),
                ConditionalContainer(
                    content=get_bracket_layout(True),
                    filter=Condition(self._with_right_bracket),
                ),
            ],
            width=width,
            height=height,
            
        )

    # Focusable
    def is_focusable(self) -> bool:
        return self.state.focusable and not self.state.disabled

    def focus(self) -> None:
        self._focused = True
        get_app().layout.focus(self.text_control)

    def unfocus(self) -> None:
        self._focused = False
        
    # MagicContainer
    def __pt_container__(self) -> Container:
        return self.layout

    def _get_formatted_text(self) -> AnyFormattedText:
        return self.text_on if self.state.checked else self.text

    def _get_switch_text(self) -> str:
        vals = self.switch_type.value if isinstance(self.switch_type, SwitchType) else self.switch_type
        return vals[1] if self.state.checked else vals[0]

    def _get_text_style(self) -> str:
        s = self.style_on if self.state.checked else self.style_off
        if self._focused: return s.focused
        if self.state.disabled: return s.disabled
        return s.base

    def _get_switch_style(self) -> str:
        s = self.switch_style_on if self.state.checked else self.switch_style_off
        if self._focused: return s.focused
        if self.state.disabled: return s.disabled
        return s.base

    def get_brackets_style(self) -> str:
        if self._focused: return self.brackets_style.focused
        if self.state.disabled: return self.brackets_style.disabled
        return self.brackets_style.base

    def _get_key_bindings(self) -> KeyBindings:
        kb = KeyBindings()
        @kb.add("enter", filter=Condition(lambda: not self.state.disabled))
        def _(event):
            self.state.checked = not self.state.checked
            if self.handler:
                self.handler(self.state.checked)
        return kb

    def _with_left_bracket(self) -> bool:
        return to_bool(self.with_left_bracket)

    def _with_right_bracket(self) -> bool:
        return to_bool(self.with_right_bracket)
