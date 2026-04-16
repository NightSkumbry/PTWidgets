from functools import singledispatch
from abc import ABC, abstractmethod
from typing import Callable, Sequence, override

from prompt_toolkit.application.current import get_app
from prompt_toolkit.cache import SimpleCache
from prompt_toolkit.key_binding import KeyBindingsBase
from prompt_toolkit.layout import (
    AnyDimension,
    Dimension,
    HorizontalAlign,
    Window,
    max_layout_dimensions,
    sum_layout_dimensions,
    to_container,
    to_dimension,
)
from prompt_toolkit.layout.containers import (
    AnyContainer,
    Container,
    HSplit,
    VSplit,
    VerticalAlign,
    _window_too_small,
)
from prompt_toolkit.layout.screen import WritePosition, Screen
from prompt_toolkit.layout.mouse_handlers import MouseHandlers
from prompt_toolkit.utils import take_using_weights, to_str


class WidgetContainer(Container, ABC):
    def get_horizontal_write_positions(
        self,
        write_position: WritePosition
    ) -> list[WritePosition] | None:
        return [write_position]
    
    def get_vertical_write_positions(
        self,
        write_position: WritePosition
    ) -> list[WritePosition] | None:
        return [write_position]
    

def get_vertical_write_positions(container: Container,
    write_position: WritePosition
) -> list[WritePosition] | None:
    return _get_vertical_write_positions(to_container(container), write_position)

def get_horizontal_write_positions(container: Container,
    write_position: WritePosition
) -> list[WritePosition] | None:
    return _get_horizontal_write_positions(to_container(container), write_position)


@singledispatch
def _get_horizontal_write_positions(
    container: Container,
    write_position: WritePosition
) -> list[WritePosition] | None:
    return [write_position]

@singledispatch
def _get_vertical_write_positions(
    container: Container,
    write_position: WritePosition
) -> list[WritePosition] | None:
    return [write_position]


@_get_vertical_write_positions.register(WidgetContainer)
def _(
    container: WidgetContainer,
    write_position: WritePosition
) -> list[WritePosition] | None:
    return container.get_vertical_write_positions(write_position)

@_get_horizontal_write_positions.register(WidgetContainer)
def _(
    container: WidgetContainer,
    write_position: WritePosition
) -> list[WritePosition] | None:
    return container.get_horizontal_write_positions(write_position)


@_get_vertical_write_positions.register(HSplit)
def _(
    container: HSplit,
    write_position: WritePosition
) -> list[WritePosition] | None:
    sizes = container._divide_heights(write_position)
    if sizes is None:
        return None
    
    ypos = write_position.ypos
    xpos = write_position.xpos
    width = write_position.width
    
    all_children = container._all_children
    real_children = container.get_children()
    i = 0
    wp = []
    for s, c in zip(sizes, all_children):
        if i < len(real_children) and c == real_children[i]:
            i += 1
            wp.append(WritePosition(xpos, ypos, width, s))
        ypos += s
    
    return wp


@_get_horizontal_write_positions.register(VSplit)
def _(
    container: VSplit,
    write_position: WritePosition
) -> list[WritePosition] | None:
    sizes = container._divide_widths(write_position.width)
    if sizes is None:
        return None
    
    all_children = container._all_children
    
    heights = [
        child.preferred_height(width, write_position.height).preferred
        for width, child in zip(sizes, all_children)
    ]
    height = max(write_position.height, min(write_position.height, max(heights)))
    
    ypos = write_position.ypos
    xpos = write_position.xpos
    
    real_children = container.get_children()
    i = 0
    wp = []
    for s, c in zip(sizes, all_children):
        if i < len(real_children) and c == real_children[i]:
            i += 1
            wp.append(WritePosition(xpos, ypos, s, height))
        xpos += s

    return wp


