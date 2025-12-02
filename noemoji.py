#!/usr/bin/env python3
"""
NoEmoji - 批量扫描并删除文件中的emoji表情

用法:
    python noemoji.py <目标文件夹> [选项]

示例:
    python noemoji.py ./docs
    python noemoji.py ./src --dry-run
    python noemoji.py ./content --ext .md .txt

提示:
    安装 emoji 库可获得更精确的匹配: pip install emoji
"""

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable, NamedTuple

# 大文件阈值：超过此大小使用流式处理
LARGE_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB

# 尝试导入 emoji 库
try:
    import emoji
    HAS_EMOJI_LIB = True
except ImportError:
    HAS_EMOJI_LIB = False


# 精确的Emoji正则表达式 - 只匹配真正的emoji，不包含中日韩字符和数学符号
# 主要覆盖 SMP 平面 (U+1Fxxx) 上的emoji
EMOJI_PATTERN = re.compile(
    "["
    # ===== SMP平面 - 真正的emoji区域 =====
    "\U0001F600-\U0001F64F"  # 表情符号 (笑脸、手势等)
    "\U0001F300-\U0001F5FF"  # 杂项符号和象形文字 (天气、动物、食物等)
    "\U0001F680-\U0001F6FF"  # 交通和地图符号 (车辆、建筑等)
    "\U0001F900-\U0001F9FF"  # 补充符号和象形文字 (更多表情、人物等)
    "\U0001FA00-\U0001FA6F"  # 国际象棋符号
    "\U0001FA70-\U0001FAFF"  # 符号和象形文字扩展-A (新emoji)
    "\U0001F1E0-\U0001F1FF"  # 旗帜 (区域指示符)
    # ===== BMP平面 - 仅常见emoji字符 =====
    "\U00002702-\U00002704"  # 剪刀等
    "\U00002708-\U0000270D"  # 飞机、信封、铅笔等
    "\U0000270F"             # 铅笔
    "\U00002712"             # 黑色笔尖
    "\U00002714"             # 重勾号 ✔
    "\U00002716"             # 重乘号 ✖
    "\U0000271D"             # 拉丁十字
    "\U00002721"             # 大卫之星
    "\U00002728"             # 闪光 ✨
    "\U00002733-\U00002734"  # 八辐轮
    "\U00002744"             # 雪花 ❄
    "\U00002747"             # 闪光
    "\U0000274C"             # 叉号 ❌
    "\U0000274E"             # 带叉方框
    "\U00002753-\U00002755"  # 问号、感叹号
    "\U00002757"             # 重感叹号 ❗
    "\U00002763-\U00002764"  # 心形 ❤
    "\U00002795-\U00002797"  # 加减乘号
    "\U000027A1"             # 向右箭头
    "\U000027B0"             # 卷曲循环
    "\U000027BF"             # 双卷曲循环
    "\U00002B05-\U00002B07"  # 箭头
    "\U00002B1B-\U00002B1C"  # 方块
    "\U00002B50"             # 白色中等星星 ⭐
    "\U00002B55"             # 重大空心圆 ⭕
    "\U00003030"             # 波浪线
    "\U0000303D"             # 部分交替标记
    "\U0001F004"             # 麻将红中
    "\U0001F0CF"             # 扑克王牌
    "\U0001F170-\U0001F171"  # A/B血型
    "\U0001F17E-\U0001F17F"  # O血型/P
    "\U0001F18E"             # AB血型
    "\U0001F191-\U0001F19A"  # 方块字母
    "\U0001F201-\U0001F202"  # 日文符号
    "\U0001F21A"             # 日文"无"
    "\U0001F22F"             # 日文"指"
    "\U0001F232-\U0001F23A"  # 日文方块
    "\U0001F250-\U0001F251"  # 日文"得""割"
    # 常用emoji符号
    "\U000023E9-\U000023F3"  # 播放控制符号
    "\U000023F8-\U000023FA"  # 播放控制
    "\U000025B6"             # 播放按钮
    "\U000025C0"             # 倒放按钮
    "\U00002600-\U00002604"  # 太阳、云等天气
    "\U00002611"             # 勾选框 ☑
    "\U00002614-\U00002615"  # 雨伞、咖啡
    "\U00002618"             # 三叶草
    "\U0000261D"             # 指向上的手指
    "\U00002620"             # 骷髅
    "\U00002622-\U00002623"  # 辐射、生化
    "\U00002626"             # 东正教十字
    "\U0000262A"             # 星月
    "\U0000262E-\U0000262F"  # 和平、阴阳
    "\U00002638-\U0000263A"  # 法轮、笑脸
    "\U00002640"             # 女性符号
    "\U00002642"             # 男性符号
    "\U00002648-\U00002653"  # 星座符号
    "\U00002668"             # 温泉
    "\U0000267B"             # 回收符号
    "\U0000267E-\U0000267F"  # 无限、轮椅
    "\U00002692-\U00002697"  # 锤子等工具
    "\U00002699"             # 齿轮
    "\U0000269B-\U0000269C"  # 原子、百合
    "\U000026A0-\U000026A1"  # 警告、闪电 ⚠⚡
    "\U000026A7"             # 跨性别符号
    "\U000026AA-\U000026AB"  # 白/黑圈
    "\U000026B0-\U000026B1"  # 棺材、骨灰盒
    "\U000026BD-\U000026BE"  # 足球、棒球
    "\U000026C4-\U000026C5"  # 雪人、太阳云
    "\U000026C8"             # 雷雨云
    "\U000026CE"             # 蛇夫座
    "\U000026CF"             # 镐
    "\U000026D1"             # 头盔
    "\U000026D3-\U000026D4"  # 链条、禁止
    "\U000026E9-\U000026EA"  # 神社、教堂
    "\U000026F0-\U000026F5"  # 山、滑雪等
    "\U000026F7-\U000026FA"  # 滑雪者、帐篷等
    "\U000026FD"             # 加油站
    "]",  # 不用+，每次只匹配单个emoji
    flags=re.UNICODE,
)


