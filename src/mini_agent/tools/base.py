from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Tool:
    name: str
    description: str
    function: Callable[..., Any]
    read_only: bool = False  # read-only tools are allowed in plan mode

    def execute(self, arguments: dict[str, Any]) -> Any:
        return self.function(**arguments)
