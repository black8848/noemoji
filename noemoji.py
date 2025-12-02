#!/usr/bin/env python3
"""
NoEmoji - 批量扫描并删除文件中的emoji表情

用法:
    python noemoji.py <目标文件夹> [选项]

示例:
    python noemoji.py ./docs
    python noemoji.py ./src --dry-run
    python noemoji.py ./content --ext .md .txt
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple


# Emoji正则表达式 - 覆盖大部分常见emoji
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # 表情符号
    "\U0001F300-\U0001F5FF"  # 符号和象形文字
    "\U0001F680-\U0001F6FF"  # 交通和地图符号
    "\U0001F700-\U0001F77F"  # 炼金术符号
    "\U0001F780-\U0001F7FF"  # 几何图形扩展
    "\U0001F800-\U0001F8FF"  # 补充箭头-C
    "\U0001F900-\U0001F9FF"  # 补充符号和象形文字
    "\U0001FA00-\U0001FA6F"  # 国际象棋符号
    "\U0001FA70-\U0001FAFF"  # 符号和象形文字扩展-A
    "\U0001F1E0-\U0001F1FF"  # 旗帜(区域指示符)
    "\U00002600-\U000026FF"  # 杂项符号 (太阳、云、雨等)
    "\U00002700-\U000027BF"  # 装饰符号 (剪刀、铅笔等)
    "\U00002300-\U000023FF"  # 杂项技术符号 (键盘、时钟等)
    "\U0000FE00-\U0000FE0F"  # 变体选择器
    "\U0001F000-\U0001F02F"  # 麻将牌
    "\U0001F0A0-\U0001F0FF"  # 扑克牌
    "\U0001F200-\U0001F251"  # 封闭表意文字
    "\U000024C2-\U000024FF"  # 封闭字母数字
    "\U00002B50-\U00002B55"  # 星星、圆圈等
    "\U0000203C-\U00003299"  # 其他常见符号
    "]+",
    flags=re.UNICODE,
)


class FileResult(NamedTuple):
    """单个文件的处理结果"""
    path: str
    emoji_count: int
    emojis_found: list[str]


def find_emojis(text: str) -> list[str]:
    """查找文本中的所有emoji"""
    return EMOJI_PATTERN.findall(text)


def remove_emojis(text: str) -> tuple[str, int]:
    """移除文本中的所有emoji，返回(处理后文本, 删除数量)"""
    emojis = find_emojis(text)
    cleaned = EMOJI_PATTERN.sub("", text)
    return cleaned, len(emojis)


def process_file(file_path: Path, dry_run: bool = False) -> FileResult | None:
    """处理单个文件，返回处理结果"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError, OSError) as e:
        print(f"  跳过 {file_path}: {e}", file=sys.stderr)
        return None

    emojis = find_emojis(content)
    if not emojis:
        return None

    if not dry_run:
        cleaned, _ = remove_emojis(content)
        try:
            file_path.write_text(cleaned, encoding="utf-8")
        except (PermissionError, OSError) as e:
            print(f"  写入失败 {file_path}: {e}", file=sys.stderr)
            return None

    return FileResult(
        path=str(file_path),
        emoji_count=len(emojis),
        emojis_found=emojis,
    )


def scan_directory(
    target_dir: Path,
    extensions: list[str] | None = None,
    dry_run: bool = False,
) -> list[FileResult]:
    """递归扫描目录并处理文件"""
    results: list[FileResult] = []

    for root, _, files in os.walk(target_dir):
        for filename in files:
            file_path = Path(root) / filename

            # 过滤文件扩展名
            if extensions:
                if file_path.suffix.lower() not in extensions:
                    continue

            result = process_file(file_path, dry_run)
            if result:
                results.append(result)

    return results


def print_report(results: list[FileResult], dry_run: bool = False) -> None:
    """打印处理报告"""
    if not results:
        print("\n没有发现包含emoji的文件")
        return

    mode = "[预览模式]" if dry_run else "[已清理]"
    print(f"\n{mode} 处理报告")
    print("=" * 60)

    total_emojis = 0
    for result in results:
        total_emojis += result.emoji_count
        emoji_preview = "".join(result.emojis_found[:10])
        if len(result.emojis_found) > 10:
            emoji_preview += "..."
        print(f"  {result.path}")
        print(f"    数量: {result.emoji_count}  内容: {emoji_preview}")

    print("=" * 60)
    print(f"共处理 {len(results)} 个文件，{'发现' if dry_run else '删除'} {total_emojis} 个emoji")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="批量扫描并删除文件中的emoji表情",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python noemoji.py ./docs              # 扫描docs文件夹
  python noemoji.py ./src --dry-run     # 预览模式，不实际删除
  python noemoji.py . --ext .md .txt    # 只处理.md和.txt文件
        """,
    )
    parser.add_argument("target", type=str, help="目标文件夹路径")
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="预览模式，只显示会删除的emoji，不实际修改文件",
    )
    parser.add_argument(
        "--ext", "-e",
        nargs="+",
        type=str,
        help="只处理指定扩展名的文件 (例如: --ext .md .txt)",
    )

    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"错误: 目录不存在 - {target_path}", file=sys.stderr)
        return 1

    if not target_path.is_dir():
        print(f"错误: 不是目录 - {target_path}", file=sys.stderr)
        return 1

    # 处理扩展名格式
    extensions = None
    if args.ext:
        extensions = [ext if ext.startswith(".") else f".{ext}" for ext in args.ext]

    print(f"扫描目录: {target_path}")
    if args.dry_run:
        print("模式: 预览 (不修改文件)")
    if extensions:
        print(f"文件类型: {', '.join(extensions)}")

    results = scan_directory(target_path, extensions, args.dry_run)
    print_report(results, args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
