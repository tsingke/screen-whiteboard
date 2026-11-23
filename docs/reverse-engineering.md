# 屏幕白板教学软件 · 逆向分析报告

本文记录对一个 Windows 屏幕白板教学软件样本的结构分析、载荷提取、应用逻辑还原，以及由此催生的开源重实现。所有分析均在本地对合法获取的样本进行，目标是理解文件格式与交互设计，不涉及绕过授权或破解付费功能。

## 1. 样本信息

| 项目 | 值 |
|---|---|
| 文件名 | `屏幕白板教学软件.exe` |
| 大小 | 16,333,312 字节 |
| SHA-256 | `2c61025d5798ef487d1fdaa0d75522386dd02828ff5af3ccecc85784663b1124` |
| 格式 | PE32+ executable (GUI) x86-64 |
| 子系统 | Windows GUI（`Subsystem = 2`） |
| 数字签名 | 无 |
| 构建时间戳 | 2026-10-25 14:27:57 UTC（核心 DLL 的 PE 时间戳） |

样本目录中另有一份未修改的备份。本文以当前样本为准，并在涉及修改痕迹时单独说明。

## 2. 初步识别

### 2.1 节表

| 节 | 虚拟大小 | 原始大小 | 熵 | 说明 |
|---|---|---|---|---|
| `.text` | 0x1E700 | 0x1E800 | 6.51 | 引导程序与静态 CRT |
| `.rdata` | 0xF60F32 | 0xF61000 | 7.999 | 常量数据 + 加密/压缩载荷 |
| `.data` | 0x2A5C0 | 0xC00 | 1.78 | 已初始化全局数据 |
| `.pdata` | 0x1650 | 0x1800 | 5.02 | 异常处理表 |
| `.rsrc` | 0x111AC | 0x11200 | 5.96 | 图标、清单 |
| `.reloc` | 0x678 | 0x800 | 4.92 | 重定位 |

`.text` 只有约 124 KB，而 `.rdata` 接近 16 MB 且熵接近 8.0，说明真正的程序不在引导代码里，而是以高熵数据块的形式嵌在 `.rdata` 中。

### 2.2 导入表

只导入 `KERNEL32.dll` 与 `SHELL32.dll`，函数组合非常具有辨识度：

- `AddDllDirectory`、`SetDllDirectoryW`、`GetShortPathNameW`、`LoadLibraryExW`
- `CreateProcessW`、`WaitForSingleObject`、`GetExitCodeProcess`、`TerminateProcess`
- `K32GetModuleFileNameExW`、`OpenProcess`
- `SHFileOperationW`、`SHGetFolderPathW`、`CommandLineToArgvW`
- `GetTempPathW`、`CreateDirectoryW`、`FindFirstFileExW`

这组 API 是 Nuitka `--onefile` 引导器的典型特征：创建临时目录、解包运行时、以子进程方式启动解包后的程序、退出时清理临时目录。

### 2.3 载荷定位

在文件中搜索 zstd 帧魔数 `28 B5 2F FD`，在偏移 `0x1EF90` 处发现：

```text
0001ef90  4b 41 59 28 b5 2f fd 00 88 a4 a0 02 ...
          K  A  Y  |-- zstd frame --|
```

`KA` 是 Nuitka onefile 的魔数前缀，第三个字节 `Y` 表示压缩方式。其后紧跟一个完整的 zstd 帧。载荷不是附加在文件末尾的 overlay，而是作为常量数组编译进 `.rdata`，因此文件末尾看不到 `MEI` 或附加数据长度字段。

## 3. 载荷格式与提取

### 3.1 解压

从 `0x1EF93` 开始按 zstd 解压，得到 **49,265,884 字节** 的明文载荷。

解压时要注意帧后面还跟着 PE 对齐数据。直接用 `zstd` CLI 可以正常处理；用 Python `zstandard` 时应使用 `decompressobj()`，在 `obj.eof` 为真后停止喂入，否则会报 `Unknown frame descriptor`。

