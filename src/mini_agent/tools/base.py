from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Tool:
    name: str
    description: str
    function: Callable[..., Any]

    def execute(self, arguments: dict[str, Any]) -> Any:
        return self.function(**arguments)
