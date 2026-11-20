# -*- coding: gb2312 -*-
"""
识别屏幕中的图片并点击。

用法示例:
    python auto_click.py images/button.png                 # 找到一次就点击，然后退出
    python auto_click.py images/a.png images/b.png --loop  # 持续扫描，找到哪个点哪个
    python auto_click.py images/button.png --dry-run       # 只识别并打印坐标，不点击
    python auto_click.py images/button.png --threshold 0.9 --interval 1 --button right

停止: Ctrl+C，或把鼠标快速移到屏幕左上角 (pyautogui 防故障机制)。
"""

import argparse
import ctypes
import sys
import time
from pathlib import Path

import cv2
import mss
import numpy as np


def enable_dpi_awareness():
    """让截图坐标和鼠标坐标一致 (缩放 125%/150%、多显示器缩放不同时必须)。

    必须在 import pyautogui 之前调用: pyautogui 导入时会把进程设成"系统 DPI 感知"，
    之后再设置就会失败，导致缩放不同的副屏上点击位置偏移。
    """
    if sys.platform != "win32":
        return
    # 每显示器 DPI 感知 V2 (Win10 1703+)
    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except Exception:
        pass
    try:
        if ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0:  # 每显示器 DPI 感知 (Win8.1+)
            return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


enable_dpi_awareness()  # 导入时立即执行，赶在 pyautogui 之前

import pyautogui  # noqa: E402  必须放在 enable_dpi_awareness() 之后


def warn_if_not_admin():
    """目标程序以管理员运行时，非管理员进程发出的点击会被 Windows 拦截 (UIPI)。"""
    if sys.platform != "win32":
        return
    try:
        admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return
    if not admin:
        print("[提示] 当前不是管理员权限。如果目标程序是以管理员运行的，点击会无效，"
              "请用“以管理员身份运行”的终端启动本脚本。")


def click_at(x, y, clicks=1, button="left", hold=0.2, interval=0.5):
    """先移动并停留，再按下-保持-松开。比 pyautogui.click 的瞬间点击兼容更多程序。"""
    pyautogui.moveTo(x, y)
    time.sleep(0.1)  # 让目标窗口先收到鼠标移入/悬停
    for i in range(clicks):
        pyautogui.mouseDown(button=button)
        time.sleep(hold)
        pyautogui.mouseUp(button=button)
        if i < clicks - 1:
            time.sleep(interval)


def load_image(path):
    """读取图片为灰度图，支持中文路径。"""
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"无法读取图片: {path}")
    return img


def grab_screen(sct, region=None):
    """截屏，返回 (灰度图, 左上角在屏幕中的坐标)。region = (left, top, width, height)。"""
    if region:
        left, top, width, height = region
        mon = {"left": left, "top": top, "width": width, "height": height}
    else:
        mon = sct.monitors[0]  # 所有显示器组成的整个虚拟屏幕
    shot = np.array(sct.grab(mon))  # BGRA
    gray = cv2.cvtColor(shot, cv2.COLOR_BGRA2GRAY)
    return gray, (mon["left"], mon["top"])


def find_template(screen, template, threshold):
    """在 screen 中查找 template，返回 (中心x, 中心y, 相似度) 或 None。"""
    th, tw = template.shape[:2]
    sh, sw = screen.shape[:2]
    if th > sh or tw > sw:
        return None
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < threshold:
        return None
    return max_loc[0] + tw // 2, max_loc[1] + th // 2, max_val


def parse_args():
    p = argparse.ArgumentParser(description="识别屏幕中的图片并点击")
    p.add_argument("templates", nargs="+", help="要查找的图片文件 (可多个)")
    p.add_argument("--threshold", type=float, default=0.8, help="匹配阈值 0~1，越高越严格 (默认 0.8)")
    p.add_argument("--loop", action="store_true", help="持续扫描，不在第一次点击后退出")
    p.add_argument("--interval", type=float, default=0.5, help="两次扫描间隔秒数 (默认 0.5)")
    p.add_argument("--timeout", type=float, default=0, help="非 loop 模式下最长等待秒数，0 表示一直等")
    p.add_argument("--button", choices=["left", "right", "middle"], default="left", help="鼠标按键")
    p.add_argument("--clicks", type=int, default=1, help="点击次数，2 为双击")
    p.add_argument("--offset", type=int, nargs=2, default=(0, 0), metavar=("DX", "DY"),
                   help="点击位置相对图片中心的偏移")
    p.add_argument("--region", type=int, nargs=4, metavar=("LEFT", "TOP", "W", "H"),
                   help="只在屏幕的这个区域内查找")
    p.add_argument("--dry-run", action="store_true", help="只识别并打印坐标，不点击")
    return p.parse_args()


def main():
    args = parse_args()
    enable_dpi_awareness()
    warn_if_not_admin()
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05

    templates = []
    for t in args.templates:
        path = Path(t)
        img = load_image(path)
        if img.std() < 15:
            print(f"[警告] {path.name} 几乎是纯色，容易误匹配，建议截取带文字/图标的区域。")
        templates.append((path.name, img))
    print(f"已加载 {len(templates)} 张图片，阈值 {args.threshold}。Ctrl+C 停止。")

    start = time.time()
    make_sct = mss.MSS if hasattr(mss, "MSS") else mss.mss
    with make_sct() as sct:
        while True:
            screen, (ox, oy) = grab_screen(sct, args.region)
            clicked = False
            for name, tpl in templates:
                hit = find_template(screen, tpl, args.threshold)
                if not hit:
                    continue
                cx, cy, score = hit
                x = ox + cx + args.offset[0]
                y = oy + cy + args.offset[1]
                if args.dry_run:
                    print(f"[找到] {name} 位置 ({x}, {y}) 相似度 {score:.3f}")
                else:
                    click_at(x, y, clicks=args.clicks, button=args.button)
                    print(f"[点击] {name} 位置 ({x}, {y}) 相似度 {score:.3f}")
                clicked = True
                break  # 每轮只点一个，点完重新截图

            if clicked and not args.loop:
                return 0
            if not args.loop and args.timeout and time.time() - start > args.timeout:
                print("超时，未找到目标图片。")
                return 1
            time.sleep(args.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已停止。")
    except pyautogui.FailSafeException:
        print("\n鼠标移到了屏幕角落，已触发安全停止。")
