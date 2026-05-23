from enum import Enum
import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.formatted_text import HTML

from pt_widgets.widgets.button import Button
from pt_widgets.widgets.label import Label
from pt_widgets.widgets.text_edit import TextEdit
from pt_widgets.layout.navigation import VerticalLayout, HorizontalLayout
from pt_widgets.managers.window import WindowManager
from pt_widgets.widgets.common import WidgetStyle
from shared_styles import get_shared_style


class AppState(Enum):
    MENU = "menu"
    SETTINGS = "settings"
    INFO = "info"


def run():
    # --- 1. Define valid transitions ---
    # From MENU we can go to SETTINGS or INFO
    # From SETTINGS or INFO we can only go back to MENU
    transitions = {
        AppState.MENU: [AppState.SETTINGS, AppState.INFO],
        AppState.SETTINGS: [AppState.MENU],
        AppState.INFO: [AppState.MENU],
    }

    # --- 2. Initialize WindowManager ---
    wm = WindowManager(initial_state=AppState.MENU, valid_transitions=transitions)

    # --- 3. Create Windows for each state ---

    # --- MENU WINDOW ---
    menu_layout = VerticalLayout([
        Label("MAIN MENU", style=WidgetStyle(base="fg:ansiyellow bold")),
        Button("Go to Settings", handler=lambda: wm.switch_to(AppState.SETTINGS)),
        Button("Go to Info", handler=lambda: wm.switch_to(AppState.INFO)),
    ], padding=1)
    wm.register_window(AppState.MENU, menu_layout)

    # --- SETTINGS WINDOW ---
    settings_layout = VerticalLayout([
        Label("SETTINGS", style=WidgetStyle(base="fg:ansicyan bold")),
        TextEdit("Username", with_left_bracket=True, with_right_bracket=True),
        TextEdit("API Key", with_left_bracket=True, with_right_bracket=True),
        Button("Back to Menu", handler=lambda: wm.switch_to(AppState.MENU)),
    ], padding=1)
    wm.register_window(AppState.SETTINGS, settings_layout)

    # --- INFO WINDOW ---
    info_layout = VerticalLayout([
        Label("INFORMATION", style=WidgetStyle(base="fg:ansigreen bold")),
        Label("This is a WindowManager demo."),
        Label("It handles state transitions and window delegation."),
        Button("Back to Menu", handler=lambda: wm.switch_to(AppState.MENU)),
    ], padding=1)
    wm.register_window(AppState.INFO, info_layout)

    # --- Root Layout ---
    status_line = Label(lambda: f"Current State: {wm.current_state.name}", style=WidgetStyle(base="fg:ansimagenta"))

    root_layout = VerticalLayout([
        Label("=== WindowManager Manual Test ===", style=WidgetStyle(base="fg:ansiyellow reverse")),
        status_line,
        wm, # WindowManager acts as a container
        Label("\n[ F1: Menu | F2: Settings | F3: Info | Ctrl+C: Exit ]", style=WidgetStyle(base="fg:ansigray italic")),
    ], padding=1)

    kb = KeyBindings()

    @kb.add("c-c")
    def _(event):
        event.app.exit()

    @kb.add("f1")
    def _(event):
        try:
            wm.switch_to(AppState.MENU)
        except ValueError:
            pass

    @kb.add("f2")
    def _(event):
        try:
            wm.switch_to(AppState.SETTINGS)
        except ValueError:
            pass

    @kb.add("f3")
    def _(event):
        try:
            wm.switch_to(AppState.INFO)
        except ValueError:
            pass

    app = Application(
        layout=Layout(root_layout),
        key_bindings=kb,
        style=get_shared_style(),
        full_screen=True,
        mouse_support=True,
    )

    app.pre_run_callables.append(lambda: root_layout.focus())

    app.run()


if __name__ == "__main__":
    run()
