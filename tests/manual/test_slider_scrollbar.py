
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

from pt_widgets.widgets.slider import SliderA, SliderB, SliderC, ScrollbarA, ScrollbarB, FillMode, Orientation
from pt_widgets.layout.navigation import VerticalLayout, HorizontalLayout
from pt_widgets.widgets.label import Label
from shared_styles import get_shared_style

def main():
    # 1. Sliders (Using Presets)
    s1 = SliderA(value=30, width=40, fill_mode=FillMode.BEFORE)
    s2 = SliderB(value=50, width=40, fill_mode=FillMode.AFTER)
    s3 = SliderC(value=70, width=40, fill_mode=FillMode.NONE)
    
    # 2. Scrollbars (Using Presets)
    sb_v_a = ScrollbarA(orientation=Orientation.VERTICAL, height=10)
    sb_v_b = ScrollbarB(orientation=Orientation.VERTICAL, height=10)
    
    sb_h_a = ScrollbarA(orientation=Orientation.HORIZONTAL, width=40)
    sb_h_b = ScrollbarB(orientation=Orientation.HORIZONTAL, width=40)
    
    # A slider to control the scrollbar position
    s_control = SliderA(value=0, min_val=0, max_val=100, width=40)
    
    def on_val_change(val):
        # Mocking update_state(position, total, visible)
        sb_v_a.update_state(int(val), 150, 50)
        sb_v_b.update_state(int(val), 150, 50)
        sb_h_a.update_state(int(val), 150, 50)
        sb_h_b.update_state(int(val), 150, 50)

    s_control.on_change = on_val_change
    on_val_change(0) # Initial update

    vl = VerticalLayout([
            Label("=== Slider & Scrollbar Test ==="),
            Label("--- Sliders ---"),
            s1,
            s2,
            s3,
            Label("--- Scrollbars (Controlled by Slider below) ---"),
            HorizontalLayout([
                VerticalLayout([
                    Label("Controller:"),
                    s_control,
                    Label("H Scrollbar A:"),
                    sb_h_a,
                    Label("H Scrollbar B:"),
                    sb_h_b
                ]),
                VerticalLayout([
                    Label("VA:"),
                    sb_v_a
                ]),
                VerticalLayout([
                    Label("VB:"),
                    sb_v_b
                ])
            ], padding=2)
        ])

    kb = KeyBindings()
    @kb.add("c-c")
    @kb.add("q")
    def _(event):
        event.app.exit()

    app = Application(
        layout=Layout(vl),
        key_bindings=kb,
        style=get_shared_style(),
        full_screen=True,
        mouse_support=True,
    )
    
    # Initial focus
    app.pre_run_callables.append(lambda: vl.focus())
    
    app.run()

if __name__ == "__main__":
    main()
