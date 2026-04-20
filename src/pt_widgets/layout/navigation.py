from typing import Callable, NamedTuple, Sequence, override, Protocol, runtime_checkable

from prompt_toolkit.application import get_app
from prompt_toolkit.filters import Always, Condition, Filter
from prompt_toolkit.key_binding import KeyBindings, KeyBindingsBase, KeyPressEvent, merge_key_bindings
from prompt_toolkit.layout import (
    AnyContainer,
    AnyDimension,
    HSplit,
    HorizontalAlign,
    VSplit,
    VerticalAlign,
    Container,
    to_container,
)

from pt_widgets.exceptions import FocusException
from pt_widgets.layout.containers import GridSplit


@runtime_checkable
class Focusable(Protocol):
    def is_focusable(self) -> bool:
        ...
    
    def focus(self) -> None:
        ...
        
    def unfocus(self) -> None:
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

def unfocus(container: AnyContainer) -> None:
    if isinstance(container, Focusable):
        container.unfocus()
    
    c = to_container(container)
    if isinstance(c, Focusable):
        c.unfocus()
            
    
class VerticalLayout:
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
        self.up_filter = up_filter
        self.down_filter = down_filter
        
        self.container = HSplit(
            children=children,
            window_too_small=window_too_small,
            padding=padding,
            padding_char=padding_char,
            padding_style=padding_style,
            width=width,
            height=height,
            z_index=z_index,
            modal=modal,
            key_bindings=self._register_key_bindings(key_bindings),
            style=style,
            align=align,
        )

        self.widgets = children
        self.focusable = focusable
        self.cyclic = cyclic
        self._last_focus: int = base_focus
        self.shift_point = shift_point
        self.active = False
        
    
    # Focusable
    def is_focusable(self) -> bool:
        return self.focusable and any(is_focusable(c) for c in self.widgets)
    
    def focus(self) -> None:
        self.active = True
        self._focus_closest()
    
    def unfocus(self) -> None:
        self.active = False
        unfocus(self.widgets[self._last_focus])
    
    # MagicContainer
    def __pt_container__(self):
        return self.container
    
    @property
    def _focusable_children_indices(self) -> list[int]:
        return [i for i, c in enumerate(self.widgets) if is_focusable(c)]
    
    def _focus_closest(self) -> None:
        focusable_indices = self._focusable_children_indices
        closest = min(focusable_indices, key=lambda i: abs(i - self._last_focus))
        self._last_focus = closest
        focus(self.widgets[closest])
        
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
        
        if not self.active:
            self._last_focus = focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]])
        else:
            base_index -= amount
            if self.cyclic:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
            
            unfocus(self.widgets[self._last_focus])
            self._last_focus = focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]])
    
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
        
        if not self.active:
            self._last_focus = focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]])
        else:
            base_index += amount
            if self.cyclic:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
            
            unfocus(self.widgets[self._last_focus])
            self._last_focus = focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]])
        
    def _register_key_bindings(self, kb: KeyBindingsBase | None) -> KeyBindingsBase:
        if kb is None:
            kb = KeyBindings()
        
        default_bindings = KeyBindings()
        
        @Condition
        def up_filter() -> bool:
            fc = self._focusable_children_indices
            if fc:
                if self.cyclic:
                    return True
                if self._last_focus > fc[0]:
                    return True
            return False

        @Condition
        def down_filter() -> bool:
            fc = self._focusable_children_indices
            if fc:
                if self.cyclic:
                    return True
                if self._last_focus < fc[-1]:
                    return True
            return False
        
        @Condition
        def shift_point_filter() -> bool:
            return self.shift_point
        
        @default_bindings.add("up", filter=up_filter & self.up_filter)
        def _(event: KeyPressEvent):
            self.move_focus_up()
        
        @default_bindings.add("down", filter=down_filter & self.down_filter)
        def _(event: KeyPressEvent):
            self.move_focus_down()
        
        
        @default_bindings.add("s-up", filter=up_filter & self.up_filter & shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_up()
        
        @default_bindings.add("s-down", filter=down_filter & self.down_filter & shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_down()
        
        return merge_key_bindings([kb, default_bindings])
        
        
class HorizontalLayout:
    def __init__(
        self,
        children: Sequence[AnyContainer],
        window_too_small: Container | None = None,
        align: HorizontalAlign = HorizontalAlign.JUSTIFY,
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
        left_filter: Filter = Always(),
        right_filter: Filter = Always(),
    ) -> None:
        self.left_filter = left_filter
        self.right_filter = right_filter
        
        self.container = VSplit(
            children=children,
            window_too_small=window_too_small,
            padding=padding,
            padding_char=padding_char,
            padding_style=padding_style,
            width=width,
            height=height,
            z_index=z_index,
            modal=modal,
            key_bindings=self._register_key_bindings(key_bindings),
            style=style,
            align=align,
        )

        self.widgets = children
        self.focusable = focusable
        self.cyclic = cyclic
        self._last_focus: int = base_focus
        self.shift_point = shift_point
        self.active = False
        
    
    # Focusable
    def is_focusable(self) -> bool:
        return self.focusable and any(is_focusable(c) for c in self.widgets)
    
    def focus(self) -> None:
        self.active = True
        self._focus_closest()
    
    def unfocus(self) -> None:
        self.active = False
        unfocus(self.widgets[self._last_focus])
    
    # MagicContainer
    def __pt_container__(self):
        return self.container
    
    @property
    def _focusable_children_indices(self) -> list[int]:
        return [i for i, c in enumerate(self.widgets) if is_focusable(c)]
    
    def _focus_closest(self) -> None:
        focusable_indices = self._focusable_children_indices
        closest = min(focusable_indices, key=lambda i: abs(i - self._last_focus))
        self._last_focus = closest
        focus(self.widgets[closest])
    
    def move_focus_left(self, amount: int = 1) -> None:
        focusable_indices = self._focusable_children_indices
        
        if not focusable_indices:
            raise FocusException("No focusable children")
        
        for ind, i in enumerate(focusable_indices):
            if i >= self._last_focus:
                base_index = ind
                break
        else:
            base_index = (-1) % len(focusable_indices)
        
        if not self.active:
            self._last_focus = focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]])
        else:
            base_index -= amount
            if self.cyclic:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
            
            unfocus(self.widgets[self._last_focus])
            self._last_focus = focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]])
    
    def move_focus_right(self, amount: int = 1) -> None:
        focusable_indices = self._focusable_children_indices

        if not focusable_indices:
            raise FocusException("No focusable children")
        
        for ind, i in enumerate(focusable_indices[::-1], 1):
            if i <= self._last_focus:
                base_index = len(focusable_indices) - ind
                break
        else:
            base_index = 0
        
        if not self.active:
            self._last_focus = focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]])
        else:
            base_index += amount
            if self.cyclic:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
            
            unfocus(self.widgets[self._last_focus])
            self._last_focus = focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]])
        
    def _register_key_bindings(self, kb: KeyBindingsBase | None) -> KeyBindingsBase:
        if kb is None:
            kb = KeyBindings()
        
        default_bindings = KeyBindings()
        
        @Condition
        def left_filter() -> bool:
            fc = self._focusable_children_indices
            if fc:
                if self.cyclic:
                    return True
                if self._last_focus > fc[0]:
                    return True
            return False

        @Condition
        def right_filter() -> bool:
            fc = self._focusable_children_indices
            if fc:
                if self.cyclic:
                    return True
                if self._last_focus < fc[-1]:
                    return True
            return False
        
        @Condition
        def shift_point_filter() -> bool:
            return self.shift_point
        
        @default_bindings.add("left", filter=left_filter & self.left_filter)
        def _(event: KeyPressEvent):
            self.move_focus_left()
        
        @default_bindings.add("right", filter=right_filter & self.right_filter)
        def _(event: KeyPressEvent):
            self.move_focus_right()
        
        
        @default_bindings.add("s-left", filter=left_filter & self.left_filter & shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_left()
        
        @default_bindings.add("s-right", filter=right_filter & self.right_filter & shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_right()
        
        return merge_key_bindings([kb, default_bindings])


class GridLayout:
    def __init__(
        self,
        children: Sequence[Sequence[AnyContainer]],
        window_too_small: Container | None = None,
        vertical_align: VerticalAlign = VerticalAlign.JUSTIFY,
        horizontal_align: HorizontalAlign = HorizontalAlign.JUSTIFY,
        padding_width: AnyDimension = 0,
        padding_height: AnyDimension = 0,
        padding_char: str | None = None,
        padding_style: str = "",
        width: AnyDimension = None,
        height: AnyDimension = None,
        z_index: int | None = None,
        modal: bool = False,
        key_bindings: KeyBindingsBase | None = None,
        style: str | Callable[[], str] = "",
        focusable: bool = True,
        cyclic_horizontal: bool = False,
        cyclic_vertical: bool = False,
        shift_point: bool = False,
        base_focus: tuple[int, int] = (0, 0),
        left_filter: Filter = Always(),
        right_filter: Filter = Always(),
        up_filter: Filter = Always(),
        down_filter: Filter = Always(),
    ) -> None:
        self.left_filter = left_filter
        self.right_filter = right_filter
        self.up_filter = up_filter
        self.down_filter = down_filter
        
        self.container = GridSplit(
            children=children,
            window_too_small=window_too_small,
            vertical_align=vertical_align,
            horizontal_align=horizontal_align,
            padding_width=padding_width,
            padding_height=padding_height,
            padding_char=padding_char,
            padding_style=padding_style,
            width=width,
            height=height,
            z_index=z_index,
            modal=modal,
            key_bindings=self._register_key_bindings(key_bindings),
            style=style,
        )
        
        self.widgets = children
        self.focusable = focusable
        self.cyclic_horizontal = cyclic_horizontal
        self.cyclic_vertical = cyclic_vertical
        self._last_focus: tuple[int, int] = base_focus
        self.shift_point = shift_point
        self.active = False
    
    # Focusable
    def is_focusable(self) -> bool:
        return self.focusable and any(is_focusable(c) for r in self.widgets for c in r)
    
    def focus(self) -> None:
        self.active = True
        self._focus_closest()
    
    def unfocus(self) -> None:
        self.active = False
        unfocus(self.widgets[self._last_focus[1]][self._last_focus[0]])
    
    # MagicContainer
    def __pt_container__(self):
        return self.container
        
    @property
    def _focusable_children_indices(self) -> list[tuple[int, int]]:
        """
        returns (x, y) pairs of focusable children
        """
        
        res = []
        for y, row in enumerate(self.widgets):
            for x, c in enumerate(row):
                if is_focusable(c):
                    res.append((x, y))
        return res

    def _focus_closest(self) -> None:
        focusable_indices = self._focusable_children_indices
        closest = min(focusable_indices, key=lambda i: abs(i[0] - self._last_focus[0]) + abs(i[1] - self._last_focus[1]))
        self._last_focus = closest
        focus(self.widgets[closest[1]][closest[0]])

    def move_focus_left(self, amount: int = 1) -> None:
        last_x, last_y = self._last_focus
        focusable_indices = [i[0] for i in self._focusable_children_indices if i[1] == last_y]
        
        if not focusable_indices:
            raise FocusException("No focusable children in this row")
        
        for ind, i in enumerate(focusable_indices):
            if i >= last_x:
                base_index = ind
                break
        else:
            base_index = (-1) % len(focusable_indices)
        
        if not self.active:
            self._last_focus = focusable_indices[base_index], last_y
            focus(self.widgets[last_y][focusable_indices[base_index]])
        else:
            base_index -= amount
            if self.cyclic_horizontal:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
            
            unfocus(self.widgets[self._last_focus[1]][self._last_focus[0]])
            self._last_focus = focusable_indices[base_index], last_y
            focus(self.widgets[last_y][focusable_indices[base_index]])
    
    def move_focus_right(self, amount: int = 1) -> None:
        last_x, last_y = self._last_focus
        focusable_indices = [i[0] for i in self._focusable_children_indices if i[1] == last_y]

        if not focusable_indices:
            raise FocusException("No focusable children in this row")
        
        for ind, i in enumerate(focusable_indices[::-1], 1):
            if i <= last_x:
                base_index = len(focusable_indices) - ind
                break
        else:
            base_index = 0
        
        if not self.active:
            self._last_focus = focusable_indices[base_index], last_y
            focus(self.widgets[last_y][focusable_indices[base_index]])
        else:
            base_index += amount
            if self.cyclic_horizontal:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
            
            unfocus(self.widgets[self._last_focus[1]][self._last_focus[0]])
            self._last_focus = focusable_indices[base_index], last_y
            focus(self.widgets[last_y][focusable_indices[base_index]])
    
    def move_focus_up(self, amount: int = 1) -> None:
        last_x, last_y = self._last_focus
        focusable_indices = [i[1] for i in self._focusable_children_indices if i[0] == last_x]
        
        if not focusable_indices:
            raise FocusException("No focusable children in this column")
        
        for ind, i in enumerate(focusable_indices):
            if i >= last_y:
                base_index = ind
                break
        else:
            base_index = (-1) % len(focusable_indices)
        
        if not self.active:
            self._last_focus = last_x, focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]][last_x])
        else:
            base_index -= amount
            if self.cyclic_vertical:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
            
            unfocus(self.widgets[self._last_focus[1]][self._last_focus[0]])
            self._last_focus = last_x, focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]][last_x])
    
    def move_focus_down(self, amount: int = 1) -> None:
        last_x, last_y = self._last_focus
        focusable_indices = [i[1] for i in self._focusable_children_indices if i[0] == last_x]

        if not focusable_indices:
            raise FocusException("No focusable children in this column")
        
        for ind, i in enumerate(focusable_indices[::-1], 1):
            if i <= last_y:
                base_index = len(focusable_indices) - ind
                break
        else:
            base_index = 0
        
        if not self.active:
            self._last_focus = last_x, focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]][last_x])
        else:
            base_index += amount
            if self.cyclic_vertical:
                base_index %= len(focusable_indices)
            elif base_index < 0:
                base_index = 0
            elif base_index >= len(focusable_indices):
                base_index = len(focusable_indices) - 1
            
            unfocus(self.widgets[self._last_focus[1]][self._last_focus[0]])
            self._last_focus = last_x, focusable_indices[base_index]
            focus(self.widgets[focusable_indices[base_index]][last_x])

    def _register_key_bindings(self, kb: KeyBindingsBase | None) -> KeyBindingsBase:
        if kb is None:
            kb = KeyBindings()
        
        default_bindings = KeyBindings()
        
        # horizontal
        @Condition
        def left_filter() -> bool:
            last_x, last_y = self._last_focus
            fc = [i[0] for i in self._focusable_children_indices if i[1] == last_y]
            if fc:
                if self.cyclic_horizontal:
                    return True
                if last_x > fc[0]:
                    return True
            return False

        @Condition
        def right_filter() -> bool:
            last_x, last_y = self._last_focus
            fc = [i[0] for i in self._focusable_children_indices if i[1] == last_y]
            if fc:
                if self.cyclic_horizontal:
                    return True
                if last_x < fc[-1]:
                    return True
            return False
        
        @Condition
        def shift_point_filter() -> bool:
            return self.shift_point
        
        @default_bindings.add("left", filter=left_filter & self.left_filter)
        def _(event: KeyPressEvent):
            self.move_focus_left()
        
        @default_bindings.add("right", filter=right_filter & self.right_filter)
        def _(event: KeyPressEvent):
            self.move_focus_right()
        

        @default_bindings.add("s-left", filter=left_filter & self.left_filter & shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_left()
        
        @default_bindings.add("s-right", filter=right_filter & self.right_filter & shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_right()
            
        # Vertical
        @Condition
        def up_filter() -> bool:
            last_x, last_y = self._last_focus
            fc = [i[1] for i in self._focusable_children_indices if i[0] == last_x]
            if fc:
                if self.cyclic_vertical:
                    return True
                if last_y > fc[0]:
                    return True
            return False

        @Condition
        def down_filter() -> bool:
            last_x, last_y = self._last_focus
            fc = [i[1] for i in self._focusable_children_indices if i[0] == last_x]
            if fc:
                if self.cyclic_vertical:
                    return True
                if last_y < fc[-1]:
                    return True
            return False
        
        @default_bindings.add("up", filter=up_filter & self.up_filter)
        def _(event: KeyPressEvent):
            self.move_focus_up()
        
        @default_bindings.add("down", filter=down_filter & self.down_filter)
        def _(event: KeyPressEvent):
            self.move_focus_down()
        

        @default_bindings.add("s-up", filter=up_filter & self.up_filter & shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_up()
        
        @default_bindings.add("s-down", filter=down_filter & self.down_filter & shift_point_filter)
        def _(event: KeyPressEvent):
            self.move_focus_down()
        
        return merge_key_bindings([kb, default_bindings])

    