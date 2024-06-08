# PilotFatigueMonitoring

## 项目结构

### 独立包
tobii-python: 眼动仪相关操作（已独立为包）
flet-page-manager: 用于支持 flet 多页面

```
emotion: 情感识别
fatiuge: 疲劳识别
monitor: 一些与项目强相关的内容
monitor/database: 数据库相关操作
monitor/gui: 图形用户界面 -> monitor/database, emotion, fatiuge

tests: 测试用例
tools: 一些工具，用于数据库初始化等
example: 例子

```

## install
安装 python、git、pip
```bash
pip install pdm pre-commit
pre-commit install 
pdm install
```

### ubuntu
maybe
apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0

## TODO
- refactor pages (complete)
- rm file_manager (complete)
- schult (complete)
- remove record_cache (complete)
- 全屏化 (deprecated)
- unittest
- error except
- page build 机制优化


## 打包说明
```bash
pyinstaller main.py --collect-all flet
```


## flet page manager 改进
找不到页面应该是error不是info （完成）