### 3.2 容器结构

明文载荷是若干条记录的简单拼接：

```text
repeat:
    filename   UTF-16LE，以 0x0000 结尾
    size       uint64 little-endian
    data       size 字节
```

第一条记录的文件名就是 `屏幕白板教学软件.dll`，长度 13,997,056 字节，紧跟其后的是 MZ/PE 头。这个 DLL 是 Nuitka 编译后的主程序模块（原源码文件名为 `屏幕白板教学软件.pyw`）。

### 3.3 提取结果

共 33 个文件，合计 49,264,740 字节（其余为文件名与长度字段）：

| 大小 | 文件 |
|---:|---|
| 13,997,056 | `屏幕白板教学软件.dll` |
| 7,832,064 | `PIL\_avif.pyd` |
| 6,792,928 | `python314.dll` |
| 6,021,880 | `libcrypto-3.dll` |
| 3,369,299 | `tcl90.dll` |
| 2,476,032 | `PIL\_imaging.pyd` |
| 2,138,360 | `tcl9tk90.dll` |
| 1,308,920 | `libssl-3.dll` |
| 1,081,329 | `tcl.zip` |
| 758,496 | `unicodedata.pyd` |
| 503,520 | `_zstd.pyd` |
| 410,112 | `PIL\_webp.pyd` |
| 295,568 | `tk.zip` |
| 290,016 | `_decimal.pyd` |
| 269,824 | `PIL\_imagingcms.pyd` |
| 201,440 | `pyexpat.pyd` |
| 192,224 | `_ssl.pyd` |
| 178,616 | `vcruntime140.dll` |
| 160,992 | `_lzma.pyd` |
| 143,072 | `_ctypes.pyd` |
| 138,976 | `_elementtree.pyd` |
| 102,912 | `zlib1.dll` |
| 87,776 | `_bz2.pyd` |
| 87,776 | `_socket.pyd` |
| 81,408 | `libtommath.dll` |
| 70,880 | `_tkinter.pyd` |
| 69,344 | `_hashlib.pyd` |
| 50,112 | `vcruntime140_1.dll` |
| 40,160 | `_wmi.pyd` |
| 39,696 | `libffi-8.dll` |
| 33,504 | `select.pyd` |
| 25,600 | `PIL\_imagingmath.pyd` |
| 14,848 | `PIL\_imagingtk.pyd` |

为避免手工抄录误差，建议直接运行提取工具获取准确清单：

```bash
python tools/nuitka_onefile_extract.py 屏幕白板教学软件.exe --list
```

### 3.4 运行时版本

| 组件 | 版本线索 |
|---|---|
| Python | 3.14.8（`Python 3.14.8 (8e6e75d...)`） |
| Nuitka | 旧版 onefile 布局（`Onefile.c`、`_NUITKA_ONEFILE_COMPRESSION_BOOL`、`KA` 魔数） |
| Pillow | 13（`Pillow 13 (2026-10-15)`） |
| Tcl/Tk | 9.0（`tcl90.dll`、`tcl9tk90.dll`、`tcl.zip`、`tk.zip`） |
| 运行库 | MSVC 静态 CRT + `vcruntime140.dll` |

## 4. 应用逻辑还原

Nuitka 把 Python 编译成机器码，不会保留原始 `.py`。不过编译产物仍保留了模块名、类名、方法名、局部变量名、字符串常量与事件绑定，足以还原完整的交互逻辑。

### 4.1 模块结构

主模块 `__main__` 只包含一个类：

```text
MyCapture
├── __init__
├── leftbutton_down
├── leftbutton_move
├── change_property
└── capture
```

`__init__` 的静态属性列表：

```text
width  height  top  canvas  image  background  fg  pen_width
```

### 4.2 界面与窗口

从常量池可还原出如下调用序列：