class FileResult(NamedTuple):
    """单个文件的处理结果"""
    path: str
    emoji_count: int
    emojis_found: list[str]


def find_emojis_regex(text: str) -> list[str]:
    """使用正则表达式查找emoji"""
    return EMOJI_PATTERN.findall(text)


def remove_emojis_regex(text: str) -> str:
    """使用正则表达式移除emoji"""
    return EMOJI_PATTERN.sub("", text)


def find_emojis_lib(text: str) -> list[str]:
    """使用emoji库查找emoji"""
    return [char for char in text if char in emoji.EMOJI_DATA]


def remove_emojis_lib(text: str) -> str:
    """使用emoji库移除emoji"""
    return emoji.replace_emoji(text, replace="")


# 根据是否安装了emoji库选择实现
if HAS_EMOJI_LIB:
    find_emojis: Callable[[str], list[str]] = find_emojis_lib
    remove_emojis: Callable[[str], str] = remove_emojis_lib
else:
    find_emojis = find_emojis_regex
    remove_emojis = remove_emojis_regex


def scan_file_streaming(file_path: Path) -> list[str]:
    """流式扫描大文件中的emoji"""
    emojis: list[str] = []
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                emojis.extend(find_emojis(line))
    except (PermissionError, OSError):
        pass
    return emojis


def process_file_streaming(file_path: Path) -> bool:
    """流式处理大文件，删除emoji，返回是否成功"""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=file_path.suffix
        ) as tmp:
            tmp_path = Path(tmp.name)
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    tmp.write(remove_emojis(line))

        # 替换原文件
        shutil.move(str(tmp_path), str(file_path))
        return True
    except (PermissionError, OSError):
        # 清理临时文件
        if tmp_path.exists():
            tmp_path.unlink()
        return False


def is_large_file(file_path: Path) -> bool:
    """判断是否是大文件"""
    try:
        return file_path.stat().st_size > LARGE_FILE_THRESHOLD
    except OSError:
        return False


def process_file(file_path: Path, dry_run: bool = False) -> tuple[FileResult | None, bool]:
    """处理单个文件，返回 (处理结果, 是否因无法读取而跳过)"""
    # 大文件使用流式扫描
    if is_large_file(file_path):
        emojis = scan_file_streaming(file_path)
        if not emojis:
            return None, False
        return FileResult(
            path=str(file_path),
            emoji_count=len(emojis),
            emojis_found=emojis,
        ), False

    # 小文件一次性读取
    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError, OSError):
        # 无法读取的文件（二进制文件等）
        return None, True

    emojis = find_emojis(content)
    if not emojis:
        return None, False

    return FileResult(
        path=str(file_path),
        emoji_count=len(emojis),
        emojis_found=emojis,
    ), False


class ProgressBar:
    """简单的进度条实现"""

    def __init__(self, total: int, width: int = 40, desc: str = ""):
        self.total = total
        self.width = width
        self.desc = desc
        self.current = 0
        self.last_percent = -1

    def update(self, n: int = 1, filename: str = "") -> None:
        """更新进度"""
        self.current += n
        percent = int(self.current * 100 / self.total) if self.total > 0 else 100

        # 只在百分比变化时更新显示，减少闪烁
        if percent != self.last_percent or filename:
            self.last_percent = percent
            filled = int(self.width * self.current / self.total) if self.total > 0 else self.width
            bar = "█" * filled + "░" * (self.width - filled)

            # 截断过长的文件名
            display_name = filename
            if len(display_name) > 30:
                display_name = "..." + filename[-27:]

            status = f"\r{self.desc} |{bar}| {percent:3d}% ({self.current}/{self.total}) {display_name:<30}"
            sys.stdout.write(status)
            sys.stdout.flush()

    def finish(self) -> None:
        """完成进度条"""
        sys.stdout.write("\n")
        sys.stdout.flush()


