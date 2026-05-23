from __future__ import annotations

from typing import Any

from prompt_toolkit.application import get_app
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
        min_items_padding: int = 0,
        min_chars_padding: int = 0,
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

        self.min_items_padding = min_items_padding
        self.min_chars_padding = min_chars_padding

        self.vertical_scroll: int = 0
        self.horizontal_scroll: int = 0

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
        if write_position.width <= 0 or write_position.height <= 0:
            return

        cont = to_container(self.content)
        
        # Determine if scrollbars are needed (Auto-hide logic)
        # First pass: assume no scrollbars to get max viewport
        vp_w_no_bars = write_position.width
        vp_h_no_bars = write_position.height
        
        v_width_no_bars = cont.preferred_width(self.max_available_width).preferred
        v_height_no_bars = cont.preferred_height(
            v_width_no_bars if self.scroll_horizontal() else vp_w_no_bars, 
            self.max_available_height
        ).preferred

        show_v = self.scroll_vertical() and self.show_scrollbar_v() and v_height_no_bars > vp_h_no_bars
        show_h = self.scroll_horizontal() and self.show_scrollbar_h() and v_width_no_bars > vp_w_no_bars
        
        # Re-check vertical if horizontal scrollbar added more height pressure
        if not show_v and self.scroll_vertical() and self.show_scrollbar_v() and show_h:
            v_height_with_h_bar = cont.preferred_height(
                v_width_no_bars if self.scroll_horizontal() else vp_w_no_bars, 
                self.max_available_height
            ).preferred
            if v_height_with_h_bar > (write_position.height - 1):
                show_v = True
                
        # Re-check horizontal if vertical scrollbar added more width pressure
        if not show_h and self.scroll_horizontal() and self.show_scrollbar_h() and show_v:
            v_width_with_v_bar = cont.preferred_width(self.max_available_width).preferred
            if v_width_with_v_bar > (write_position.width - 1):
                show_h = True

        viewport_width = write_position.width - (1 if show_v else 0)
        viewport_height = write_position.height - (1 if show_h else 0)

        if viewport_width <= 0 or viewport_height <= 0:
            return

        # 3. Final virtual dimensions based on actual viewport and unconstrained max values
        v_width = cont.preferred_width(self.max_available_width).preferred
        v_height = cont.preferred_height(
            v_width if self.scroll_horizontal() else viewport_width, 
            self.max_available_height
        ).preferred
        
        virtual_width = max(v_width, viewport_width)
        virtual_height = max(v_height, viewport_height)

        # 4. Render content to virtual screen
        temp_screen = Screen(default_char=Char(char=" ", style=parent_style))
        temp_screen.show_cursor = screen.show_cursor
        temp_write_position = WritePosition(xpos=0, ypos=0, width=virtual_width, height=virtual_height)
        temp_mouse_handlers = MouseHandlers()

        cont.write_to_screen(temp_screen, temp_mouse_handlers, temp_write_position, parent_style, erase_bg, z_index)
        temp_screen.draw_all_floats()

        # 5. Focus tracking and scroll update
        if self.keep_focused_visible():
            cursor_pos = None
            if temp_screen.show_cursor and temp_screen.cursor_positions:
                try:
                    focused_window = get_app().layout.current_window
                    if focused_window in temp_screen.cursor_positions:
                        cursor_pos = temp_screen.cursor_positions[focused_window]
                    elif temp_screen.cursor_positions:
                        cursor_pos = list(temp_screen.cursor_positions.values())[0]
                except Exception:
                    # Fallback if get_app() fails (e.g. during test init without app running)
                    cursor_pos = list(temp_screen.cursor_positions.values())[0] if temp_screen.cursor_positions else None

            focused_container = self.get_focused_container()
            bounding_box = self._get_bounding_box(focused_container, temp_screen)

            if cursor_pos or bounding_box:
                v_pos = get_vertical_write_positions(self.content, temp_write_position)
                h_pos = get_horizontal_write_positions(self.content, temp_write_position)

                # Vertical scroll update
                if self.scroll_vertical():
                    # Determine target range to keep visible
                    ty_min: int | None = None
                    ty_max: int | None = None
                    
                    if cursor_pos:
                        ty_min, ty_max = cursor_pos.y, cursor_pos.y + 1
                    elif bounding_box:
                        _, _, ty_min, ty_max = bounding_box
                    
                    if ty_min is not None and ty_max is not None:
                        target_y_min: int = ty_min
                        target_y_max: int = ty_max

                        # Find focused item index in vertical positions
                        focused_v_idx = -1
                        if v_pos:
                            center_y = (target_y_min + target_y_max) // 2
                            for idx, p in enumerate(v_pos):
                                if p.ypos <= center_y < p.ypos + p.height:
                                    focused_v_idx = idx
                                    break
                        
                        if focused_v_idx != -1 and v_pos is not None:
                            # Apply padding
                            pad_start_idx = max(0, focused_v_idx - self.min_items_padding)
                            pad_end_idx = min(len(v_pos) - 1, focused_v_idx + self.min_items_padding)
                            
                            target_y_min = v_pos[pad_start_idx].ypos - self.min_chars_padding
                            target_y_max = v_pos[pad_end_idx].ypos + v_pos[pad_end_idx].height + self.min_chars_padding
                        else:
                            # Fallback to simple char padding if items not found
                            target_y_min -= self.min_chars_padding
                            target_y_max += self.min_chars_padding

                        target_height = target_y_max - target_y_min
                        
                        if target_height <= viewport_height:
                            # Range fits in viewport
                            if self.vertical_scroll > target_y_min:
                                self.vertical_scroll = target_y_min
                            if self.vertical_scroll < target_y_max - viewport_height:
                                self.vertical_scroll = target_y_max - viewport_height
                        else:
                            # Range too large, center focused element
                            focused_elem_center: int = (target_y_min + target_y_max) // 2
                            if focused_v_idx != -1 and v_pos:
                                p = v_pos[focused_v_idx]
                                focused_elem_center = p.ypos + p.height // 2
                            
                            self.vertical_scroll = focused_elem_center - viewport_height // 2
                            
                            # Ensure cursor (if any) or focused area is still visible
                            if cursor_pos:
                                self.vertical_scroll = max(self.vertical_scroll, cursor_pos.y - viewport_height + 1)
                                self.vertical_scroll = min(self.vertical_scroll, cursor_pos.y)
                            elif bounding_box:
                                _, _, b_min_y, b_max_y = bounding_box
                                if b_max_y - b_min_y <= viewport_height:
                                    self.vertical_scroll = max(self.vertical_scroll, b_max_y - viewport_height)
                                    self.vertical_scroll = min(self.vertical_scroll, b_min_y)

                # Horizontal scroll update
                if self.scroll_horizontal():
                    tx_min: int | None = None
                    tx_max: int | None = None
                    
                    if cursor_pos:
                        tx_min, tx_max = cursor_pos.x, cursor_pos.x + 1
                    elif bounding_box:
                        tx_min, tx_max, _, _ = bounding_box
                    
                    if tx_min is not None and tx_max is not None:
                        target_x_min: int = tx_min
                        target_x_max: int = tx_max

                        # Find focused item index in horizontal positions
                        focused_h_idx = -1
                        if h_pos:
                            center_x = (target_x_min + target_x_max) // 2
                            for idx, p in enumerate(h_pos):
                                if p.xpos <= center_x < p.xpos + p.width:
                                    focused_h_idx = idx
                                    break
                        
                        if focused_h_idx != -1 and h_pos:
                            pad_start_idx = max(0, focused_h_idx - self.min_items_padding)
                            pad_end_idx = min(len(h_pos) - 1, focused_h_idx + self.min_items_padding)
                            
                            target_x_min = h_pos[pad_start_idx].xpos - self.min_chars_padding
                            target_x_max = h_pos[pad_end_idx].xpos + h_pos[pad_end_idx].width + self.min_chars_padding
                        else:
                            target_x_min -= self.min_chars_padding
                            target_x_max += self.min_chars_padding

                        target_width = target_x_max - target_x_min
                        
                        if target_width <= viewport_width:
                            if self.horizontal_scroll > target_x_min:
                                self.horizontal_scroll = target_x_min
                            if self.horizontal_scroll < target_x_max - viewport_width:
                                self.horizontal_scroll = target_x_max - viewport_width
                        else:
                            focused_elem_center = (target_x_min + target_x_max) // 2
                            if focused_h_idx != -1 and h_pos:
                                p = h_pos[focused_h_idx]
                                focused_elem_center = p.xpos + p.width // 2
                                
                            self.horizontal_scroll = focused_elem_center - viewport_width // 2
                            
                            if cursor_pos:
                                self.horizontal_scroll = max(self.horizontal_scroll, cursor_pos.x - viewport_width + 1)
                                self.horizontal_scroll = min(self.horizontal_scroll, cursor_pos.x)
                            elif bounding_box:
                                b_min_x, b_max_x, _, _ = bounding_box
                                if b_max_x - b_min_x <= viewport_width:
                                    self.horizontal_scroll = max(self.horizontal_scroll, b_max_x - viewport_width)
                                    self.horizontal_scroll = min(self.horizontal_scroll, b_min_x)

        # Final bounds check
        self.vertical_scroll = int(max(0, min(self.vertical_scroll, virtual_height - viewport_height)))
        self.horizontal_scroll = int(max(0, min(self.horizontal_scroll, virtual_width - viewport_width)))

        # 6. Copy visible area
        self._copy_over_screen(screen, temp_screen, write_position, viewport_width, viewport_height)
        self._copy_over_mouse_handlers(mouse_handlers, temp_mouse_handlers, write_position, viewport_width, viewport_height)
        self._copy_over_write_positions(screen, temp_screen, write_position)

        # Cursors and menus
        if temp_screen.show_cursor:
            screen.show_cursor = True
        for window, point in temp_screen.cursor_positions.items():
            if (self.horizontal_scroll <= point.x < viewport_width + self.horizontal_scroll and
                self.vertical_scroll <= point.y < viewport_height + self.vertical_scroll):
                screen.cursor_positions[window] = Point(
                    x=point.x + write_position.xpos - self.horizontal_scroll, 
                    y=point.y + write_position.ypos - self.vertical_scroll
                )
        for window, point in temp_screen.menu_positions.items():
            screen.menu_positions[window] = self._clip_point_to_visible_area(
                Point(x=point.x + write_position.xpos - self.horizontal_scroll, 
                      y=point.y + write_position.ypos - self.vertical_scroll),
                write_position, viewport_width, viewport_height
            )

        # 7. Draw Scrollbars
        if show_v:
            self.scrollbar_v.update_state(self.vertical_scroll, virtual_height, viewport_height, length=viewport_height)
            sb_v_pos = WritePosition(xpos=write_position.xpos + viewport_width, ypos=write_position.ypos, width=1, height=viewport_height)
            to_container(self.scrollbar_v).write_to_screen(screen, mouse_handlers, sb_v_pos, parent_style, erase_bg, z_index)
            
        if show_h:
            self.scrollbar_h.update_state(self.horizontal_scroll, virtual_width, viewport_width, length=viewport_width)
            sb_h_pos = WritePosition(xpos=write_position.xpos, ypos=write_position.ypos + viewport_height, width=viewport_width, height=1)
            to_container(self.scrollbar_h).write_to_screen(screen, mouse_handlers, sb_h_pos, parent_style, erase_bg, z_index)
            
        if show_v and show_h:
            screen.data_buffer[write_position.ypos + viewport_height][write_position.xpos + viewport_width] = Char(char=" ", style=parent_style)

        screen.width = max(screen.width, write_position.xpos + write_position.width)
        screen.height = max(screen.height, write_position.ypos + write_position.height)

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
