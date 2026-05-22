from dataclasses import dataclass
from typing import Callable

from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import AnyDimension, Container, VSplit, Window, BufferControl, D, to_dimension
from prompt_toolkit.validation import Validator

from pt_widgets.layout.containers import ConditionalContainer
from pt_widgets.widgets.brackets import BracketType, BracketsControl
from pt_widgets.widgets.button import Button
from pt_widgets.widgets.common import BoolOrCallable, WidgetState, WidgetStyle, combine_styles, to_bool


@dataclass
class TextEditState(WidgetState):
    text: str
    editing: bool
    error: bool


class TextEdit:
    def __init__(
        self,
        text: str = "",
        multiline: bool = False,
        validator: Validator | None = None,
        handler: Callable[[str], None] | None = None,
        width: AnyDimension = None,
        height: AnyDimension = None,
        style: WidgetStyle | None = None,
        edit_style: WidgetStyle | None = None,
        error_style: WidgetStyle | None = None,
        brackets_style: WidgetStyle | None = None,
        state: TextEditState | None = None,
        with_left_bracket: BoolOrCallable = False,
        with_right_bracket: BoolOrCallable = False,
        bracket_type: BracketType = BracketType.SQUARE,
        edit_bracket_type: BracketType | None = None,
        custom_button_key_bindings: KeyBindings | None = None,
        custom_edit_key_bindings: KeyBindings | None = None,
    ) -> None:
        self.multiline = multiline
        self.validator = validator
        self.handler = handler
        self.width = width
        self.height = height
        self._focused = False
        
        # Styles
        self.style = combine_styles(style, WidgetStyle(
            base="class:pt_widget.line_edit",
            focused="class:pt_widget.line_edit.focused",
            disabled="class:pt_widget.line_edit.disabled"
        ))
        self.edit_style = combine_styles(edit_style, WidgetStyle(
            base="class:pt_widget.line_edit.edit",
            focused="class:pt_widget.line_edit.edit.focused",
        ))
        self.error_style = combine_styles(error_style, WidgetStyle(
            base="class:pt_widget.line_edit.error",
            focused="class:pt_widget.line_edit.error.focused",
        ))
        self.brackets_style = combine_styles(brackets_style, WidgetStyle(
            base="class:pt_widget.brackets",
            focused="class:pt_widget.brackets.focused",
            disabled="class:pt_widget.brackets.disabled"
        ))
        
        # State
        self.state = state if state is not None else TextEditState(
            text=text,
            editing=False,
            error=False,
            focusable=True,
            disabled=False
        )
        
        self._original_text = text
        
        self.with_left_bracket = with_left_bracket
        self.with_right_bracket = with_right_bracket
        self.bracket_type = bracket_type
        self.edit_bracket_type = edit_bracket_type or bracket_type

        # Buffer setup
        self.buffer = Buffer(
            document=Document(text, 0),
            multiline=multiline,
            read_only=Condition(lambda: not self.state.editing),
            on_text_changed=self._on_text_changed,
        )

        self.buffer_control = BufferControl(
            buffer=self.buffer,
            focusable=True,
            key_bindings=self._get_edit_key_bindings() if custom_edit_key_bindings is None else custom_edit_key_bindings,
        )
        
        # Display mode button
        self.button = Button(
            text=lambda: self.buffer.text,
            handler=self._start_editing,
            width=width,
            height=height,
            style=self.style,
            brackets_style=self.brackets_style,
            state=self.state,
            with_left_bracket=with_left_bracket,
            with_right_bracket=with_right_bracket,
            bracket_type=bracket_type,
            custom_key_bindings=custom_button_key_bindings,
        )

        # Main layout
        self.layout = ConditionalContainer(
            content=self._create_editor_layout(),
            filter=Condition(lambda: self.state.editing),
            alternative_content=self.button,
        )

    def _create_editor_layout(self) -> VSplit:
        def get_bracket_layout(is_right: bool):
            content = []
            if is_right:
                content.append(Window(width=1, dont_extend_width=True, style=self._get_brackets_style))
            
            content.append(Window(
                BracketsControl(self.edit_bracket_type.value(is_right=is_right)),
                style=self._get_brackets_style,
                dont_extend_width=True,
                height=self._get_height_dim,
            ))
            
            if not is_right:
                content.append(Window(width=1, dont_extend_width=True, style=self._get_brackets_style))
                
            return VSplit(content)

        return VSplit(
            [
                ConditionalContainer(
                    content=get_bracket_layout(False),
                    filter=Condition(lambda: to_bool(self.with_left_bracket)),
                ),
                Window(
                    content=self.buffer_control,
                    dont_extend_height=True,
                    dont_extend_width=True,
                    width=self._get_width_dim,
                    height=self._get_height_dim,
                    style=self._get_style,
                ),
                ConditionalContainer(
                    content=get_bracket_layout(True),
                    filter=Condition(lambda: to_bool(self.with_right_bracket)),
                ),
            ],
            width=self.width,
            height=self.height,
            modal=True,
        )

    def _get_width_dim(self) -> D:
        if self.width is not None:
            return to_dimension(self.width)
        lines = self.buffer.text.split('\n')
        max_len = max(len(line) for line in lines) if lines else 0
        return D(min=max_len + 1, preferred=max_len + 1)

    def _get_height_dim(self) -> D:
        if self.height is not None:
            return to_dimension(self.height)
        if self.multiline:
            lines = self.buffer.text.split('\n')
            return D(min=len(lines), preferred=len(lines))
        return D.exact(1)

    def _start_editing(self) -> None:
        self._original_text = self.buffer.text
        self.state.editing = True
        get_app().layout.focus(self.buffer_control)

    @property
    def text(self) -> str:
        return self.buffer.text

    @text.setter
    def text(self, value: str) -> None:
        self.buffer.set_document(Document(value, 0), bypass_readonly=True)

    def _on_text_changed(self, buffer: Buffer) -> None:
        self.state.error = False

    def is_focusable(self) -> bool:
        return self.state.focusable and not self.state.disabled

    def focus(self) -> None:
        self._focused = True
        if self.state.editing:
            get_app().layout.focus(self.buffer_control)
        else:
            self.button.focus()

    def unfocus(self) -> None:
        self._focused = False
        self.button.unfocus()

    def __pt_container__(self) -> Container:
        return self.layout

    def _get_style(self) -> str:
        if self.state.error:
            return self.error_style.focused if self._focused else self.error_style.base
        if self.state.editing:
            return self.edit_style.focused if self._focused else self.edit_style.base
        return self.style.focused if self._focused else self.style.base

    def _get_brackets_style(self) -> str:
        if self.state.disabled:
            return self.brackets_style.disabled
        return self.brackets_style.focused if self._focused else self.brackets_style.base

    def _get_edit_key_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("enter", filter=Condition(lambda: self.state.editing))
        def _(event: KeyPressEvent):
            if self.validator:
                try:
                    self.validator.validate(self.buffer.document)
                except Exception:
                    self.state.error = True
                    return
            
            self.state.editing = False
            self.state.error = False
            get_app().layout.focus(self.button)
            
            if self.handler:
                self.handler(self.buffer.text)

        @kb.add("escape", filter=Condition(lambda: self.state.editing))
        def _(event: KeyPressEvent):
            self.buffer.text = self._original_text
            self.state.editing = False
            self.state.error = False
            get_app().layout.focus(self.button)

        @kb.add('escape', 'enter', filter=Condition(lambda: self.state.editing and self.multiline))
        def _(event: KeyPressEvent):
            event.current_buffer.insert_text("\n")

        return kb
