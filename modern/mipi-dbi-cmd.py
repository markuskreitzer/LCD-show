#!/usr/bin/env python3

import argparse
import shlex
from pathlib import Path

MAGIC = b"MIPI DBI" + bytes(7) + bytes([1])


def byte(value: str) -> int:
    number = int(value, 0)
    if not 0 <= number <= 255:
        raise ValueError(f"value is not one byte: {value}")
    return number


def compile_commands(source: str) -> bytes:
    output = bytearray(MAGIC)
    for line_number, line in enumerate(source.splitlines(), 1):
        fields = shlex.split(line, comments=True)
        if not fields:
            continue
        if fields[0] == "delay" and len(fields) == 2:
            output.extend((0, 1, byte(fields[1])))
            continue
        if fields[0] == "command" and len(fields) >= 2:
            values = [byte(value) for value in fields[1:]]
            parameters = values[1:]
            output.extend((values[0], len(parameters), *parameters))
            continue
        raise ValueError(f"invalid command on line {line_number}: {line}")
    if len(output) == len(MAGIC):
        raise ValueError("command file is empty")
    return bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    args.output.write_bytes(compile_commands(args.input.read_text()))


if __name__ == "__main__":
    main()
