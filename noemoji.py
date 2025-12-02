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
import sys
from pathlib import Path
from typing import Callable, NamedTuple

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
    "\U00002934-\U00002935"  # 箭头
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
    "\U000025AA-\U000025AB"  # 小方块
    "\U000025B6"             # 播放按钮
    "\U000025C0"             # 倒放按钮
    "\U000025FB-\U000025FE"  # 方块
    "\U00002600-\U00002604"  # 太阳、云等天气
    "\U0000260E"             # 电话
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
    "\U0000265F-\U00002660"  # 国际象棋
    "\U00002663"             # 梅花
    "\U00002665-\U00002666"  # 红心、方块
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
    "]+",
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
        cleaned = remove_emojis(content)
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

    # 显示使用的检测方式
    if HAS_EMOJI_LIB:
        print("检测引擎: emoji库 (精确模式)")
    else:
        print("检测引擎: 正则表达式 (安装emoji库可更精确: pip install emoji)")

    results = scan_directory(target_path, extensions, args.dry_run)
    print_report(results, args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
