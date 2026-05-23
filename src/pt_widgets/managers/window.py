from enum import Enum
from typing import Callable

from prompt_toolkit.layout import AnyContainer, Container, to_container, Dimension
from prompt_toolkit.layout.screen import WritePosition, Screen
from prompt_toolkit.layout.mouse_handlers import MouseHandlers
from prompt_toolkit.key_binding import KeyBindingsBase

from pt_widgets.layout.navigation import is_focusable, focus, unfocus
from pt_widgets.layout.containers import get_horizontal_write_positions, get_vertical_write_positions


class WindowManager[StateT: Enum](Container):
    def __init__(
        self,
        initial_state: StateT,
        valid_transitions: dict[StateT, list[StateT]],
    ):
        self.windows: dict[StateT, AnyContainer] = {}
        self._state = initial_state
        self._transitions = valid_transitions
    
    @property
    def current_state(self) -> StateT:
        return self._state
    
    def switch_to(self, new_state: StateT) -> None:
        allowed_states = self._transitions.get(self._state, [])
        
        if new_state not in allowed_states:
            raise ValueError(f"Invalid transition from {self._state} to {new_state}")
            
        unfocus(self.current_window)
        self._state = new_state
        focus(self.current_window)


    @property
    def current_window(self) -> AnyContainer:
        return self.windows[self._state]

    def _get_container(self) -> Container:
        return to_container(self.current_window)

    # Container implementation
    def reset(self) -> None:
        self._get_container().reset()

    def preferred_width(self, max_available_width: int) -> Dimension:
        return self._get_container().preferred_width(max_available_width)

    def preferred_height(self, width: int, max_available_height: int) -> Dimension:
        return self._get_container().preferred_height(width, max_available_height)

    def write_to_screen(
        self,
        screen: Screen,
        mouse_handlers: MouseHandlers,
        write_position: WritePosition,
        parent_style: str,
        erase_bg: bool,
        z_index: int | None,
    ) -> None:
        self._get_container().write_to_screen(
            screen, mouse_handlers, write_position, parent_style, erase_bg, z_index
        )

    def is_modal(self) -> bool:
        return self._get_container().is_modal()

    def get_key_bindings(self) -> KeyBindingsBase | None:
        return None

    def get_children(self) -> list[Container]:
        return [self._get_container()]

    # WidgetContainer protocol
    def get_horizontal_write_positions(
        self,
        write_position: WritePosition
    ) -> list[WritePosition] | None:
        return get_horizontal_write_positions(self.current_window, write_position)
    
    def get_vertical_write_positions(
        self,
        write_position: WritePosition
    ) -> list[WritePosition] | None:
        return get_vertical_write_positions(self.current_window, write_position)

    # Focusable
    def is_focusable(self) -> bool:
        return is_focusable(self.current_window)
    
    def focus(self) -> None:
        focus(self.current_window)
    
    def unfocus(self) -> None:
        unfocus(self.current_window)
    
    def register_window(self, state: StateT, window: AnyContainer) -> None:
        self.windows[state] = window
