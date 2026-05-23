import sys
import ast
import re
from html.parser import HTMLParser
from typing import List, Optional, TextIO, Tuple


def esc(s: str) -> str:
    return ast.unparse(ast.Constant(s))


re_ws = re.compile(r"[\s\n]*")
re_chomp = re.compile(r"\n$")
self_closing_tags = [
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "keygen",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
]


class TranslatingParser(HTMLParser):
    def __init__(self, out: TextIO, indent: str = "    ", starting_indent: str = ""):
        super().__init__()
        self._out = out
        self._indent = indent
        self._starting_indent = starting_indent
        self._tag_stack: List[str] = []
        self._buffer: str = ""

    def _write(self, s: str) -> None:
        self._flush_buffer()
        self._out.write(s)

    def _write_indent(self) -> None:
        self._flush_buffer()
        self._write(self._starting_indent + (self._indent * len(self._tag_stack)))

    def _write_tentative(self, s: str) -> None:
        """Put string value in a temporary buffer

        Values in the buffer will be flushed to the output stream if/when the next
        non-tentative write occurs.
        """
        self._buffer = self._buffer + s

    def _flush_buffer(self) -> None:
        self._out.write(self._buffer)
        self._buffer = ""

    def _pre(self) -> bool:
        return "pre" in self._tag_stack

    def _write_starttag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]], has_children: bool
    ) -> None:
        self._write(f"tags.{tag}(")
        if len(attrs) > 0:
            self._write("{")
            self._write(
                ", ".join(
                    [
                        f"{esc(name)}: {esc(value if value is not None else '')}"
                        for name, value in attrs
                    ]
                )
            )
            self._write("}")
            if has_children:
                self._write(",")

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self._write_indent()
        self._write_starttag(tag, attrs, True)
        if tag in self_closing_tags:
            self._write(")")
            self._write_tentative(",\n")
        else:
            self._write_tentative("\n")
            self._tag_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if len(self._tag_stack) == 0 or self._tag_stack[-1] != tag:
            # TODO: Print line/col of problematic HTML
            raise ValueError(
                f"Malformed HTML (</{tag}> encountered where </{self._tag_stack[-1]}> was expected)"
            )
        self._tag_stack.pop()

        self._write_indent()
        self._write(")")
        self._write_tentative(",\n")

    def handle_startendtag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        self._write_indent()
        self._write_starttag(tag, attrs, False)
        self._write(")")
        self._write_tentative(",\n")

    def handle_data(self, data: str) -> None:
        if self._pre():
            self._write(esc(data))
        else:
            if not re_ws.fullmatch(data):
                data = re_chomp.sub("", data)
                self._write_indent()
                if "\n" not in data:
                    self._write(esc(data.strip()))
                elif '"""' not in data:
                    self._write('"""')
                    self._write(data)
                    self._write('"""')
                else:
                    # TODO: multi-line values can be handled better
                    self._write(esc(data))
            else:
                return
        self._write_tentative(",\n")

    def handle_comment(self, data: str) -> None:
        for line in data.splitlines():
            self._write_indent()
            self._write(f"# {line.strip()}")
            self._write("\n")

    def handle_decl(self, decl: str) -> None:
        ...

    def handle_pi(self, data: str) -> None:
        ...

    def unknown_decl(self, data: str) -> None:
        ...


def main():
    p = TranslatingParser(sys.stdout)
    for line in sys.stdin:
        p.feed(line)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
