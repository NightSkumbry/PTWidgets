from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.formatted_text import HTML

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

    # 1. Styled text (HTML) + auto-update (no handler)
    line_edit_styled = TextEdit(
        text=HTML('<style color="ansiyellow">Styled</style> <style color="ansicyan">Text</style>'),
        with_left_bracket=True,
        with_right_bracket=True,
    )

    # 2. Simple Edit + handler + no update
    line_edit1 = TextEdit(
        text="Edit me (Handler + no update)",
        with_left_bracket=True,
        with_right_bracket=True,
        bracket_type=BracketType.SQUARE,
        edit_bracket_type=BracketType.PARENTHESIS,
        save_handler=handle_save("Edit1"),
        update_button_text_from_buffer=False
    )

    # 3. Validated Edit + auto-update
    line_edit2 = TextEdit(
        text="No Handler (Auto-save)",
        validator=NotIntegerValidator(),
        with_left_bracket=True,
        with_right_bracket=True,
    )

    # 4. Multiline Edit + handler
    line_edit3 = TextEdit(
        text="Multiline\nArea",
        multiline=True,
        with_left_bracket=True,
        with_right_bracket=True,
        save_handler=handle_save("Edit3")
    )

    layout = VerticalLayout([
        Label("=== PTWidgets TextEdit Test ===", style=WidgetStyle(base="fg:ansiyellow bold")),
        
        status_label,

        Label("\n1. HTML Styled Text (Auto-updates to plain text):"),
        line_edit_styled,

        Label("\n2. Simple Edit (Has Handler, status updates):"),
        line_edit1,

        Label("\n3. Validated Edit (No Handler, button updates automatically):"),
        line_edit2,

        Label("\n4. Multiline Edit (Has Handler):"),
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