```python
tkinter
root = tk.Tk()
width  = root.winfo_screenwidth()
height = root.winfo_screenheight()

top = tk.Toplevel(...)
top.overrideredirect(True)
top.geometry(...)
top.attributes('-top', True)      # Tk 接受 '-top' 作为 '-topmost' 的前缀缩写

canvas = tk.Canvas(top, width=..., height=..., bg='white')
canvas.pack(fill='both', expand=True)

image = ImageGrab.grab()
background = ImageTk.PhotoImage(image.resize((width, height)))
canvas.create_image(0, 0, anchor='nw', image=background)

self.fg = 'red'
self.pen_width = ...
```

悬浮按钮位于屏幕右上角：

```python
geometry('-20+10')                 # 距右边缘 20px，距顶部 10px
Button(text='开始手写', bg='blue', command=self.capture)
bind('<ButtonRelease-3>', ...)      # 右键退出
```

`leftbutton_down` / `leftbutton_move` 里出现了 `x0`、`y0`、`newX`、`newY`、`winfo_x`、`winfo_y`，说明按钮窗口支持按住左键拖动：

```python
newX = top.winfo_x() + event.x - x0
newY = top.winfo_y() + event.y - y0
top.geometry(f'+{newX}+{newY}')
```

### 4.3 事件绑定与快捷键

恢复出的事件序列：

```text
<Button-1>          开始一笔
<B1-Motion>         拖动绘制
<Key>               快捷键
<Escape>            退出标注模式
<ButtonRelease-3>   右键退出程序
```

`change_property` 中出现的常量：

```text
create_line  fill  width  char
colors: r -> red, g -> green, b -> blue
find_all  delete
ImageGrab  grab
asksaveasfilename  title='保存截图'  filetypes='*.jpg *.png'
endswith  '.jpg'  '.png'  save  quality  destroy
'123456789'
```

据此可确定：

| 按键 | 行为 |
|---|---|
| R / G / B | 切换红、绿、蓝 |
| 1 ~ 9 | 切换线条粗细 |
| C | 清除线条 |
| S | 保存屏幕截图 |
| Esc | 退出画线模式 |

保存流程是：先 `ImageGrab.grab()` 重新抓一次屏，再弹出另存为对话框，按扩展名保存 JPG（带 `quality`）或 PNG，最后 `destroy()` 关闭标注层。因此在保存瞬间出现的其他窗口也会被拍进图片，这是原实现的一个小缺陷。

### 4.4 使用说明文件

主模块在启动时会写一个 UTF-8 文本文件：

```text
屏幕白板教学软件使用说明.txt
```

内容包含：软件用途、点击右上角按钮进入标注、按钮可拖动、右键退出、R/G/B 换色、1~9 换粗细、C 清除、S 保存、Esc 退出。写完后调用 `os.startfile` 自动打开该文件。

当前样本中，说明文本里的作者署名已被替换为空白；`os.startfile` 的目标位置在打包内的 `python314.dll` 中被改为空操作，因此启动时仍会生成 txt，但不会自动弹出。

### 4.5 DPI

常量池中出现：

```text
windll  shcore  SetProcessDpiAwareness
```

说明程序通过 `ctypes.windll.shcore.SetProcessDpiAwareness(...)` 声明 DPI 感知，避免高缩放比例下画布与鼠标坐标错位。

## 5. 安全性评估

| 检查项 | 结果 |
|---|---|
| 网络访问 | 应用层未发现 HTTP 客户端、套接字或上传逻辑 |
| 开机自启 | 未发现 `Run` 注册表键、计划任务或启动目录写入 |
| 进程/命令执行 | 引导器用 `CreateProcessW` 启动解包后的程序，属 Nuitka 正常机制 |
| 数据外传 | 未发现 |
| 写文件 | 启动时在当前目录写说明 txt；保存截图时写用户选择的路径 |
| 打包内含网络模块 | `_ssl.pyd`、`_socket.pyd` 等来自 Python/Pillow 依赖，不代表应用使用 |

结论：行为与「屏幕标注 + 保存截图」的定位一致，没有发现恶意行为。建议仍在隔离环境或有备份的机器上运行来历不明的可执行文件。

