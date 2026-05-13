from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from pt_widgets.widgets.label import Label
from pt_widgets.widgets.switch import Checkbox, CheckboxGroup, RadioButton, RadioGroup, SwitchType
from pt_widgets.layout.navigation import VerticalLayout, HorizontalLayout
from pt_widgets.widgets.common import WidgetState, WidgetStyle
from shared_styles import get_shared_style

def run():
    # Состояние для отображения результатов
    cb_status = Label("Checkbox Selection: Python, Go") # Default state
    rb_status = Label("Radio Selection: Medium") # Default state

    # --- Checkbox Group ---
    cb_items = {
        "Python": Checkbox("Python", state=WidgetState(checked=True)),
        "Rust": Checkbox("Rust"),
        "C++": Checkbox("C++"),
        "Go": Checkbox("Go", state=WidgetState(checked=True))
    }
    
    def cb_handler(name, checked):
        selected = [name for name, cb in cb_items.items() if cb.state.checked]
        cb_status.text = f"Checkbox Selection: {', '.join(selected) if selected else 'None'}"

    CheckboxGroup(cb_items, handler=cb_handler)

    # --- Radio Group ---
    rb_items = {
        "Small": RadioButton("Small"),
        "Medium": RadioButton("Medium", state=WidgetState(checked=True)),
        "Large": RadioButton("Large"),
        "Optional (Can be unselected)": RadioButton("Optional (Can be unselected)", can_be_disabled=True)
    }

    def rb_handler(name):
        rb_status.text = f"Radio Selection: {name}"

    RadioGroup(rb_items, handler=rb_handler)

    # Дополнительный обработчик для "Optional", чтобы обновить статус при снятии выделения
    optional_rb = rb_items["Optional (Can be unselected)"]
    original_optional_handler = optional_rb.handler
    def custom_optional_handler(checked):
        if original_optional_handler:
            original_optional_handler(checked)
        if not checked:
            rb_status.text = "Radio Selection: None (Optional unselected)"
    
    optional_rb.handler = custom_optional_handler

    layout = VerticalLayout([
        Label("=== PTWidgets Switch Groups Test ===", style=WidgetStyle(base="fg:ansiyellow bold")),
        
        Label("\n--- Checkbox Group (Select Multiple) ---", style=WidgetStyle(base="fg:ansicyan underline")),
        VerticalLayout(list(cb_items.values())),
        cb_status,

        Label("\n--- Radio Group (Select One) ---", style=WidgetStyle(base="fg:ansicyan underline")),
        VerticalLayout(list(rb_items.values())),
        rb_status,

        Label("\n[ Use Arrows to Navigate, Enter to Toggle, Ctrl+C to Exit ]", style=WidgetStyle(base="fg:ansigray italic")),
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
