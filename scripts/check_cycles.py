#!/usr/bin/env python3
"""Reject import cycles between the project's immediate packages."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path


def package_of(file_path: str, source_roots: list[str]) -> str | None:
    path = Path(file_path)
    for root in source_roots:
        if root in (".", ""):
            parts = path.parts
        elif path.is_relative_to(root):
            parts = path.relative_to(root).parts
        else:
            continue
        return ".".join(parts[:2]) if len(parts) >= 3 else None
    return None


def cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    result: list[list[str]] = []
    counter = 0

    def visit(node: str) -> None:
        nonlocal counter
        index[node] = low[node] = counter
        counter += 1
        stack.append(node)
        on_stack.add(node)
        for neighbour in sorted(graph.get(node, ())):
            if neighbour not in index:
                visit(neighbour)
                low[node] = min(low[node], low[neighbour])
            elif neighbour in on_stack:
                low[node] = min(low[node], index[neighbour])
        if low[node] == index[node]:
            component = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            if len(component) > 1:
                result.append(sorted(component))

    for node in sorted(graph):
        if node not in index:
            visit(node)
    return result


def main() -> int:
    config_path = Path("tach.toml")
    if not config_path.exists():
        print("Run this check from the repository root (tach.toml is missing).", file=sys.stderr)
        return 2

    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    roots = sorted(
        (root.rstrip("/") for root in config.get("source_roots", ["."])),
        key=len,
        reverse=True,
    )
    completed = subprocess.run(
        [sys.executable, "-m", "tach", "map", "--output", "-"],
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        print(completed.stdout + completed.stderr, file=sys.stderr)
        return completed.returncode

    dependency_map = json.loads(completed.stdout)
    graph: dict[str, set[str]] = {}
    for importer, imported_files in dependency_map.items():
        source = package_of(importer, roots)
        if source is None:
            continue
        targets = graph.setdefault(source, set())
        for imported in imported_files:
            target = package_of(imported, roots)
            if target is not None and target != source:
                targets.add(target)

    found = cycles(graph)
    if not found:
        print("No import cycles between packages.")
        return 0
    for cycle in found:
        print(f"Circular dependency between packages: {' <-> '.join(cycle)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
