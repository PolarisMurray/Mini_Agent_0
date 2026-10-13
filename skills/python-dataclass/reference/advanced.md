# Advanced dataclass cases

## Immutable object
```python
@dataclass(frozen=True)
class Point:
    x: float
    y: float
```

## Inheritance
Child fields are added after parent fields, so a parent field with a default
forces every child field to have a default too. Use `kw_only=True` to avoid this.
```python
@dataclass
class Animal:
    name: str
    sound: str = "..."

@dataclass(kw_only=True)
class Dog(Animal):
    breed: str
```

## Many small objects
`@dataclass(slots=True)` saves memory and blocks typo attributes.
