import re
from pathlib import Path


RAW_BLOCKS = {
    "EXPERIENCE_BLOCK",
    "PROJECTS_BLOCK",
    "SKILLS_BLOCK",
    "RECIPIENT",
}


def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_file(path: str, content: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding="utf-8")


def escape_latex_text(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def replace_block(content: str, block_name: str, new_text: str) -> str:
    pattern = (
        rf"(%<TAILOR:{re.escape(block_name)}_START>\s*\n)"
        rf"(.*?)"
        rf"(\n%<TAILOR:{re.escape(block_name)}_END>)"
    )
    match = re.search(pattern, content, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Block '{block_name}' not found.")

    return (
        content[:match.start()]
        + match.group(1)
        + new_text.strip()
        + match.group(3)
        + content[match.end():]
    )


def patch_file(input_path: str, output_path: str, replacements: dict[str, str]) -> None:
    content = read_file(input_path)

    for block_name, new_text in replacements.items():
        if block_name in RAW_BLOCKS:
            replacement_text = new_text
        else:
            replacement_text = escape_latex_text(new_text)

        content = replace_block(content, block_name, replacement_text)

    write_file(output_path, content)
