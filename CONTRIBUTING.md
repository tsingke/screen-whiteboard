# 贡献指南

## 开发环境

- Python 3.8 及以上
- Pillow 9 及以上
- Tk（Windows/macOS 官方 Python 自带；Debian/Ubuntu 需安装 `python3-tk`）

```bash
python -m pip install -r requirements.txt
python -m pip install zstandard   # 提取工具的测试需要
python -m unittest discover -s tests -v
```

## 提交规范

- 一个提交只做一件事，提交信息用 `feat:`、`fix:`、`docs:`、`test:`、`refactor:` 前缀
- 新增快捷键或配置项时同步更新 README 与 `docs/reverse-engineering.md`
- 修改交互逻辑时补充或更新对应单元测试

## Pull Request

1. Fork 仓库并从 `main` 拉出分支
2. 保证 `python -m unittest discover -s tests -v` 全部通过
3. 在 PR 描述里说明动机、行为和验证方式
4. 涉及界面的改动请附截图或录屏

## 代码风格

- 使用 4 空格缩进
- 公共函数写类型标注与简短 docstring
- 不引入新的运行时依赖，除非有充分理由
- 不做与当前改动无关的重排或格式化

## 逆向工具

`tools/nuitka_onefile_extract.py` 只允许做字节级解析，不得加入执行、加载或自动启动被提取内容的逻辑。提交样本相关问题时请勿上传完整的商业软件二进制。
