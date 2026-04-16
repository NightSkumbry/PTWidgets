from typing import Callable, NamedTuple, Sequence, override, Protocol, runtime_checkable

from prompt_toolkit.application import get_app
from prompt_toolkit.filters import Always, Condition, Filter
from prompt_toolkit.key_binding import KeyBindings, KeyBindingsBase, KeyPressEvent, merge_key_bindings
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
        raise FocusException("This container is not focusable")
    
    c = to_container(container)
    if isinstance(c, Focusable):
        if c.is_focusable():
            c.focus()
            return
        raise FocusException("This container is not focusable")
    
    get_app().layout.focus(c)
            
    
class VerticalLayout(HSplit):
    def __init__(
        self,
        children: Sequence[AnyContainer],
        window_too_small: Container | None = None,
        align: VerticalAlign = VerticalAlign.JUSTIFY,
        padding: AnyDimension = 0,
        padding_char: str | None = None,
        padding_style: str = "",
        width: AnyDimension = None,
        height: AnyDimension = None,
        z_index: int | None = None,
        modal: bool = False,
        key_bindings: KeyBindingsBase | None = None,
        style: str | Callable[[], str] = "",
        focusable: bool = True,
        cyclic: bool = False,
        shift_point: bool = False,
        base_focus: int = 0,
        up_filter: Filter = Always(),
        down_filter: Filter = Always(),
    ) -> None:
        super().__init__(
            children=children,
            window_too_small=window_too_small,
            padding=padding,
            padding_char=padding_char,
            padding_style=padding_style,
            width=width,
            height=height,
            z_index=z_index,
            modal=modal,
            key_bindings=key_bindings,
            style=style,
            align=align,
        )
        
        self.focusable = focusable
        self.cyclic = cyclic
        self._last_focus: int = base_focus
        self.up_filter = up_filter
        self.down_filter = down_filter
        self.shift_point = shift_point
        
        self._register_key_bindings()
    
    # Focusable
    def is_focusable(self) -> bool:
        return self.focusable
    
    def focus(self) -> None:
        self.move_focus_up(0)
    
    @property
    def _focusable_children_indices(self) -> list[int]:
        return [i for i, c in enumerate(self.get_children()) if is_focusable(c)]
    
    def move_focus_up(self, amount: int = 1) -> None:
        focusable_indices = self._focusable_children_indices
        
        if not focusable_indices:
            raise FocusException("No focusable children")
        
        for ind, i in enumerate(focusable_indices):
            if i >= self._last_focus:
                base_index = ind
                break
        else:
            base_index = (-1) % len(focusable_indices)
        
        if not get_app().layout.has_focus(self):
            focus(self.get_children()[focusable_indices[base_index]])
        else:
            base_index -= amount
            if self.cyclic:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
                
            self._last_focus = focusable_indices[base_index]
            focus(self.get_children()[focusable_indices[base_index]])
    
    def move_focus_down(self, amount: int = 1) -> None:
        focusable_indices = self._focusable_children_indices

        if not focusable_indices:
            raise FocusException("No focusable children")
        
        for ind, i in enumerate(focusable_indices[::-1], 1):
            if i <= self._last_focus:
                base_index = len(focusable_indices) - ind
                break
        else:
            base_index = 0
        
        if not get_app().layout.has_focus(self):
            focus(self.get_children()[focusable_indices[base_index]])
        else:
            base_index += amount
            if self.cyclic:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
            
            self._last_focus = focusable_indices[base_index]
            focus(self.get_children()[focusable_indices[base_index]])
        
    def _register_key_bindings(self) -> None:
        if not self.key_bindings:
            self.key_bindings = KeyBindings()

        default_bindings = KeyBindings()
        
        @Condition
        def up_filter() -> bool:
            if self._focusable_children_indices:
                if self.cyclic:
                    return True
                if not get_app().layout.has_focus(self.get_children()[self._focusable_children_indices[0]]):
                    return True
            return False

        @Condition
        def down_filter() -> bool:
            if self._focusable_children_indices:
                if self.cyclic:
                    return True
                if not get_app().layout.has_focus(self.get_children()[self._focusable_children_indices[-1]]):
                    return True
            return False
        
        @Condition
        def shift_point_filter() -> bool:
            return self.shift_point
        
        default_bindings.add("up", filter=up_filter and self.up_filter)
        def _(event: KeyPressEvent):
            self.move_focus_up()
        
        default_bindings.add("down", filter=down_filter and self.down_filter)
        def _(event: KeyPressEvent):
            self.move_focus_down()
        
        
        default_bindings.add("s-up", filter=up_filter and self.up_filter and shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_up()
        
        default_bindings.add("s-down", filter=down_filter and self.down_filter and shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_down()
        
        self.key_bindings = merge_key_bindings([self.key_bindings, default_bindings])

        
        
        

        
        
