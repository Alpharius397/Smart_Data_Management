import re
from django import forms, template
from Main.templatetags.bad_image import bad_image
from typing import NamedTuple
from datetime import datetime


class Image(NamedTuple):
    img: str


register = template.Library()


@register.filter(name="getID")
def get_id(obj, attr):
    return obj.get(attr, None)


@register.filter(name="all")
def all_check(obj: list, attr: str):
    return obj if all(i[attr] for i in obj) else []


@register.filter(name="str")
def str_convert(obj):
    return str(obj)


@register.filter(name="addOne")
def addOne(obj: int | float):
    return int(obj) + 1


@register.filter(name="check")
def check(obj) -> bool:
    return obj is not None


@register.filter(name="enum")
def enum(obj) -> list[tuple[int, list]]:
    return list(enumerate(obj))


@register.filter(name="len")
def len__(obj) -> int:
    try:
        return len(obj)
    except:
        return 1


@register.filter(name="img")
def image(obj) -> Image:
    return Image(f"data:image/png;base64,{str(obj).replace("-","+").replace("_","/")}")


@register.filter(name="in")
def in_check(obj, vector):
    return bool(obj in vector)


@register.filter(name="index")
def index(vector, index):
    return vector[int(index) % len(vector)] if (index is not None) else None


@register.filter(name="index_str")
def str_index(vector, index):
    return vector.get(str(index), None)


@register.filter(name="full_img")
def full_image(obj):
    try:
        raw_img = obj.split(":")
        width, height, img = raw_img
    except:
        width, height = 100, 100
        img = bad_image

    return Image(f"data:image/jpeg;base64,{img}", width, height)


@register.filter(name="get_last")
def last_path(obj):
    path = obj.split("/")

    return "/".join(path[:-2])


@register.filter(name="clean")
def clean_text(obj):
    sem_data = r"(.+)Sem_\d+$"

    sem: list[str] = re.findall(sem_data, obj)

    if sem:
        return sem[0].strip().strip("_")

    return None


@register.filter(name="timestamp")
def timestamp(obj):
    try:
        return datetime.fromisoformat(obj).strftime("%d/%m/%Y, %H:%M:%S")
    except:
        return "Incorrect Time Format"


@register.filter(name="date")
def url_date(obj: datetime):
    try:
        return obj.strftime("%Y-%m-%d")
    except:
        return "Incorrect Time Format"


@register.filter(name="rgb")
def rgb(obj: str, opacity: int = 1):
    r = g = b = 255
    a = re.findall(r"#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", obj)

    try:
        r, g, b = list(map(lambda x: int(x, 16), next(iter(a))))

    except Exception:
        pass
    print(f"rgb({r},{g},{b},{opacity})")
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
    return 'None' if obj is None else obj[:-index]

@register.filter(name="isImage")
def isImage(obj: str):
    return str(obj[-1]) == 'I'

@register.filter(name="isText")
def isText(obj: str):
    return str(obj[-1]) == 'T'

@register.filter(name="step")
def step(obj: forms.Form, steps: int = 0):
    fields: list = []
    current: list = []
    
    for idx, field in enumerate(iter(obj)):
        
        if idx>0 and idx%steps == 0:
            fields.append(current.copy())
            current.clear()
        current.append(field)
        
    if current: fields.append(current)
        
    return fields