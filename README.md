# autoClick 自动识图点击

`sequence_click.py` 会按顺序在屏幕上找图片并点击，每轮间隔随机几十秒，一直循环。`auto_click.py` 提供识图和点击的基础功能，也可以单独使用。

## 一、新设备准备工作

### 1. 安装 Python

- 到 <https://www.python.org/downloads/> 下载 Python 3.9 或更高版本（本机用的是 3.13）。
- 安装时勾选 **Add python.exe to PATH**。
- 装好后打开命令行检查：

```bash
python --version
pip --version
```

### 2. 安装依赖库

```bash
pip install opencv-python numpy mss pyautogui
```

国内网络下载慢可以加清华镜像：

```bash
pip install opencv-python numpy mss pyautogui -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 拷贝文件

把整个文件夹拷到新电脑，至少包含：

```text
autoClick/
├─ auto_click.py
├─ sequence_click.py
└─ images/
   ├─ 1.png
   └─ 2.png
```

`sequence_click.py` 依赖 `auto_click.py`，两个文件必须放在同一个目录。

### 4. 在新电脑上重新截图

识图是按像素比对的。新电脑的分辨率、缩放比例（100%/125%/150%）、主题或目标程序的窗口大小只要和截图时不同，旧图片就可能匹配不上。所以建议在新电脑上重新截一遍：

1. 打开目标程序，让要点击的按钮显示出来。
2. 按 `Win + Shift + S`，框选按钮区域。
3. 保存为 PNG，覆盖 `images/1.png`、`images/2.png`（文件名要和脚本配置里一致）。

截图建议：

- 截带文字或图标的区域，不要截纯色块，否则容易点错位置。
- 只截按钮本身，周围少带会变化的背景。

### 5. 管理员权限

如果目标程序是"以管理员身份运行"的，脚本也必须用管理员权限运行，否则 Windows 会拦截点击。做法：右键"命令提示符"或"终端"，选"以管理员身份运行"，再在里面启动脚本。

脚本启动时如果提示"当前不是管理员权限"，而点击又没反应，就是这个原因。

## 二、使用教程

### 1. 先试运行（不点击）

```bash
cd 脚本所在目录
python sequence_click.py --dry-run
```

`--dry-run` 只识别图片并打印坐标和相似度，不会真的点击。看到类似下面的输出，说明图片能找到：

```text
第 1 轮 (10:15:02)
  [找到] 1.png (812, 455) 相似度 0.987
  [找到] 2.png (1020, 630) 相似度 0.962
```

如果显示 `[跳过] 10 秒内没找到 1.png`，说明图片没匹配上，回到"新电脑上重新截图"那一步。

### 2. 正式运行

```bash
python sequence_click.py
```

运行流程：每一轮依次找 `images/1.png` 双击，再找 `images/2.png` 单击；一轮做完后等到随机间隔结束，再开始下一轮。

### 3. 停止脚本

- 在命令行窗口按 `Ctrl + C`；
- 或者把鼠标快速甩到屏幕任意一个角落，触发安全停止。

### 4. 修改配置

打开 `sequence_click.py`，改 `===== 配置区 =====` 里的值：

| 配置项 | 当前值 | 含义 |
| --- | --- | --- |
| `STEPS` | 1.png 点 2 次，2.png 点 1 次 | 点击步骤，按列表顺序执行。每项是 `(图片路径, 点击次数)`，1 是单击，2 是双击 |
| `ROUND_SECONDS` | `(42, 50)` | 每轮间隔在这个范围内随机，单位秒 |
| `THRESHOLD` | `0.8` | 匹配阈值 0~1。找不到图可以调低到 0.7；点错地方就调高 |
| `STEP_TIMEOUT` | `10` | 每一步最多等多少秒，超时就跳过这一步 |
| `STEP_DELAY` | `2.0` | 每次点击后等多少秒，给界面反应时间 |
| `SCAN_INTERVAL` | `0.3` | 等图片出现时，多久截一次屏 |

增加步骤的例子（加第三步：单击 `images/3.png`）：

```python
STEPS = [
    (BASE / "images" / "1.png", 2),
    (BASE / "images" / "2.png", 1),
    (BASE / "images" / "3.png", 1),
]
```

> 注意：两个 `.py` 文件是 **GB2312 编码**。用 VS Code 打开如果中文是乱码，点右下角的编码 →"通过编码重新打开"→ 选 GB2312，改完也要用 GB2312 保存，否则运行会报错或中文乱码。

### 5. 单独使用 auto_click.py

只想点一张图时可以直接用：

```bash
python auto_click.py images/1.png                      # 找到就点一次，然后退出
python auto_click.py images/1.png images/2.png --loop  # 一直扫描，看到哪张点哪张
python auto_click.py images/1.png --dry-run            # 只识别不点击
python auto_click.py images/1.png --clicks 2           # 双击
python auto_click.py --help                            # 查看全部参数
```

### 6. 常见问题

| 现象 | 原因和处理 |
| --- | --- |
| 一直提示没找到图片 | 截图和当前屏幕不一致。重新截图，或把 `THRESHOLD` 调低 |
| 能找到但点击没反应 | 目标程序是管理员运行的，用管理员终端启动脚本 |
| 点到了别的地方 | 截图太小或是纯色，换一个特征更明显的区域；或调高 `THRESHOLD` |
| 运行时报 `No module named ...` | 依赖没装，重新执行"安装依赖库"那一步 |

## 三、打包成 exe

打包后的 exe 可以在没装 Python 的 Windows 电脑上直接运行。

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 打包

在脚本所在目录执行：

```bash
pyinstaller --onefile --add-data "images;images" sequence_click.py
```

- `--onefile`：打成单个 exe 文件。
- `--add-data "images;images"`：把 `images` 文件夹一起打进去，分号前是源目录，分号后是 exe 里的目录。
- `auto_click.py` 会被自动打包进去，不用另外指定。
- 不要加 `-w` / `--noconsole`，脚本需要命令行窗口来显示输出和按 `Ctrl + C` 停止。

如果目标程序是管理员运行的，可以加 `--uac-admin`，双击 exe 时会自动弹出管理员授权：

```bash
pyinstaller --onefile --uac-admin --add-data "images;images" sequence_click.py
```

### 3. 打包结果

- 生成的文件在 `dist/sequence_click.exe`，把这个文件发给别人即可。
- `build/` 文件夹和 `sequence_click.spec` 是中间文件，可以删掉。
- 双击 exe 会打开一个黑色命令行窗口并开始运行。想先试运行，在命令行里执行 `sequence_click.exe --dry-run`。

### 4. 注意事项

- 图片和配置都打包在 exe 里面。换电脑后要重新截图，或者改了配置，都需要重新打包。
- 如果希望换图片时不用重新打包，去掉 `--onefile`：

  ```bash
  pyinstaller --add-data "images;images" sequence_click.py
  ```

  生成的是 `dist/sequence_click/` 文件夹，整个文件夹一起拷走。图片在 `dist/sequence_click/_internal/images/` 里，直接替换同名文件就能生效。
- 杀毒软件有时会把 PyInstaller 打的 exe 误报为病毒，添加信任即可。
- 打包用的电脑和运行 exe 的电脑最好都是 64 位 Windows 10 或更新版本。
