# -*- coding: gb2312 -*-
"""
按顺序点击多张图片，整体循环执行。

每一轮: 双击 images/1.png -> 单击 images/2.png，
每轮开始间隔随机 25~40 秒。

用法:
    python sequence_click.py            # 正常运行
    python sequence_click.py --dry-run  # 只识别打印坐标，不点击

停止: Ctrl+C，或把鼠标快速移到屏幕左上角。
"""

import argparse
import random
import sys
import time
from pathlib import Path

import mss

# auto_click 必须先于 pyautogui 导入，它会在导入时设置 DPI 感知
from auto_click import (click_at, enable_dpi_awareness, find_template, grab_screen,
                        load_image, warn_if_not_admin)
import pyautogui  # noqa: E402

BASE = Path(__file__).parent

# ===== 配置区，可按需修改 =====
STEPS = [
    # (图片路径, 点击次数)
    #(BASE / "images" / "1.png", 2),  # 双击
    (BASE / "images" / "1.png", 2),  # 单击
    (BASE / "images" / "2.png", 1),  # 单击
]
ROUND_SECONDS = (42, 50)  # 每轮间隔的随机范围 (秒)
THRESHOLD = 0.8           # 匹配阈值
STEP_TIMEOUT = 10         # 每一步最多等待图片出现的秒数，超时则跳过这一步
STEP_DELAY = 2.0          # 每步点击后等待的秒数，给界面反应时间
SCAN_INTERVAL = 0.3       # 等待图片时的扫描间隔
# ============================


def wait_and_click(sct, name, template, clicks, dry_run):
    """等待图片出现并点击，成功返回 True，超时返回 False。"""
    deadline = time.time() + STEP_TIMEOUT
    while time.time() < deadline:
        screen, (ox, oy) = grab_screen(sct)
        hit = find_template(screen, template, THRESHOLD)
        if hit:
            cx, cy, score = hit
            x, y = ox + cx, oy + cy
            action = "双击" if clicks == 2 else f"点击x{clicks}"
            if dry_run:
                action = "找到"
            else:
                click_at(x, y, clicks=clicks)
            print(f"  [{action}] {name} ({x}, {y}) 相似度 {score:.3f}")
            return True
        time.sleep(SCAN_INTERVAL)
    print(f"  [跳过] {STEP_TIMEOUT} 秒内没找到 {name}")
    return False


def main():
    p = argparse.ArgumentParser(description="按顺序点击图片并循环")
    p.add_argument("--dry-run", action="store_true", help="只识别不点击")
    args = p.parse_args()

    enable_dpi_awareness()
    warn_if_not_admin()
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05

    steps = [(path.name, load_image(path), clicks) for path, clicks in STEPS]
    print(f"已加载 {len(steps)} 步，每轮间隔 {ROUND_SECONDS[0]}~{ROUND_SECONDS[1]} 秒。Ctrl+C 停止。")

    make_sct = mss.MSS if hasattr(mss, "MSS") else mss.mss
    round_no = 0
    with make_sct() as sct:
        while True:
            round_no += 1
            start = time.time()
            period = random.uniform(*ROUND_SECONDS)
            print(f"第 {round_no} 轮 ({time.strftime('%H:%M:%S')})")

            for name, template, clicks in steps:
                if wait_and_click(sct, name, template, clicks, args.dry_run):
                    time.sleep(STEP_DELAY)

            wait = max(0, period - (time.time() - start))
            print(f"  本轮完成，{wait:.1f} 秒后开始下一轮")
            time.sleep(wait)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已停止。")
    except pyautogui.FailSafeException:
        print("\n鼠标移到了屏幕角落，已触发安全停止。")
