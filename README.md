# NoEmoji

批量扫描并删除文件中的 emoji 表情。

AI 生成的代码和文档经常包含大量 emoji，这个工具可以帮你快速清理。

## 功能特点

- 递归扫描目录
- 精确匹配 emoji
- 支持文件类型白名单/黑名单过滤
- 支持 .gitignore 过滤
- 删除前预览确认
- 实时进度条显示
- 统计每个文件删除的 emoji 数量
- 大文件流式处理（>10MB）
- 多进程并行扫描
- 零依赖，开箱即用（可选安装 emoji 库提高精度）

## 安装

```bash
# 克隆项目
git clone https://github.com/black8848/noemoji.git
cd noemoji

# 可选：安装 emoji 库以获得更精确的匹配
pip install emoji
```

## 使用方法

```bash
# 基本用法 - 扫描目录，预览后确认删除 - 请认真查看预览列表，避免误删 HTML/XML 字符实体映射的文件
python noemoji.py ./your_project

# 预览模式 - 只查看，不删除
python noemoji.py ./your_project --dry-run

# 只处理指定类型文件
python noemoji.py ./your_project --ext .md .txt .py

# 排除指定类型文件
python noemoji.py ./your_project --exclude .json .yml

# 使用多进程加速扫描（自动检测核心数）
python noemoji.py ./your_project -w

# 自动跳过 .gitignore 中的文件
python noemoji.py ./your_project -g

# 查看所有参数用法
python noemoji.py ./your_project --help
```

## 参数说明

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `target` | - | 目标文件夹路径（必填） |
| `--dry-run` | `-n` | 预览模式，只显示不删除 |
| `--ext` | `-e` | 白名单，只处理指定扩展名 |
| `--exclude` | `-x` | 黑名单，排除指定扩展名 |
| `--yes` | `-y` | 跳过确认，直接执行删除 |
| `--workers` | `-w` | 启用多进程并行（自动检测核心数） |
| `--gitignore` | `-g` | 跳过被 .gitignore 忽略的文件 |
| `--help` | `-h` | 显示帮助信息 |

## 输出示例

```
扫描目录: /path/to/project
检测引擎: 正则表达式 (安装emoji库可更精确: pip install emoji)
扫描中 |████████████████████████████████████████| 100% (15/15) example.md

[预览模式] 处理报告
============================================================
  /path/to/project/docs/guide.md
    数量: 12  内容: 😀🎉✨🚀📝🔥💡...
  /path/to/project/README.md
    数量: 5  内容: ⭐🎯📌...
============================================================
共处理 2 个文件，发现 17 个emoji
已跳过文件类型: .jpg, .png, .gif

确认删除以上emoji? (yes/no):
```

## 工作流程

1. 扫描目标目录下的所有文件
2. 根据白名单/黑名单过滤文件类型
3. 检测每个文件中的 emoji
4. 显示预览报告
5. 等待用户确认（除非使用 `--yes` 或 `--dry-run`）
6. 执行删除并显示结果

## 注意事项

- 默认会跳过二进制文件（如图片、视频等）
- 建议先使用 `--dry-run` 预览，确认无误后再执行
- 处理 `node_modules` 等第三方库目录时，建议使用 `-g` 参数，这会让程序自动忽略 .gitignore 以及 .git/ 下的文件
- 安装 `emoji` 库可获得更精确的匹配：`pip install emoji`
- 在较大项目中，推荐使用白名单一个一个类型删除，做好版本控制，避免误删实体映射的文件

## 支持的 Emoji 范围

默认正则表达式覆盖：

- 表情符号（笑脸、手势等）
- 动物、食物、活动图标
- 交通、地图符号
- 旗帜
- 常见装饰符号（星星、爱心、对错号等）

## License

MIT
