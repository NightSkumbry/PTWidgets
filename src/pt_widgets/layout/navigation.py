from typing import Callable, NamedTuple, Sequence, override, Protocol, runtime_checkable

from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindingsBase
from prompt_toolkit.layout import AnyContainer, AnyDimension, HSplit, VerticalAlign, Container, to_container

from pt_widgets.exceptions import FocusException


@runtime_checkable
class Focusable(Protocol):
    def is_focusable(self) -> bool:
        ...
    
    def focus(self) -> None:
        ...


def is_focusable(container: AnyContainer) -> bool:
    if isinstance(container, Focusable):
        return container.is_focusable()

    c = to_container(container)
    if isinstance(c, Focusable):
        return c.is_focusable()
    
    return False

def focus(container: AnyContainer) -> None:
    if isinstance(container, Focusable):
        if container.is_focusable():
            container.focus()
            return
        raise FocusException("This container is not focusable now")
    
    c = to_container(container)
    if isinstance(c, Focusable):
        if c.is_focusable():
            c.focus()
            return
        raise FocusException("This container is not focusable now")
    
    get_app().layout.focus(c)
            
            
        
        
        

        
    
    






