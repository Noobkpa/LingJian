from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    text = re.sub(r"[ＳSｓsＷw万]+", "", text)
    text = re.sub(r"[@#].*", "", text)
    text = re.sub(r"[·\.\-_\=\+]+", "", text)
    text = re.sub(r"[\[\]\{\}\(\)]", "", text)
    text = text.strip()
    text = re.sub(r'["“”‘’\[\]<>]', '"', text)
    text = text.replace(",", "，").replace("?", "？").replace(":", "：")
    text = text.replace("=", "＝").replace(".", "。").replace("!", "！")
    text = re.sub(r"^[+：:.\d]+", "", text)
    text = re.sub(r"[+：:.\d]+$", "", text)
    text = re.sub(r"[A-Za-z]{3,}", "", text)
    return text.replace(" ", "")


def join_nonempty(parts: list[str], sep: str = "\n") -> str:
    return sep.join(p.strip() for p in parts if p and p.strip()).strip()
