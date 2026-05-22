from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.validation import Validator, ValidationError

from pt_widgets.widgets.button import Button
from pt_widgets.widgets.text_edit import TextEdit
from pt_widgets.layout.navigation import VerticalLayout, HorizontalLayout
from pt_widgets.widgets.label import Label
from pt_widgets.widgets.brackets import BracketType
from pt_widgets.widgets.common import WidgetStyle
from shared_styles import get_shared_style


class NotIntegerValidator(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            pass
        else:
            raise ValidationError(message="Cannot be an integer")

def run():
    status_label = Label("Status: Waiting for input...", style=WidgetStyle(base="fg:ansigreen"))

    def handle_save(name: str):
        def handler(text: str):
            status_label.text = f"Status: Saved {name}: {text.replace('\n', ' ')}"
        return handler

    line_edit1 = TextEdit(
        text="Edit me",
        with_left_bracket=True,
        with_right_bracket=True,
        bracket_type=BracketType.SQUARE,
        edit_bracket_type=BracketType.PARENTHESIS,
        handler=handle_save("Edit1")
    )

    line_edit2 = TextEdit(
        text="Mandatory",
        validator=NotIntegerValidator(),
        with_left_bracket=True,
        with_right_bracket=True,
        handler=handle_save("Edit2")
    )

    line_edit3 = TextEdit(
        text="Multiline\nArea",
        multiline=True,
        with_left_bracket=True,
        with_right_bracket=True,
        handler=handle_save("Edit3")
    )

    layout = VerticalLayout([
        Button("Кнопка"),
        
        Label("=== PTWidgets LineEdit Test ===", style=WidgetStyle(base="fg:ansiyellow bold")),
        
        status_label,

        Label("\nSimple LineEdit (Changes brackets on edit):"),
        line_edit1,

        Label("\nValidated LineEdit (Cannot be empty):"),
        line_edit2,

        Label("\nMultiline LineEdit (Use Esc+Enter for newline):"),
        line_edit3,

        Label("\n[ Arrows: Navigate | Enter: Edit/Save | Esc: Cancel | Ctrl+C: Exit ]",
              style=WidgetStyle(base="fg:ansigray italic")),
    ], padding=0)

    kb = KeyBindings()
    @kb.add("c-c")
    def _(event):
        event.app.exit()

    app = Application(
        layout=Layout(layout),
        key_bindings=kb,
        style=get_shared_style(),
        full_screen=True,
        mouse_support=True,
    )
    
    app.pre_run_callables.append(lambda: layout.focus())
    
    app.run()

if __name__ == "__main__":
    run()
