#!/usr/bin/env python3
"""Extract CM-550 motion pages from an R+ Motion .mtn3 file.

Usage:
  python3 scripts/extract_cm550_motion_map.py /path/to/file.mtn3

The script prints:
  1. A table of motion pages discovered from <Flow name="NNN Label">
  2. A suggested ROS 2 command_map string for cm550_motion_bridge_node
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FLOW_PREFIX_RE = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")


def slugify(label: str) -> str:
    cleaned = label.lower().strip()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def infer_semantic_aliases(entries):
    alias_map = {}
    for page, label, slug in entries:
        if "spin_left" in slug:
            alias_map.setdefault("turn_left", page)
            alias_map.setdefault("spin_left", page)
        elif "spin_right" in slug:
            alias_map.setdefault("turn_right", page)
            alias_map.setdefault("spin_right", page)
        elif slug in {"001_ready_pose", "002_basic_pose"} or "ready_pose" in slug or "basic_pose" in slug:
            alias_map.setdefault("stand", page)
            alias_map.setdefault("stop", page)
            alias_map.setdefault("idle", page)
        elif slug == "003_stand_up" or "stand_up" in slug:
            alias_map.setdefault("stand_up", page)
        elif "sitdown" in slug:
            alias_map.setdefault("sitdown", page)
        elif "hello" in slug:
            alias_map.setdefault("hello", page)
        elif "clap" in slug:
            alias_map.setdefault("clap", page)

        if slug.startswith("103_w_l_f_go") or slug.startswith("153_w_h_f_go"):
            alias_map.setdefault("walk", page)
            alias_map.setdefault("follow", page)
        elif slug.startswith("108_w_l_b_go") or slug.startswith("158_w_h_b_go"):
            alias_map.setdefault("reverse", page)

    return alias_map


def load_entries(path: Path):
    root = ET.parse(path).getroot()
    flow_root = root.find("FlowRoot")
    if flow_root is None:
        raise ValueError("No se encontro <FlowRoot> en el archivo")

    entries = []
    for flow in flow_root.findall("Flow"):
        name = flow.attrib.get("name", "").strip()
        match = FLOW_PREFIX_RE.match(name)
        if not match:
            continue
        page = int(match.group(1))
        label = match.group(2).strip()
        entries.append((page, label, slugify(name)))
    return entries


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 scripts/extract_cm550_motion_map.py /path/to/file.mtn3", file=sys.stderr)
        return 1

    path = Path(sys.argv[1]).expanduser()
    if not path.exists():
        print(f"No existe: {path}", file=sys.stderr)
        return 1

    entries = load_entries(path)
    print(f"# Motion pages extraidas de {path}")
    print("page\tlabel\tslug")
    for page, label, slug in entries:
        print(f"{page}\t{label}\t{slug}")

    aliases = infer_semantic_aliases(entries)
    if aliases:
        ordered_keys = [
            "walk", "follow", "stop", "idle", "turn_left", "spin_left",
            "turn_right", "spin_right", "reverse", "stand", "stand_up",
            "sitdown", "hello", "clap",
        ]
        items = [f"{key}:{aliases[key]}" for key in ordered_keys if key in aliases]
        print("\n# command_map sugerido")
        print(",".join(items))
    else:
        print("\n# No se pudieron inferir aliases semanticos automaticamente")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
