import os
import re

import pandas as pd
from beartype import beartype as typed
from beartype.door import die_if_unbearable as assert_type
from beartype.typing import Iterable
from tqdm import tqdm


def extract_files(source_dir, extension):
    filenames = []
    for root, _dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith(extension):
                filename = os.path.join(root, file)
                filenames.append(filename)
    return filenames


@typed
def inside_brackets(s: str, start_pos: int) -> str:
    assert s[start_pos] == "{"
    balance = 0
    for i in range(start_pos, len(s)):
        balance += (s[i] == "{") - (s[i] == "}")
        if not balance:
            return s[start_pos : i + 1]
    raise RuntimeError("unclosed bracket")


@typed
def java_methods_in_string(content: str) -> Iterable[tuple[str, str]]:
    beginning = "^\s*"
    keywords = "(?:(?:public|protected|private|static|abstract|final|@NotNull)\s)+"
    type = "([\w\<\>\[\]]+)\s+"  # group 1
    name = "(\w+)\s*"  # group 2
    arguments = "(\([^\)]*\))\s*"  # group 3
    bracket = "(\{)"  # group 4
    pattern = beginning + keywords + type + name + arguments + bracket
    for match in re.finditer(pattern, content, flags=re.MULTILINE):
        try:
            body = inside_brackets(content, match.start(4))
        except RuntimeError:
            print("unclosed bracket or wrong match")
            continue
        typed_body = " ".join([match[1], match[3], body])
        normalized_typed_body = re.sub("\s+", " ", typed_body)
        name = match[2]
        yield normalized_typed_body, name


@typed
def java_methods_in_file(filename: str) -> Iterable[tuple[str, str]]:
    try:
        with open(filename, encoding="utf-8") as file:
            return java_methods_in_string(file.read())
    except UnicodeDecodeError:
        print("something wrong with decoding")
        return []


filenames = extract_files("intellij-community-master", ".java")
bodies = []
names = []

for filename in tqdm(filenames):
    methods = java_methods_in_file(filename)
    for body, name in methods:
        bodies.append(body)
        names.append(name)

dataset = pd.DataFrame({"body": bodies, "name": names})
dataset.to_csv("train.csv")