class ScanResult(NamedTuple):
    """扫描结果"""
    files: list[FileResult]
    skipped_extensions: set[str]


def scan_directory(
    target_dir: Path,
    extensions: list[str] | None = None,
    excludes: list[str] | None = None,
    dry_run: bool = False,
) -> ScanResult:
    """递归扫描目录并处理文件"""
    # 第一步：收集所有需要处理的文件，同时记录跳过的扩展名
    files_to_process: list[Path] = []
    skipped_extensions: set[str] = set()

    for root, _, files in os.walk(target_dir):
        for filename in files:
            file_path = Path(root) / filename
            suffix = file_path.suffix.lower()

            # 过滤文件扩展名 (白名单)
            if extensions:
                if suffix not in extensions:
                    if suffix:
                        skipped_extensions.add(suffix)
                    continue

            # 排除文件扩展名 (黑名单)
            if excludes:
                if suffix in excludes:
                    if suffix:
                        skipped_extensions.add(suffix)
                    continue

            files_to_process.append(file_path)

    # 第二步：带进度条处理文件
    results: list[FileResult] = []
    total = len(files_to_process)

    if total == 0:
        return ScanResult(files=results, skipped_extensions=skipped_extensions)

    progress = ProgressBar(total, desc="扫描中")

    for file_path in files_to_process:
        progress.update(filename=file_path.name)
        result, was_skipped = process_file(file_path, dry_run)
        if result:
            results.append(result)
        elif was_skipped:
            # 记录因无法读取而跳过的文件类型
            suffix = file_path.suffix.lower()
            if suffix:
                skipped_extensions.add(suffix)

    progress.finish()
    return ScanResult(files=results, skipped_extensions=skipped_extensions)


def print_report(results: list[FileResult], skipped_extensions: set[str], dry_run: bool = False) -> None:
    """打印处理报告"""
    if not results:
        print("\n没有发现包含emoji的文件")
        if skipped_extensions:
            print(f"已跳过文件类型: {', '.join(sorted(skipped_extensions))}")
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
    if skipped_extensions:
        print(f"已跳过文件类型: {', '.join(sorted(skipped_extensions))}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="批量扫描并删除文件中的emoji表情",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python noemoji.py ./docs              # 扫描docs文件夹
  python noemoji.py ./src --dry-run     # 预览模式，不实际删除
  python noemoji.py . --ext .md .txt    # 只处理.md和.txt文件
  python noemoji.py . --exclude .md     # 排除.md文件
  python noemoji.py . -x .md .json      # 排除多种文件类型

提示:
  安装 emoji 库可获得更精确的匹配: pip install emoji
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
    parser.add_argument(
        "--exclude", "-x",
        nargs="+",
        type=str,
        help="排除指定扩展名的文件 (例如: --exclude .md .json)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="跳过确认，直接执行删除",
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

    excludes = None
    if args.exclude:
        excludes = [ext if ext.startswith(".") else f".{ext}" for ext in args.exclude]

    print(f"扫描目录: {target_path}")
    if args.dry_run:
        print("模式: 预览 (不修改文件)")
    if extensions:
        print(f"包含类型: {', '.join(extensions)}")
    if excludes:
        print(f"排除类型: {', '.join(excludes)}")

    # 显示使用的检测方式
    if HAS_EMOJI_LIB:
        print("检测引擎: emoji库 (精确模式)")
    else:
        print("检测引擎: 正则表达式 (安装emoji库可更精确: pip install emoji)")

    # 先执行预览扫描
    scan_result = scan_directory(target_path, extensions, excludes, dry_run=True)
    print_report(scan_result.files, scan_result.skipped_extensions, dry_run=True)

    # 如果是预览模式或没有找到emoji，直接返回
    if args.dry_run or not scan_result.files:
        return 0

    # 询问用户确认
    if not args.yes:
        print()
        try:
            confirm = input("确认删除以上emoji? (yes/no): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n已取消")
            return 0

        if confirm not in ("yes", "y"):
            print("已取消")
            return 0

    # 执行实际删除
    print("\n执行删除...")
    for result in scan_result.files:
        file_path = Path(result.path)
        try:
            if is_large_file(file_path):
                # 大文件流式处理
                if not process_file_streaming(file_path):
                    print(f"  处理失败 {file_path}", file=sys.stderr)
            else:
                # 小文件一次性处理
                content = file_path.read_text(encoding="utf-8")
                cleaned = remove_emojis(content)
                file_path.write_text(cleaned, encoding="utf-8")
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            print(f"  处理失败 {file_path}: {e}", file=sys.stderr)

    total_emojis = sum(r.emoji_count for r in scan_result.files)
    print(f"\n完成! 共清理 {len(scan_result.files)} 个文件，删除 {total_emojis} 个emoji")

    return 0


if __name__ == "__main__":
    sys.exit(main())
