from prompt_toolkit.styles import Style

def get_shared_style() -> Style:
    return Style.from_dict({
        # Кнопки
        "pt_widget.button": "fg:ansiblue bg:ansigray",
        "pt_widget.button.focused": "fg:ansiyellow bg:ansiblue",
        "pt_widget.button.disabled": "fg:ansigray bg:ansiblack",
        
        # Метки
        "pt_widget.label": "fg:ansiwhite",
        "pt_widget.label.focused": "fg:ansiblack bg:ansiwhite",
        "pt_widget.label.disabled": "fg:ansigray",
        
        # Переключатели (Текст)
        "pt_widget.switch.text": "fg:ansiwhite",
        "pt_widget.switch.text.focused": "fg:ansiblack bg:ansiyellow",
        "pt_widget.switch.text.disabled": "fg:ansigray",
        "pt_widget.switch.text.on": "fg:ansigreen bold",
        "pt_widget.switch.text.on.focused": "fg:ansiyellow bg:ansigreen",
        "pt_widget.switch.text.on.disabled": "fg:ansidarkgreen nobold",
        
        # Переключатели (Тумблер)
        "pt_widget.switch.toggle": "fg:ansired",
        "pt_widget.switch.toggle.focused": "fg:ansired bg:ansiyellow",
        "pt_widget.switch.toggle.disabled": "fg:ansidarkred",
        "pt_widget.switch.toggle.on": "fg:ansibrightgreen",
        "pt_widget.switch.toggle.on.focused": "fg:ansibrightgreen bg:ansiyellow",
        "pt_widget.switch.toggle.on.disabled": "fg:ansigreen",
        
        # LineEdit
        "pt_widget.line_edit": "fg:ansiblue bg:ansigray",
        "pt_widget.line_edit.focused": "fg:ansiyellow bg:ansiblue",
        "pt_widget.line_edit.disabled": "fg:ansigray bg:ansiblack",
        "pt_widget.line_edit.edit": "fg:ansiwhite bg:ansiblack",
        "pt_widget.line_edit.edit.focused": "fg:ansiwhite bg:ansiblack",
        "pt_widget.line_edit.error": "fg:ansiwhite bg:ansired",
        "pt_widget.line_edit.error.focused": "fg:ansiyellow bg:ansidarkred",
        
        # Скобки
        "pt_widget.brackets": "fg:ansicyan",
        "pt_widget.brackets.focused": "fg:ansiwhite bg:ansiblue",
        "pt_widget.brackets.disabled": "fg:ansicyan",
    })
