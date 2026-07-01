#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : convert_rsod.py
# @Author    : ODPlatform team
# @Project   : ODPlatform
# @Function  : RSOD dataset conversion script - Pascal VOC to YOLO
"""Convert data/raw/rsod Pascal VOC annotations to YOLO format.

Usage:
    python scripts/convert_rsod.py           # dry-run overview
    python scripts/convert_rsod.py --convert # execute conversion
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLATFORM_SRC = REPO_ROOT / "apps" / "platform" / "src"
if str(PLATFORM_SRC) not in sys.path:
    sys.path.insert(0, str(PLATFORM_SRC))

from od_platform.common.constants import AnnotationFormat, Task
from od_platform.data_pipeline.convert.registry import ConvertOptions, list_capabilities
from od_platform.data_pipeline.convert.service import convert_data_to_yolo


def main(convert: bool = False) -> None:
    raw_dir = REPO_ROOT / "data" / "raw" / "rsod"
    xml_dir = raw_dir / "annotations"
    images_dir = raw_dir / "images"
    output_dir = REPO_ROOT / "data" / "processed" / "rsod_yolo" / "labels"

    print("=" * 60)
    print("RSOD dataset conversion: Pascal VOC -> YOLO")
    print("=" * 60)

    xml_count = len(list(xml_dir.glob("*.xml"))) if xml_dir.exists() else 0
    jpg_count = len(list(images_dir.glob("*.jpg"))) if images_dir.exists() else 0
    png_count = len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0
    img_count = jpg_count + png_count

    print("\n[Dataset Overview]")
    print(f"   Annotation dir: {xml_dir}")
    print(f"   Image dir:      {images_dir}")
    print(f"   XML labels:     {xml_count}")
    print(f"   Image files:    {img_count}")
    print(f"   Background:     {img_count - xml_count}")

    print("\n[Registered Converters]")
    caps = list_capabilities()
    for fmt, tasks in caps.items():
        enabled = "[V]" if Task.DETECT in tasks else "[!]"
        print(f"   {enabled} {fmt}: supports {', '.join(tasks)}")

    if not convert:
        print("\n[Hint] This is dry-run mode. Use --convert to execute conversion.")
        return

    print("\n[Start Conversion]")
    print(f"   Input:  {xml_dir}")
    print(f"   Output: {output_dir}")

    options = ConvertOptions(task=Task.DETECT)
    classes = convert_data_to_yolo(
        input_dir=xml_dir,
        output_labels_dir=output_dir,
        annotation_format=AnnotationFormat.PASCAL_VOC,
        options=options,
    )

    txt_count = len(list(output_dir.glob("*.txt"))) if output_dir.exists() else 0
    print("\n[Conversion Done]")
    print(f"   YOLO labels: {txt_count}")
    print(f"   Classes ({len(classes)}): {', '.join(classes)}")
    print(f"   Output dir: {output_dir}")

    print("\n[Label Preview: first 3 files]")
    for index, txt_file in enumerate(sorted(output_dir.glob("*.txt"))[:3], 1):
        raw_text = txt_file.read_text(encoding="utf-8").strip()
        lines = raw_text.split("\n") if raw_text else []
        print(f"   [{index}] {txt_file.name}: {len(lines)} targets")
        for line in lines[:3]:
            print(f"       {line}")


if __name__ == "__main__":
    convert_flag = "--convert" in sys.argv
    main(convert=convert_flag)
