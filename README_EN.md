[中文](README.md) | **English**

# NoEmoji

Batch scan and remove emojis from files.

AI-generated code and documentation often contain excessive emojis. This tool helps you clean them up quickly.

## Features

- Recursive directory scanning
- Precise emoji matching
- File type whitelist/blacklist filtering
- .gitignore support
- Preview before deletion
- Real-time progress bar
- Per-file emoji count statistics
- Streaming processing for large files (>10MB)
- Multi-process parallel scanning
- Zero dependencies, ready to use (optional emoji library for better accuracy)

## Installation

```bash
# Clone the project
git clone https://github.com/black8848/noemoji.git
cd noemoji

# Optional: Install emoji library for more accurate matching
pip install emoji
```

## Usage

```bash
# Basic usage - scan directory, preview and confirm deletion
# Please review the preview list carefully to avoid accidentally deleting HTML/XML entity mapping files
python noemoji.py ./your_project

# Dry run mode - preview only, no deletion
python noemoji.py ./your_project --dry-run

# Process only specific file types
python noemoji.py ./your_project --ext .md .txt .py

# Exclude specific file types
python noemoji.py ./your_project --exclude .json .yml

# Use multi-process for faster scanning (auto-detect CPU cores)
python noemoji.py ./your_project -w

# Automatically skip files in .gitignore
python noemoji.py ./your_project -g

# View all options
python noemoji.py ./your_project --help
```

## Parameters

| Parameter | Short | Description |
|-----------|-------|-------------|
| `target` | - | Target directory path (required) |
| `--dry-run` | `-n` | Dry run mode, preview only |
| `--ext` | `-e` | Whitelist, process only specified extensions |
| `--exclude` | `-x` | Blacklist, exclude specified extensions |
| `--yes` | `-y` | Skip confirmation, execute directly |
| `--workers` | `-w` | Enable multi-process parallel (auto-detect cores) |
| `--gitignore` | `-g` | Skip files ignored by .gitignore |
| `--help` | `-h` | Show help message |

## Output Example

```
Scanning directory: /path/to/project
Detection engine: Regex (install emoji lib for better accuracy: pip install emoji)
Scanning |████████████████████████████████████████| 100% (15/15) example.md

[Dry Run] Processing Report
============================================================
  /path/to/project/docs/guide.md
    Count: 12  Content: 😀🎉✨🚀📝🔥💡...
  /path/to/project/README.md
    Count: 5  Content: ⭐🎯📌...
============================================================
Processed 2 files, found 17 emojis
Skipped file types: .jpg, .png, .gif

Confirm deletion of the above emojis? (yes/no):
```

## Workflow

1. Scan all files in the target directory
2. Filter file types based on whitelist/blacklist
3. Detect emojis in each file
4. Display preview report
5. Wait for user confirmation (unless using `--yes` or `--dry-run`)
6. Execute deletion and show results

## Notes

- Binary files (images, videos, etc.) are skipped by default
- It's recommended to use `--dry-run` first to preview, then execute after confirmation
- When processing `node_modules` or other third-party library directories, use `-g` flag to automatically ignore files in .gitignore and .git/
- Install `emoji` library for more accurate matching: `pip install emoji`
- For large projects, it's recommended to use whitelist to delete one file type at a time, maintain version control, and avoid accidental deletion of entity mapping files

## Supported Emoji Range

Default regex covers:

- Emoticons (smileys, gestures, etc.)
- Animals, food, activity icons
- Transportation, map symbols
- Flags
- Common decorative symbols (stars, hearts, check marks, etc.)

## License

MIT
