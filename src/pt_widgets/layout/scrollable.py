from __future__ import annotations

from typing import Any

from prompt_toolkit.data_structures import Point
from prompt_toolkit.filters import FilterOrBool, to_filter
from prompt_toolkit.key_binding import KeyBindingsBase
from prompt_toolkit.layout import (
    AnyContainer,
    AnyDimension,
    Container,
    Dimension,
    sum_layout_dimensions,
    to_container,
    to_dimension,
)
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.mouse_handlers import MouseHandler, MouseHandlers
from prompt_toolkit.layout.screen import Char, Screen, WritePosition
from prompt_toolkit.mouse_events import MouseEvent

from pt_widgets.layout.containers import WidgetContainer, get_horizontal_write_positions, get_vertical_write_positions
from pt_widgets.layout.navigation import Focusable, Navigation, focus, is_focusable, unfocus
from pt_widgets.widgets.slider import Orientation, Scrollbar, ScrollbarA

__all__ = ["Scrollable"]

# Default max dimensions to prevent excessive memory usage if content is infinite.
MAX_AVAILABLE_HEIGHT = 10_000
MAX_AVAILABLE_WIDTH = 10_000


class Scrollable(Container, Navigation, Focusable, WidgetContainer):
    """
    A container that provides a scrollable view over its content.
    It implements the Navigation and Focusable protocols, delegating focus 
    logic to its inner content. 
    
    Scrolling occurs when the currently focused element moves out of the
    visible viewport.
    """

    def __init__(
        self,
        content: AnyContainer,
        keep_focused_visible: FilterOrBool = True,
        max_available_height: int = MAX_AVAILABLE_HEIGHT,
        max_available_width: int = MAX_AVAILABLE_WIDTH,
        width: AnyDimension = None,
        height: AnyDimension = None,
        scroll_vertical: FilterOrBool = True,
        scroll_horizontal: FilterOrBool = False,
        show_scrollbar_v: FilterOrBool = True,
        show_scrollbar_h: FilterOrBool = False,
        scrollbar_v: Scrollbar | None = None,
        scrollbar_h: Scrollbar | None = None,
    ) -> None:
        self.content = content
        self.keep_focused_visible = to_filter(keep_focused_visible)
        self.max_available_height = max_available_height
        self.max_available_width = max_available_width
        self.width = width
        self.height = height

        self.scroll_vertical = to_filter(scroll_vertical)
        self.scroll_horizontal = to_filter(scroll_horizontal)
        self.show_scrollbar_v = to_filter(show_scrollbar_v)
        self.show_scrollbar_h = to_filter(show_scrollbar_h)

        self.vertical_scroll = 0
        self.horizontal_scroll = 0

        # Use the ScrollbarA preset from widgets/slider by default.
        self.scrollbar_v = scrollbar_v or ScrollbarA(orientation=Orientation.VERTICAL, width=1)
        self.scrollbar_h = scrollbar_h or ScrollbarA(orientation=Orientation.HORIZONTAL, height=1)

    def __repr__(self) -> str:
        return f"Scrollable({self.content!r})"

    def reset(self) -> None:
        to_container(self.content).reset()

    # --- Container API ---
    def preferred_width(self, max_available_width: int) -> Dimension:
        if self.width is not None:
            return to_dimension(self.width)

        content_width = to_container(self.content).preferred_width(max_available_width)
        
        res = content_width
        if self.scroll_horizontal():
            res = Dimension(min=0, preferred=content_width.preferred)
            
        if self.scroll_vertical() and self.show_scrollbar_v():
            return sum_layout_dimensions([Dimension.exact(1), res])

        return res

    def preferred_height(self, width: int, max_available_height: int) -> Dimension:
        if self.height is not None:
            return to_dimension(self.height)

        if self.scroll_vertical() and self.show_scrollbar_v():
            width = max(0, width - 1)

        dimension = to_container(self.content).preferred_height(width, self.max_available_height)
        
        res = dimension
        if self.scroll_vertical():
            res = Dimension(min=0, preferred=dimension.preferred)

        if self.scroll_horizontal() and self.show_scrollbar_h():
            return sum_layout_dimensions([Dimension.exact(1), res])

        return res

    def get_children(self) -> list[Container]:
        return [to_container(self.content)]

    def is_modal(self) -> bool:
        return to_container(self.content).is_modal()

    def get_key_bindings(self) -> KeyBindingsBase | None:
        return to_container(self.content).get_key_bindings()

    # --- Focusable & Navigation API ---
    def is_focusable(self) -> bool:
        return is_focusable(self.content)

    def focus(self) -> None:
        focus(self.content)

    def unfocus(self) -> None:
        unfocus(self.content)

    def get_focused_container(self) -> AnyContainer:
        if isinstance(self.content, Navigation):
            return self.content.get_focused_container()
        return self.content

    # --- WidgetContainer API ---
    def get_horizontal_write_positions(self, write_position: WritePosition) -> list[WritePosition] | None:
        show_v = self.scroll_vertical() and self.show_scrollbar_v()
        show_h = self.scroll_horizontal() and self.show_scrollbar_h()
        
        viewport_width = write_position.width - (1 if show_v else 0)
        viewport_height = write_position.height - (1 if show_h else 0)
        
        temp_wpos = WritePosition(
            xpos=write_position.xpos,
            ypos=write_position.ypos,
            width=viewport_width,
            height=viewport_height
        )
        positions = get_horizontal_write_positions(self.content, temp_wpos)
        if positions is None:
            return None
        
        res = []
        for p in positions:
            nx = p.xpos - self.horizontal_scroll
            # Keep if it overlaps the visible region on the X axis
            if nx + p.width > write_position.xpos and nx < write_position.xpos + viewport_width:
                res.append(WritePosition(nx, p.ypos, p.width, p.height))
        return res

    def get_vertical_write_positions(self, write_position: WritePosition) -> list[WritePosition] | None:
        show_v = self.scroll_vertical() and self.show_scrollbar_v()
        show_h = self.scroll_horizontal() and self.show_scrollbar_h()
        
        viewport_width = write_position.width - (1 if show_v else 0)
        viewport_height = write_position.height - (1 if show_h else 0)
        
        temp_wpos = WritePosition(
            xpos=write_position.xpos,
            ypos=write_position.ypos,
            width=viewport_width,
            height=viewport_height
        )
        positions = get_vertical_write_positions(self.content, temp_wpos)
        if positions is None:
            return None
            
        res = []
        for p in positions:
            ny = p.ypos - self.vertical_scroll
            # Keep if it overlaps the visible region on the Y axis
            if ny + p.height > write_position.ypos and ny < write_position.ypos + viewport_height:
                res.append(WritePosition(p.xpos, ny, p.width, p.height))
        return res

    # --- Core Rendering ---
    def _get_bounding_box(self, container: AnyContainer, temp_screen: Screen) -> tuple[int, int, int, int] | None:
        """Find the min and max X/Y position of all windows within a container on the virtual screen."""
        min_y = float('inf')
        max_y = -1
        min_x = float('inf')
        max_x = -1
        
        def walk(c: AnyContainer) -> None:
            nonlocal min_y, max_y, min_x, max_x
            c_cont = to_container(c)
            
            # If this part of the container tree is a Window that was drawn
            if isinstance(c_cont, Window) and c_cont in temp_screen.visible_windows_to_write_positions:
                pos = temp_screen.visible_windows_to_write_positions[c_cont]
                min_y = min(min_y, pos.ypos)
                max_y = max(max_y, pos.ypos + pos.height)
                min_x = min(min_x, pos.xpos)
                max_x = max(max_x, pos.xpos + pos.width)
            
            # Recursively walk the layout tree
            if hasattr(c, "get_children"):
                for child in getattr(c, "get_children")():
                    walk(child)
            elif hasattr(c_cont, "get_children"):
                for child in c_cont.get_children():
                    walk(child)
                    
        walk(container)
        if min_y != float('inf'):
            return int(min_x), int(max_x), int(min_y), int(max_y)
        return None

    def write_to_screen(
        self,
        screen: Screen,
        mouse_handlers: MouseHandlers,
        write_position: WritePosition,
        parent_style: str,
        erase_bg: bool,
        z_index: int | None,
    ) -> None:
        show_v = self.scroll_vertical() and self.show_scrollbar_v()
        show_h = self.scroll_horizontal() and self.show_scrollbar_h()
        
        viewport_width = write_position.width - (1 if show_v else 0)
        viewport_height = write_position.height - (1 if show_h else 0)

        # Determine virtual dimensions based on content's preferred size
        cont = to_container(self.content)
        virtual_width = cont.preferred_width(self.max_available_width).preferred
        virtual_width = max(virtual_width, viewport_width)
        virtual_width = min(virtual_width, self.max_available_width)
        
        virtual_height = cont.preferred_height(virtual_width, self.max_available_height).preferred
        virtual_height = max(virtual_height, viewport_height)
        virtual_height = min(virtual_height, self.max_available_height)

        # 1. Create a virtual screen and render the content onto it at (0,0)
        temp_screen = Screen(default_char=Char(char=" ", style=parent_style))
        temp_screen.show_cursor = screen.show_cursor
        temp_write_position = WritePosition(
            xpos=0, ypos=0, width=virtual_width, height=virtual_height
        )
        temp_mouse_handlers = MouseHandlers()

        cont.write_to_screen(
            temp_screen,
            temp_mouse_handlers,
            temp_write_position,
            parent_style,
            erase_bg,
            z_index,
        )
        temp_screen.draw_all_floats()

        # 2. Update scroll if focused element moved out of bounds
        if self.keep_focused_visible():
            focused_container = self.get_focused_container()
            bounding_box = self._get_bounding_box(focused_container, temp_screen)
            
            if bounding_box:
                min_x, max_x, min_y, max_y = bounding_box
                
                # Vertical scrolling
                if self.scroll_vertical():
                    element_height = max_y - min_y
                    if element_height >= viewport_height:
                        target_min_scroll_y = min_y
                        target_max_scroll_y = min_y
                    else:
                        target_min_scroll_y = max_y - viewport_height
                        target_max_scroll_y = min_y
                        
                    if self.vertical_scroll < target_min_scroll_y:
                        self.vertical_scroll = target_min_scroll_y
                    elif self.vertical_scroll > target_max_scroll_y:
                        self.vertical_scroll = target_max_scroll_y

                # Horizontal scrolling
                if self.scroll_horizontal():
                    element_width = max_x - min_x
                    if element_width >= viewport_width:
                        target_min_scroll_x = min_x
                        target_max_scroll_x = min_x
                    else:
                        target_min_scroll_x = max_x - viewport_width
                        target_max_scroll_x = min_x
                        
                    if self.horizontal_scroll < target_min_scroll_x:
                        self.horizontal_scroll = target_min_scroll_x
                    elif self.horizontal_scroll > target_max_scroll_x:
                        self.horizontal_scroll = target_max_scroll_x

        # Ensure scroll is within global bounds
        if self.scroll_vertical():
            max_scroll_limit_y = max(0, virtual_height - viewport_height)
            self.vertical_scroll = max(0, min(self.vertical_scroll, max_scroll_limit_y))
        else:
            self.vertical_scroll = 0
            
        if self.scroll_horizontal():
            max_scroll_limit_x = max(0, virtual_width - viewport_width)
            self.horizontal_scroll = max(0, min(self.horizontal_scroll, max_scroll_limit_x))
        else:
            self.horizontal_scroll = 0

        # 3. Copy the visible portion of the virtual screen to the real screen
        self._copy_over_screen(screen, temp_screen, write_position, viewport_width, viewport_height)
        self._copy_over_mouse_handlers(mouse_handlers, temp_mouse_handlers, write_position, viewport_width, viewport_height)
        self._copy_over_write_positions(screen, temp_screen, write_position)

        # Update screen dimensions
        screen.width = max(screen.width, write_position.xpos + viewport_width)
        screen.height = max(screen.height, write_position.ypos + viewport_height)

        if temp_screen.show_cursor:
            screen.show_cursor = True

        # Map virtual cursor positions to real screen coordinates
        for window, point in temp_screen.cursor_positions.items():
            if (
                self.horizontal_scroll <= point.x < viewport_width + self.horizontal_scroll
                and self.vertical_scroll <= point.y < viewport_height + self.vertical_scroll
            ):
                screen.cursor_positions[window] = Point(
                    x=point.x + write_position.xpos - self.horizontal_scroll, 
                    y=point.y + write_position.ypos - self.vertical_scroll
                )

        # Map virtual menu positions
        for window, point in temp_screen.menu_positions.items():
            screen.menu_positions[window] = self._clip_point_to_visible_area(
                Point(
                    x=point.x + write_position.xpos - self.horizontal_scroll, 
                    y=point.y + write_position.ypos - self.vertical_scroll
                ),
                write_position,
                viewport_width,
                viewport_height
            )

        # 4. Draw Scrollbars
        if show_v:
            self.scrollbar_v.update_state(self.vertical_scroll, virtual_height, viewport_height)
            sb_v_pos = WritePosition(
                xpos=write_position.xpos + viewport_width,
                ypos=write_position.ypos,
                width=1,
                height=viewport_height
            )
            to_container(self.scrollbar_v).write_to_screen(
                screen, mouse_handlers, sb_v_pos, parent_style, erase_bg, z_index
            )
            
        if show_h:
            self.scrollbar_h.update_state(self.horizontal_scroll, virtual_width, viewport_width)
            sb_h_pos = WritePosition(
                xpos=write_position.xpos,
                ypos=write_position.ypos + viewport_height,
                width=viewport_width,
                height=1
            )
            to_container(self.scrollbar_h).write_to_screen(
                screen, mouse_handlers, sb_h_pos, parent_style, erase_bg, z_index
            )
            
        if show_v and show_h:
            screen.data_buffer[write_position.ypos + viewport_height][write_position.xpos + viewport_width] = Char(char=" ", style=parent_style)

    def _clip_point_to_visible_area(self, point: Point, write_position: WritePosition, viewport_width: int, viewport_height: int) -> Point:
        if point.x < write_position.xpos:
            point = point._replace(x=write_position.xpos)
        if point.y < write_position.ypos:
            point = point._replace(y=write_position.ypos)
        if point.x >= write_position.xpos + viewport_width:
            point = point._replace(x=write_position.xpos + viewport_width - 1)
        if point.y >= write_position.ypos + viewport_height:
            point = point._replace(y=write_position.ypos + viewport_height - 1)
        return point

    def _copy_over_screen(
        self,
        screen: Screen,
        temp_screen: Screen,
        write_position: WritePosition,
        viewport_width: int,
        viewport_height: int,
    ) -> None:
        ypos = write_position.ypos
        xpos = write_position.xpos

        for y in range(viewport_height):
            temp_row = temp_screen.data_buffer[y + self.vertical_scroll]
            row = screen.data_buffer[y + ypos]
            temp_zero_width_escapes = temp_screen.zero_width_escapes[y + self.vertical_scroll]
            zero_width_escapes = screen.zero_width_escapes[y + ypos]

            for x in range(viewport_width):
                row[x + xpos] = temp_row[x + self.horizontal_scroll]
                if (x + self.horizontal_scroll) in temp_zero_width_escapes:
                    zero_width_escapes[x + xpos] = temp_zero_width_escapes[x + self.horizontal_scroll]

    def _copy_over_mouse_handlers(
        self,
        mouse_handlers: MouseHandlers,
        temp_mouse_handlers: MouseHandlers,
        write_position: WritePosition,
        viewport_width: int,
        viewport_height: int,
    ) -> None:
        ypos = write_position.ypos
        xpos = write_position.xpos

        mouse_handler_wrappers: dict[MouseHandler, MouseHandler] = {}

        def wrap_mouse_handler(handler: MouseHandler) -> MouseHandler:
            if handler not in mouse_handler_wrappers:
                def new_handler(event: MouseEvent) -> None:
                    new_event = MouseEvent(
                        position=Point(
                            x=event.position.x - xpos + self.horizontal_scroll,
                            y=event.position.y - ypos + self.vertical_scroll,
                        ),
                        event_type=event.event_type,
                        button=event.button,
                        modifiers=event.modifiers,
                    )
                    handler(new_event)
                mouse_handler_wrappers[handler] = new_handler
            return mouse_handler_wrappers[handler]

        mouse_handlers_dict = mouse_handlers.mouse_handlers
        temp_mouse_handlers_dict = temp_mouse_handlers.mouse_handlers

        for y in range(viewport_height):
            # Check if this row exists in virtual screen's mouse handlers
            if y + self.vertical_scroll in temp_mouse_handlers_dict:
                temp_mouse_row = temp_mouse_handlers_dict[y + self.vertical_scroll]
                mouse_row = mouse_handlers_dict[y + ypos]
                for x in range(viewport_width):
                    if (x + self.horizontal_scroll) in temp_mouse_row:
                        mouse_row[x + xpos] = wrap_mouse_handler(temp_mouse_row[x + self.horizontal_scroll])

    def _copy_over_write_positions(
        self, screen: Screen, temp_screen: Screen, write_position: WritePosition
    ) -> None:
        ypos = write_position.ypos
        xpos = write_position.xpos

        for win, write_pos in temp_screen.visible_windows_to_write_positions.items():
            screen.visible_windows_to_write_positions[win] = WritePosition(
                xpos=write_pos.xpos + xpos - self.horizontal_scroll,
                ypos=write_pos.ypos + ypos - self.vertical_scroll,
                height=write_pos.height,
                width=write_pos.width,
            )

