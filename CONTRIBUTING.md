# 贡献指南

## 开发环境

- Python 3.9 及以上
- PySide6（Qt 6.6 及以上）
- 建议使用虚拟环境

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

测试使用 Qt 的 offscreen 平台，不需要真实桌面：

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

## 提交规范

- 一个提交只做一件事，提交信息用 `feat:`、`fix:`、`docs:`、`test:`、`refactor:` 前缀
- 新增快捷键或配置项时同步更新 README、应用内说明与单元测试
- 修改绘制逻辑时说明对高 DPI、多显示器或性能的影响

## Pull Request

1. Fork 仓库并从 `main` 拉出分支
2. 保证单元测试全部通过，并通过 `ruff check screen_whiteboard tools tests main.py`
3. 在 PR 描述里说明动机、行为和验证方式
4. 涉及界面的改动请附截图或录屏

## 代码风格

- 使用 4 空格缩进
- 公共函数写类型标注与简短 docstring
- 优先使用 Qt 原生绘制，避免引入额外的图像处理依赖
- 不引入新的运行时依赖，除非有充分理由
- 不做与当前改动无关的重排或格式化

## 性能与清晰度

- 标注层采用增量绘制，避免每帧重绘全部笔迹
- 所有坐标使用逻辑像素，渲染时按 `devicePixelRatio` 放大到物理像素
- 新增绘制功能时请在 Retina / 200% 缩放下检查边缘是否发虚
