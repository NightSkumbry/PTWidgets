from pt_widgets.layout import get_vertical_write_positions, get_horizontal_write_positions, GridSplit
from prompt_toolkit.layout import D, HorizontalAlign, Layout, VSplit, Window, FormattedTextControl, HSplit, FloatContainer
from prompt_toolkit import Application
from prompt_toolkit.formatted_text import to_formatted_text
from functools import partial
from random import randint
from prompt_toolkit.layout.screen import WritePosition


def G_split():
    
    split = GridSplit([[
        Window(style='bg:#123456', content=FormattedTextControl([('', '\n'.join([chr(ord('a')+i+j)[0]*randint(1, 4)] * randint(1, 4)) + '\n')]), height=D(max=7), width=D(max=7))
        for i in range(5)
    ] for j in range(0, 25, 5)],
        height=D(max=30, weight=1),
        width=D(max=30),
        # horizontal_align=HorizontalAlign.CENTER
        # padding_width=D.exact(10),
        # padding_height=D.exact(2),
        padding_style='bg:#6543F1'
    )
    
    def get_h_text():
        return to_formatted_text([('', str(get_horizontal_write_positions(split, WritePosition(0, 0, 162, 23))))])
    def get_v_text():
        return to_formatted_text([('', str(get_vertical_write_positions(split, WritePosition(0, 0, 162, 23))))])

    layout = Layout(FloatContainer(content=HSplit([
        split,
        Window(content=FormattedTextControl(text=get_h_text), wrap_lines=True, height=D.exact(3)),
        Window(content=FormattedTextControl(text=get_v_text), wrap_lines=True, height=D.exact(3)),
    ],), floats=[]))
    
    app = Application(
        layout=layout,
        full_screen=True,
        mouse_support=False,
        erase_when_done=True,
    )

    app.run()


if __name__ == "__main__":
    G_split()


