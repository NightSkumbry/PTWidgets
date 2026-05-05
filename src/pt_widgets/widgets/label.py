from prompt_toolkit.application import get_app
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.layout import AnyDimension, Container, FormattedTextControl, VSplit, Window

from pt_widgets.layout.containers import ConditionalContainer
from pt_widgets.widgets.brackets import BracketType, BracketsControl
from pt_widgets.widgets.common import BoolOrCallable, WidgetState, WidgetStyle, combine_styles, to_bool


class Label:
    def __init__(
        self,
        text: AnyFormattedText = "",
        width: AnyDimension = None,
        height: AnyDimension = None,
        style: WidgetStyle | None = None,
        brackets_style: WidgetStyle | None = None,
        state: WidgetState | None = None,
        with_left_bracket: BoolOrCallable = False,
        with_right_bracket: BoolOrCallable = False,
        bracket_type: BracketType = BracketType.SQUARE,
    ) -> None:
        self.text = text
        self.width = width
        self.height = height
        self.style = combine_styles(style, WidgetStyle(
            base="class:pt_widget.label",
            focused="class:pt_widget.label.focused",
            disabled="class:pt_widget.label.disabled"
        ))
        self.brackets_style = combine_styles(brackets_style, WidgetStyle(
            base="class:pt_widget.brackets",
            focused="class:pt_widget.brackets.focused",
            disabled="class:pt_widget.brackets.disabled"
        ))
        self._focused = False
        self.state = state if state is not None else WidgetState(focusable=False, disabled=False)
        self.with_left_bracket = with_left_bracket
        self.with_right_bracket = with_right_bracket

        self.control = Window(
            content=FormattedTextControl(
                self._get_formatted_text,
                focusable=Condition(lambda: self.state.focusable),
                show_cursor=False,
            ),
            dont_extend_height=True,
            dont_extend_width=True,
            style=self._get_style,
        )
        
        self.layout = VSplit(
            [
                ConditionalContainer(
                    content=VSplit([
                        Window(
                            BracketsControl(
                                bracket_type.value(is_right=False),
                            ),
                            style=self.get_brackets_style,
                            dont_extend_width=True,
                        ),
                        Window(
                            content=None,
                            dont_extend_width=True,
                            style=self.get_brackets_style,
                            width=1,
                        ),
                    ]),
                    filter=Condition(self._with_left_bracket),
                ),
                self.control,
                ConditionalContainer(
                    content=VSplit([
                        Window(
                            content=None,
                            dont_extend_width=True,
                            style=self.get_brackets_style,
                            width=1,
                        ),
                        Window(
                            BracketsControl(
                                bracket_type.value(is_right=True),
                            ),
                            style=self.get_brackets_style,
                            dont_extend_width=True,
                        ),
                    ]),
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
        get_app().layout.focus(self.control)

    def unfocus(self) -> None:
        self._focused = False
    
    # MagicContainer
    def __pt_container__(self) -> Container:
        return self.layout

    def _get_formatted_text(self) -> AnyFormattedText:
        return self.text

    def _get_style(self) -> str:
        if self._focused:
            return self.style.focused
        elif self.state.disabled:
            return self.style.disabled
        return self.style.base
    
    def get_brackets_style(self) -> str:
        if self._focused:
            return self.brackets_style.focused
        elif self.state.disabled:
            return self.brackets_style.disabled
        return self.brackets_style.base

    def _with_left_bracket(self) -> bool:
        return to_bool(self.with_left_bracket)

    def _with_right_bracket(self) -> bool:
        return to_bool(self.with_right_bracket)
