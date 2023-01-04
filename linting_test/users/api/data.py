import json
from typing import Union


def foo_bar() -> Union[int, None]:
    return True


try:
    foo_bar()
except ValueError or TypeError:
    pass


def read_file(path: str) -> str:
    f = open("bar.txt", "w")
    f.write("bar")


def read_json():
    with open("some/path.json") as f:
        content = json.loads(f.read())
    return content
