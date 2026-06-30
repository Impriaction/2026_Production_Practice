#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : system_utils.py
# @Project   : ODPlatform
# @Function  : System and environment utilities

from __future__ import annotations

import logging
import os
import platform
import time
from typing import List, Optional

from od_platform.common.paths import RAW_DATA_DIR, ROOT_DIR
from od_platform.common.string_utils import pad_to_width

LINE_WIDTH = 60

logger = logging.getLogger(__name__)


def _format_size(bytes_size) -> str:
    """Format a byte size into a human-readable string."""
    if not bytes_size or not isinstance(bytes_size, (int, float)):
        return "N/A"
    if bytes_size >= 1024**3:
        return f"{bytes_size / 1024**3:.2f} GB"
    if bytes_size >= 1024**2:
        return f"{bytes_size / 1024**2:.2f} MB"
    if bytes_size >= 1024:
        return f"{bytes_size / 1024:.2f} KB"
    return f"{bytes_size} B"


def get_basic_device_info() -> dict:
    """Return structured environment information."""
    cpu_name = platform.processor() or platform.machine() or "未知CPU"
    cpu_cores = os.cpu_count() or "Unknown"

    try:
        import psutil

        memory = psutil.virtual_memory()
        total_ram = _format_size(memory.total)
        available_ram = _format_size(memory.available)
        ram_usage = f"{memory.percent}%"
    except ImportError:
        total_ram = "N/A(psutil 未安装)"
        available_ram = "N/A(psutil 未安装)"
        ram_usage = "N/A(psutil 未安装)"

    try:
        import torch

        torch_version = torch.__version__
        cuda_available = torch.cuda.is_available()
        gpu_count = torch.cuda.device_count() if cuda_available else 0
        torch_module = torch
    except ImportError:
        torch_version = "N/A(torch 未安装)"
        cuda_available = "N/A(torch 未安装)"
        gpu_count = "N/A(torch 未安装)"
        torch_module = None

    try:
        from ultralytics import __version__ as ultralytics_version
    except ImportError:
        ultralytics_version = "N/A(ultralytics 未安装)"

    gpu_info = {
        "GPU可用": cuda_available,
        "GPU数量": gpu_count,
    }
    if cuda_available and torch_module is not None:
        for index in range(gpu_count):
            gpu_info[f"GPU {index}"] = torch_module.cuda.get_device_name(index)
            gpu_info[f"GPU {index} 显存"] = _format_size(
                torch_module.cuda.get_device_properties(index).total_memory
            )

    return {
        "系统信息": {
            "操作系统": f"{platform.system()} {platform.release()} {platform.machine()}",
            "主机名": platform.node(),
            "Python版本": platform.python_version(),
            "PyTorch版本": torch_version,
            "Ultralytics版本": ultralytics_version,
            "当前时间": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "CPU信息": {
            "CPU型号": cpu_name,
            "核心数": cpu_cores,
        },
        "内存信息": {
            "总内存": total_ram,
            "可用内存": available_ram,
            "内存使用率": ram_usage,
        },
        "GPU信息": gpu_info,
    }


def log_device_info(target_logger: Optional[logging.Logger] = None) -> dict:
    """Log environment information through a logger."""
    log = target_logger if target_logger is not None else logger
    info = get_basic_device_info()

    log.info("运行环境信息概览".center(LINE_WIDTH))
    log.info("=" * LINE_WIDTH)

    key_width = 20
    for category, details in info.items():
        log.info(category.center(LINE_WIDTH))
        log.info("-" * LINE_WIDTH)
        for key, value in details.items():
            padded_key = pad_to_width(key, key_width)
            log.info("%s: %s", padded_key, value)
    return info


def _check_raw_data_status() -> List[str]:
    raw_status: List[str] = []
    rel_raw = RAW_DATA_DIR.relative_to(ROOT_DIR)

    if not RAW_DATA_DIR.exists():
        logger.warning("原始数据目录不存在: %s，请在该目录下放置原始数据文件", rel_raw)
        raw_status.append(f"{rel_raw} 不存在，-> 请创建并放入数据")
    elif not any(RAW_DATA_DIR.iterdir()):
        logger.warning(
            "原始数据目录为空: %s，请在该目录下放置原始数据文件\n"
            "预期的组织形式为:\n"
            "  %s/<数据集名称>/\n"
            "  ├── images\n"
            "  └── annotations",
            rel_raw,
            rel_raw,
        )
        raw_status.append(f"{rel_raw} 为空，-> 请创建并放入至少一个数据集")
    else:
        sub_dirs = [path for path in RAW_DATA_DIR.iterdir() if path.is_dir()]
        logger.info("检测到原始数据目录: %s，共有 %s 个数据集文件夹", rel_raw, len(sub_dirs))
        raw_status.append(f"{rel_raw} 存在，包含 {len(sub_dirs)} 个数据集")
        for sub_dir in sorted(sub_dirs):
            raw_status.append(f"  - {sub_dir.name}")

    return raw_status


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    log_device_info()
    for line in _check_raw_data_status():
        print(line)