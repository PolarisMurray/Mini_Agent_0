---
name: python-dataclass
description: Use whenever writing or editing Python code that defines a class. Always use @dataclass instead of a hand-written __init__.
---

# Python classes: always @dataclass

## Core rule
Every class that holds data uses `@dataclass`. Never write `__init__` by hand.

```python
# Wrong
class User:
    def __init__(self, name, age=0):
        self.name = name
        self.age = age

# Right
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int = 0
```

## Checklist
1. `from dataclasses import dataclass, field`
2. Every field has a type hint.
3. Fields without defaults come before fields with defaults.
4. Mutable defaults (list, dict, set) use `field(default_factory=list)`, never `= []`.
5. Extra setup or validation goes in `__post_init__`, not `__init__`.

## More (load only when needed)
- Inheritance, frozen (immutable) classes, `slots` → `load_skill("python-dataclass", "reference/advanced.md")`