class GridSplit(WidgetContainer):
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
    ) -> None:
        self.children = [[to_container(c) for c in row] for row in children]
        m = max(len(row) for row in self.children)
        for row in self.children:
            while len(row) < m:
                row.append(Window())
        
        self.window_too_small = window_too_small or _window_too_small()
        self.padding_width = padding_width
        self.padding_height = padding_height
        self.padding_char = padding_char
        self.padding_style = padding_style
        
        self.sizeY = len(self.children)
        self.sizeX = len(self.children[0]) if self.sizeY else 0

        self.width = width
        self.height = height
        self.z_index = z_index

        self.modal = modal
        self.key_bindings = key_bindings
        self.style = style

        self.vertical_align = vertical_align
        self.horizontal_align = horizontal_align

        self._children_cache: SimpleCache[tuple[tuple[Container, ...], ...], list[list[Container]]] = (
            SimpleCache(maxsize=1)
        )
        self._remaining_space_window = Window()  # Dummy window.

    def is_modal(self) -> bool:
        return self.modal

    def get_key_bindings(self) -> KeyBindingsBase | None:
        return self.key_bindings

    def get_children(self) -> list[Container]:
        res = []
        for row in self.children:
            res.extend(row)
        return res
    
    def get_children_grid(self) -> list[list[Container]]:
        return self.children

    def preferred_width(self, max_available_width: int) -> Dimension:
        if self.width is not None:
            return to_dimension(self.width)

        if not (self.sizeY and self.sizeX):
            return sum_layout_dimensions([])
        
        dimensions = []
        
        for column in range(self.sizeX):
            dimensions.append(max_layout_dimensions(
                [r[column].preferred_width(max_available_width) for r in self._all_children]
            ))

        return sum_layout_dimensions(dimensions)
        
    def preferred_height(self, width: int, max_available_height: int) -> Dimension:
        if self.height is not None:
            return to_dimension(self.height)
        
        if not (self.sizeY and self.sizeX):
            return sum_layout_dimensions([])
        
        dimensions = [
            max_layout_dimensions([c.preferred_height(width, max_available_height) for c in r])
            for r in self._all_children
        ]
        
        return sum_layout_dimensions(dimensions)

    def reset(self) -> None:
        for r in self.children:
            for c in r:
                c.reset()

    @property
    def _all_children(self) -> list[list[Container]]:
        """
        List of child objects, including padding.
        """

        def get() -> list[list[Container]]:
            result: list[list[Container]] = []
            
            # Padding Top.
            if self.vertical_align in (VerticalAlign.CENTER, VerticalAlign.BOTTOM):
                result.append([
                    Window(width=Dimension(preferred=0))
                    for _ in range(self.sizeX*2-1 +
                                   (self.horizontal_align in (HorizontalAlign.CENTER, HorizontalAlign.RIGHT)) +
                                   (self.horizontal_align in (HorizontalAlign.CENTER, HorizontalAlign.LEFT)))
                ])
            
            for row in self.children:
                buff: list[Container] = []
                
                # Padding Left.
                if self.horizontal_align in (HorizontalAlign.CENTER, HorizontalAlign.RIGHT):
                    buff.append(Window(width=Dimension(preferred=0)))
                
                # The children with padding.
                for child in row:
                    buff.append(child)
                    buff.append(
                        Window(
                            width=self.padding_width,
                            height=self.padding_height,
                            char=self.padding_char,
                            style=self.padding_style,
                        )
                    )
                if buff:
                    buff.pop()

                # Padding right.
                if self.horizontal_align in (HorizontalAlign.CENTER, HorizontalAlign.LEFT):
                    buff.append(Window(width=Dimension(preferred=0)))
                
                result.append(buff)
                
                result.append(
                    [Window(
                        height=self.padding_height,
                        width=self.padding_width,
                        char=self.padding_char,
                        style=self.padding_style,
                    ) for _ in range(self.sizeX*2-1 +
                                   (self.horizontal_align in (HorizontalAlign.CENTER, HorizontalAlign.RIGHT)) +
                                   (self.horizontal_align in (HorizontalAlign.CENTER, HorizontalAlign.LEFT)))]
                )
            
            if result:
                result.pop()
            
            # Padding bottom.
            if self.vertical_align in (VerticalAlign.CENTER, VerticalAlign.TOP):
                result.append([
                    Window(width=Dimension(preferred=0))
                    for _ in range(self.sizeX*2-1 +
                                   (self.horizontal_align in (HorizontalAlign.CENTER, HorizontalAlign.RIGHT)) +
                                   (self.horizontal_align in (HorizontalAlign.CENTER, HorizontalAlign.LEFT)))
                ])
            
            return result

        return self._children_cache.get(tuple(tuple(r) for r in self.children), get)

    def _divide_widths(self, width: int) -> list[int] | None:
        children = self._all_children

        if not children:
            return []
        
        # Calculate widths.
        dimensions = []
        for column in range(len(children[0])):
            dimensions.append(max_layout_dimensions(
                [r[column].preferred_width(width) for r in self._all_children]
            ))
        preferred_dimensions = [d.preferred for d in dimensions]
        
        # Sum dimensions
        sum_dimensions = sum_layout_dimensions(dimensions)

        # If there is not enough space for both.
        # Don't do anything.
        if sum_dimensions.min > width:
            return None
        
        # Find optimal sizes. (Start with minimal size, increase until we cover
        # the whole width.)
        sizes = [d.min for d in dimensions]

        child_generator = take_using_weights(
            items=list(range(len(dimensions))), weights=[d.weight for d in dimensions]
        )

        i = next(child_generator)

        # Increase until we meet at least the 'preferred' size.
        preferred_stop = min(width, sum_dimensions.preferred)

        while sum(sizes) < preferred_stop:
            if sizes[i] < preferred_dimensions[i]:
                sizes[i] += 1
            i = next(child_generator)

        # Increase until we use all the available space.
        max_dimensions = [d.max for d in dimensions]
        max_stop = min(width, sum_dimensions.max)

        while sum(sizes) < max_stop:
            if sizes[i] < max_dimensions[i]:
                sizes[i] += 1
            i = next(child_generator)

        return sizes

    def write_to_screen(
        self,
        screen: Screen,
        mouse_handlers: MouseHandlers,
        write_position: WritePosition,
        parent_style: str,
        erase_bg: bool,
        z_index: int | None,
    ) -> None:
        style = parent_style + " " + to_str(self.style)
        z_index = z_index if self.z_index is None else self.z_index
        
        sizesX = self._divide_widths(write_position.width)
        if sizesX is None:
            self.window_too_small.write_to_screen(
                screen, mouse_handlers, write_position, style, erase_bg, z_index
            )
            return
        
        sizesY = self._divide_heights(sizesX, write_position.height)
        if sizesY is None:
            self.window_too_small.write_to_screen(
                screen, mouse_handlers, write_position, style, erase_bg, z_index
            )
            return
        
        ypos = write_position.ypos
        
        for row, height in zip(self._all_children, sizesY):
            xpos = write_position.xpos
            
            for child, width in zip(row, sizesX):
                child.write_to_screen(
                    screen,
                    mouse_handlers,
                    WritePosition(xpos, ypos, width, height),
                    style,
                    erase_bg,
                    z_index,
                )
                xpos += width
                
            # Fill in the remaining space. This happens when a child control
            # refuses to take more space and we don't have any padding. Adding a
            # dummy child control for this (in `self._all_children`) is not
            # desired, because in some situations, it would take more space, even
            # when it's not required. This is required to apply the styling.
            remaining_width = write_position.xpos + write_position.width - xpos
            if remaining_width > 0:
                self._remaining_space_window.write_to_screen(
                    screen,
                    mouse_handlers,
                    WritePosition(xpos, ypos, remaining_width, height),
                    style,
                    erase_bg,
                    z_index,
                )
            
            ypos += height
        
        # Fill in the remaining space. This happens when a child control
        # refuses to take more space and we don't have any padding. Adding a
        # dummy child control for this (in `self._all_children`) is not
        # desired, because in some situations, it would take more space, even
        # when it's not required. This is required to apply the styling.
        remaining_height = write_position.ypos + write_position.height - ypos
        if remaining_height > 0:
            self._remaining_space_window.write_to_screen(
                screen,
                mouse_handlers,
                WritePosition(write_position.xpos, ypos, sum(sizesX), remaining_height),
                style,
                erase_bg,
                z_index,
            )
        

    def _divide_heights(self, widths: list[int], height: int) -> list[int] | None:
        if not self.children:
            return []
        
        # Calculate heights.
        dimensions = [
            max_layout_dimensions([c.preferred_height(width, height) for c, width in zip(r, widths)])
            for r in self._all_children
        ]
        
        # Sum dimensions
        sum_dimensions = sum_layout_dimensions(dimensions)

        # If there is not enough space for both.
        # Don't do anything.
        if sum_dimensions.min > height:
            return None

        # Find optimal sizes. (Start with minimal size, increase until we cover
        # the whole height.)
        sizes = [d.min for d in dimensions]

        child_generator = take_using_weights(
            items=list(range(len(dimensions))), weights=[d.weight for d in dimensions]
        )

        i = next(child_generator)

        # Increase until we meet at least the 'preferred' size.
        preferred_stop = min(height, sum_dimensions.preferred)
        preferred_dimensions = [d.preferred for d in dimensions]

        while sum(sizes) < preferred_stop:
            if sizes[i] < preferred_dimensions[i]:
                sizes[i] += 1
            i = next(child_generator)

        # Increase until we use all the available space. (or until "max")
        if not get_app().is_done:
            max_stop = min(height, sum_dimensions.max)
            max_dimensions = [d.max for d in dimensions]

            while sum(sizes) < max_stop:
                if sizes[i] < max_dimensions[i]:
                    sizes[i] += 1
                i = next(child_generator)

        return sizes
    
    @override
    def get_horizontal_write_positions(self, write_position: WritePosition) -> list[WritePosition] | None:
        sizesX = self._divide_widths(write_position.width)
        if not (self.sizeX and self.sizeY):
            return []
        
        if sizesX is None:
            return None
        
        sizesY = self._divide_heights(sizesX, write_position.height)
        if sizesY is None:
            return None
        
        ypos = write_position.ypos
        xpos = write_position.xpos
        real_children = self.get_children_grid()
        height = max(write_position.height, min(write_position.height, sum(sizesY)))
        
        res = []
        all_children = self._all_children
        
        i = 0
        for c, width in zip(all_children[0], sizesX):
            if i < len(real_children) and real_children[0] and c == real_children[0][i]:
                res.append(WritePosition(xpos, ypos, width, height))
                i += 1

            xpos += width
        
        return res
         

    @override
    def get_vertical_write_positions(self, write_position: WritePosition) -> list[WritePosition] | None:
        sizesX = self._divide_widths(write_position.width)
        if not (self.sizeX and self.sizeY):
            return []
        
        if sizesX is None:
            return None
        
        sizesY = self._divide_heights(sizesX, write_position.height)
        if sizesY is None:
            return None
        
        ypos = write_position.ypos
        xpos = write_position.xpos
        width = write_position.width
        
        all_children = self._all_children
        real_children = self.get_children_grid()
        i = 0
        wp = []
        for row, height in zip(all_children, sizesY):
            if i < len(real_children) and real_children[i] and row[0] == real_children[i][0]:
                wp.append(WritePosition(xpos, ypos, width, height))
                i += 1
            ypos += height
        
        return wp

