from enum import Enum

from prompt_toolkit.layout import AnyContainer, Container, to_container

from pt_widgets.layout.navigation import is_focusable, focus, unfocus


class WindowManager[StateT: Enum]:
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
            
        self._state = new_state

    @property
    def current_window(self) -> AnyContainer:
        return self.windows[self._state]

    # Focusable
    def is_focusable(self) -> bool:
        return is_focusable(self.current_window)
    
    def focus(self) -> None:
        focus(self.current_window)
    
    def unfocus(self) -> None:
        unfocus(self.current_window)
    
    def register_window(self, state: StateT, window: AnyContainer) -> None:
        self.windows[state] = window

    # MagicContainer
    def __pt_container__(self) -> Container:
        return to_container(self.current_window)






