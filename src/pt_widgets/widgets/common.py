from dataclasses import dataclass
from typing import Callable, Union


@dataclass
class WidgetStyle:
    base: str = ""
    focused: str = ""
    disabled: str = ""
    
def combine_styles(WidgetStyle1: WidgetStyle | None, WidgetStyle2: WidgetStyle | None) -> WidgetStyle:
    """
    returns a style with components of both styles, prioritizing WidgetStyle1 over WidgetStyle2
    """
    if WidgetStyle1 is None:
        return WidgetStyle2 if WidgetStyle2 is not None else WidgetStyle("", "", "")
    if WidgetStyle2 is None:
        return WidgetStyle1
    return WidgetStyle(
        base=WidgetStyle1.base or WidgetStyle2.base,
        focused=WidgetStyle1.focused or WidgetStyle2.focused,
        disabled=WidgetStyle1.disabled or WidgetStyle2.disabled,
    )


@dataclass
class WidgetState:
    focusable: bool = True
    disabled: bool = False
    checked: bool = False


BoolOrCallable = Union[
    bool,
    Callable[[], bool],
]

def to_bool(bool_or_callable: BoolOrCallable) -> bool:
    if callable(bool_or_callable):
        return bool_or_callable()
    return bool_or_callable