## 6. 复现步骤

```bash
# 1. 查看文件类型与哈希
file 屏幕白板教学软件.exe
shasum -a 256 屏幕白板教学软件.exe

# 2. 用本仓库的工具列出内嵌文件
python -m pip install zstandard
python tools/nuitka_onefile_extract.py 屏幕白板教学软件.exe --list

# 3. 完整提取（输出到独立目录）
python tools/nuitka_onefile_extract.py 屏幕白板教学软件.exe -o extracted

# 4. 查看主模块中的中文常量
python - <<'PY'
import re
data = open('extracted/屏幕白板教学软件.dll', 'rb').read()
for m in re.finditer(rb'(?:[\xe4-\xe9][\x80-\xbf]{2}){2,}', data):
    try:
        print(m.group().decode('utf-8'))
    except UnicodeDecodeError:
        pass
PY
```

## 7. 提取工具的实现要点

`tools/nuitka_onefile_extract.py` 不依赖样本特征，适用于同类旧版 Nuitka onefile 程序：

1. 在整份文件中搜索 `28 B5 2F FD`，检查前三个字节是否为 `KA?`，得到候选载荷。
2. 依次尝试 zstd 解压；用 `decompressobj()` 在帧结束时停止，容忍尾部对齐数据。
3. 按 `[UTF-16LE 文件名][u64 长度][数据]` 解析条目，校验长度与边界。
4. 文件名做目录穿越与绝对路径过滤，默认把 `PIL\x.pyd` 这类内部路径扁平化为 `PIL__x.pyd`。
5. 只写文件，不执行、不加载。

若目标使用了新版 Nuitka 的 overlay 布局（载荷附在文件末尾、末尾 8 字节为长度），当前版本会找不到嵌入载荷；这种情况可按 Nuitka `Onefile.c` 中的 `getAttachedPayloadEndOffset()` 逻辑扩展。

## 8. 对重实现的启示

原始软件的功能非常克制：一个悬浮按钮、一层冻结画面、几个快捷键。重实现保留了这套心智模型，并针对实际课堂使用做了以下调整：

| 问题 | 原实现 | 本仓库 |
|---|---|---|
| 清空 | `find_all()` 会把背景图一起删掉 | 用 `ink` 标签区分笔迹，只清笔迹 |
| 保存 | 重新抓屏，可能拍到其他窗口 | 在原始截图上离屏重绘 |
| 误操作 | 无法撤销 | Ctrl+Z |
| 多显示器 | 只截主屏 | Windows 支持虚拟桌面 |
| 启动打扰 | 每次写并打开说明 txt | 应用内说明，仅首次显示 |
| 平台 | 仅 Windows | Windows / macOS / Linux |
| 高 DPI | 系统级 DPI 感知 | Per-Monitor V2，失败降级 |

由于 Nuitka 产物不保留源码，本仓库的 Python 代码是依据行为与常量重新编写的，没有复制原始实现。数值型默认值（例如初始线宽）在常量表中无法可靠区分，重实现采用了自己的默认值并写入配置系统。

## 9. 局限

- 未逐个反编译 Nuitka 生成的机器码函数，因此不能保证每一行控制流与原始程序完全一致。
- 原始软件的图标、说明文本、作者信息等资源未纳入本仓库。
- 未对打包内的 Python 运行时、Tcl/Tk、Pillow 做逐字节完整性审计，仅按公开版本特征识别。
- 样本为 2026 年构建的 Nuitka 旧版布局；Nuitka 后续版本可能改变载荷封装方式。

## 10. 法律与伦理

本次分析针对本地持有的一份 Windows 软件，目的是学习其文件封装与交互设计，并据此编写独立实现。仓库不包含原始程序的二进制、反编译源码、图标或说明文本，也不提供任何绕过授权、去除限制或再次分发原软件的能力。若你是原始软件的权利人并认为本文有不妥之处，请通过仓库 Issue 联系。
