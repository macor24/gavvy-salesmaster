#!/usr/bin/env python3
"""
数据备份脚本

用法:
  python scripts/backup_data.py
    --source ./data
    --dest ./backups
    --keep-days 30
"""

import os
import sys
import shutil
import time
import zipfile
from datetime import datetime
from pathlib import Path
import argparse


def backup_data(source_dir: Path, dest_dir: Path, keep_days: int = 30):
    """备份数据

    Args:
        source_dir: 源数据目录
        dest_dir: 备份目录
        keep_days: 保留天数
    """
    # 创建目标目录
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 检查源目录
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"[WARN] 源目录不存在或不是目录: {source_dir}")
        return False

    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"sales_data_backup_{timestamp}.zip"
    backup_path = dest_dir / backup_name

    print(f"[INFO] 开始备份: {source_dir} -> {backup_path}")

    # 创建 ZIP 备份
    file_count = 0
    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
                    file_count += 1

        print(f"[OK] 备份完成: {file_count} 个文件")
        print(f"[OK] 备份文件: {backup_path}")
    except Exception as e:
        print(f"[ERROR] 备份失败: {e}")
        return False

    # 清理过期备份
    cleanup_old_backups(dest_dir, keep_days)

    return True


def cleanup_old_backups(dest_dir: Path, keep_days: int):
    """清理过期备份"""
    now = time.time()
    cutoff = now - (keep_days * 24 * 3600)

    removed_count = 0
    for backup_file in dest_dir.glob("sales_data_backup_*.zip"):
        if backup_file.is_file():
            mtime = backup_file.stat().st_mtime
            if mtime < cutoff:
                backup_file.unlink()
                removed_count += 1

    if removed_count > 0:
        print(f"[INFO] 清理过期备份: 删除 {removed_count} 个文件")


def main():
    parser = argparse.ArgumentParser(description="数据备份工具")
    parser.add_argument(
        "--source",
        default="./data",
        help="源数据目录 (默认: ./data)"
    )
    parser.add_argument(
        "--dest",
        default="./backups",
        help="备份目录 (默认: ./backups)"
    )
    parser.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="保留天数 (默认: 30)"
    )

    args = parser.parse_args()

    source_dir = Path(args.source).resolve()
    dest_dir = Path(args.dest).resolve()

    success = backup_data(source_dir, dest_dir, args.keep_days)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
