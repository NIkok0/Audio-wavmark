#!/usr/bin/env python3
import os
import time
import argparse
from typing import List

DEFAULT_PATHS = [
    os.path.join('instance', 'uploads'),
    os.path.join('instance', 'embeds'),
    os.path.join('instance', 'extracts'),
]


def human_size(num_bytes: int) -> str:
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            fpath = os.path.join(dirpath, name)
            # 仅处理常规文件
            if os.path.isfile(fpath):
                yield fpath


def clean_once(paths: List[str], expire_days: int, dry_run: bool = False, prune_empty: bool = False) -> int:
    now = time.time()
    expire_seconds = expire_days * 24 * 3600
    deleted_count = 0

    for base in paths:
        if not base:
            continue
        if not os.path.isabs(base):
            base = os.path.abspath(base)
        if not os.path.exists(base):
            continue

        for fpath in iter_files(base):
            try:
                age = now - os.path.getmtime(fpath)
                if age > expire_seconds:
                    if dry_run:
                        print(f"[cleaner][dry-run] would delete: {fpath}")
                    else:
                        try:
                            size = os.path.getsize(fpath)
                        except Exception:
                            size = 0
                        os.remove(fpath)
                        deleted_count += 1
                        print(f"[cleaner] deleted: {fpath} ({human_size(size)})")
            except FileNotFoundError:
                # 竞争条件：文件可能已被其他进程删除
                continue
            except Exception as e:
                print(f"[cleaner] failed: {fpath} -> {e}")

        if prune_empty:
            # 自底向上清理空目录（仅在base内部）
            for dirpath, dirnames, filenames in os.walk(base, topdown=False):
                try:
                    if not dirnames and not filenames:
                        if dry_run:
                            print(f"[cleaner][dry-run] would rmdir: {dirpath}")
                        else:
                            os.rmdir(dirpath)
                            print(f"[cleaner] rmdir: {dirpath}")
                except Exception as e:
                    print(f"[cleaner] rmdir failed: {dirpath} -> {e}")

    return deleted_count


def main():
    parser = argparse.ArgumentParser(description='清理 instance 下各用户的过期文件（按天）')
    parser.add_argument(
        '-p', '--paths', nargs='*', default=DEFAULT_PATHS,
        help='要扫描的目录列表（默认：instance/uploads instance/embeds instance/extracts instance/temp）'
    )
    parser.add_argument(
        '-d', '--expire-days', type=int, default=7,
        help='删除最后修改时间超过 N 天的文件（默认：7）'
    )
    parser.add_argument(
        '-i', '--interval', type=int, default=3000,
        help='循环扫描周期（秒）。为 0 时只执行一次（默认：0）'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='仅打印将要删除的文件，不实际删除,用来测试打印日志机制 但不正真删除文件'
    )
    parser.add_argument(
        '--prune-empty', action='store_true',
        help='删除清理后产生的空目录'
    )

    args = parser.parse_args()

    # 规范化路径，过滤不存在的路径
    paths = []
    for p in args.paths:
        if not p:
            continue
        paths.append(p)

    if args.interval <= 0:
        clean_once(paths, args.expire_days, dry_run=args.dry_run, prune_empty=args.prune_empty)
        return

    # 循环模式
    try:
        while True:
            print(f"[cleaner] scanning paths: {', '.join(paths)}; expire_days={args.expire_days}; dry_run={args.dry_run}")
            clean_once(paths, args.expire_days, dry_run=args.dry_run, prune_empty=args.prune_empty)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('[cleaner] interrupted by user')


if __name__ == "__main__":
    main()
