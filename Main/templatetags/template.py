import re
from django import forms, template # type: ignore
from typing import Any, NamedTuple
from datetime import datetime
from tools.utils import tryCatchThis

class Image(NamedTuple):
    img: str


register = template.Library()


@register.filter(name="capitalize")
def capitalize(obj: Any):
    return str(obj).capitalize()


@register.filter(name="get")
def get_id(obj: Any, attr: Any):
    return tryCatchThis(obj.get, None)(attr)


@register.filter(name="str")
def str_convert(obj):
    return str(obj)


@register.filter(name="len")
def len__(obj) -> int:
    return tryCatchThis(len, 0)(obj)


@register.filter(name="img")
def image(obj) -> Image:
    return Image(
        f"data:image/png;base64,{str(obj).replace('-', '+').replace('_', '/')}"
    )


@register.filter(name="in")
def in_check(obj, vector):
    return bool(obj in vector)


@register.filter(name="index")
def index(vector: list[Any], index: int):
    return tryCatchThis((lambda x: vector[int(x)]), None)(index)


@register.filter(name="index_str")
def str_index(vector: dict, index: str):
    return tryCatchThis((lambda x: vector.get(str(x))), None)(index)


@register.filter(name="timestamp")
def timestamp(obj):
    return tryCatchThis((lambda x: datetime.fromisoformat(x).strftime("%d/%m/%Y, %H:%M:%S")), "Incorrect Time Format")(obj)

@register.filter(name="date")
def url_date(obj: datetime):
    return tryCatchThis((lambda x: x.strftime("%d/%m/%Y, %H:%M:%S")), "Incorrect Time Format")(obj)


@register.filter(name="rgb")
def rgb(obj: str, opacity: int = 1):
    r = g = b = 255
    a = re.findall(r"#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", obj)

    try:
        r, g, b = list(map(lambda x: int(x, 16), next(iter(a))))

    except Exception:
        pass
    return f"rgb({r},{g},{b},{opacity})"


@register.filter(name="encode")
def encode(obj: str):
    a = b"if-you-see-this-you-are-screwed"

    try:
        return obj.encode()
    except Exception:
        return a


@register.filter(name="hex")
def hex(obj: bytes):
    a = "if-you-see-this-you-are-screwed"
    try:
        return obj.hex()
    except Exception:
        return a


@register.filter(name="rstrip")
def rstrip(obj: str, index: int):
    return tryCatchThis((lambda x, y: x[:-int(y)]), "None")(obj, index)


@register.filter(name="isImage")
def isImage(obj: str):
    return str(obj[-1]) == "I"


@register.filter(name="isText")
def isText(obj: str):
    return str(obj[-1]) == "T"


@register.filter(name="step")
def step(obj: forms.Form, steps: int = 0):
    fields: list = []
    current: list = []

    for idx, field in enumerate(iter(obj)):
        if idx > 0 and idx % steps == 0:
            fields.append(current.copy())
            current.clear()
        current.append(field)

    if current:
        fields.append(current)

    return fields

