# Windows 10 应用打包和部署说明

## 前置条件

### 1. 安装 Python 和依赖

首先确保在 Windows 上安装了 Python 3.7 以上版本，然后安装必要的包：

```bash
pip install PyInstaller vosk sounddevice
```

### 2. 准备文件

确保以下文件都在同一目录中：
- `speech_to_text_unified.py` - 主程序
- `corrections.json` - 纠正规则配置
- `vosk-model-small-cn-0.22/` - 语音识别模型文件夹

## 打包方法

### 方法 A: 使用自动化脚本（推荐）

Windows 命令行中运行：

```bash
python build_windows_app.py
```

脚本会自动：
- 检查依赖是否安装
- 创建必要的配置文件
- 打包成 `dist/语音转文字.exe`

### 方法 B: 手动使用 PyInstaller

```bash
pyinstaller --name=语音转文字 --onefile --windowed ^
    --add-data="corrections.json;." ^
    --add-data="vosk-model-small-cn-0.22;vosk-model-small-cn-0.22" ^
    --hidden-import=vosk ^
    --hidden-import=sounddevice ^
    speech_to_text_unified.py
```

## 打包后的部署

### 结构
```
dist/
├── 语音转文字.exe          # 主应用程序
├── corrections.json        # 配置文件（可选）
└── vosk-model-small-cn-0.22/  # 语音模型（可选）
```

### 发布方式

#### 选项 1: 便携版（推荐）
- 将 `dist` 文件夹重命名为 `语音转文字`
- 用户直接运行 `语音转文字.exe` 即可
- 无需安装，可以放在 U 盘或网盘分享

#### 选项 2: 创建安装程序
使用 NSIS 或 Inno Setup 创建专业的安装程序（见下面的说明）

#### 选项 3: 绿色版压缩包
- 将 `dist/语音转文字.exe` 及其依赖文件打成 ZIP 压缩包
- 用户解压后即可使用

## 常见问题

### 问题 1: 模型文件太大
**现象**: 打包失败或生成的 exe 太大  
**解决方案**:
1. 不包含模型文件打包：删除 `--add-data=vosk-model-small-cn-0.22` 参数
2. 用户在首次运行时自动下载模型
3. 或分开发布：程序包和模型包分开

### 问题 2: 找不到模型文件
**现象**: 运行 exe 时提示模型不存在  
**解决方案**:
1. 确保 `vosk-model-small-cn-0.22` 在 exe 同目录
2. 修改程序中的模型路径为相对路径

### 问题 3: 缺少 DLL 文件
**现象**: 运行报错关于 DLL 文件  
**解决方案**:
```bash
# 安装 Visual C++ 可再发行组件包
# https://support.microsoft.com/zh-cn/help/2977003
```

## 进阶：创建安装程序

### 使用 Inno Setup

1. 下载安装 Inno Setup: https://jrsoftware.org/isdl.php

2. 创建 `installer.iss` 文件：

```ini
[Setup]
AppName=语音转文字
AppVersion=1.0
DefaultDirName={pf}\语音转文字
DefaultGroupName=语音转文字
OutputDir=dist
OutputBaseFilename=语音转文字-安装程序
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\语音转文字.exe"; DestDir: "{app}"
Source: "dist\corrections.json"; DestDir: "{app}"
Source: "dist\vosk-model-small-cn-0.22\*"; DestDir: "{app}\vosk-model-small-cn-0.22"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\语音转文字"; Filename: "{app}\语音转文字.exe"
Name: "{commondesktop}\语音转文字"; Filename: "{app}\语音转文字.exe"

[Run]
Filename: "{app}\语音转文字.exe"; Description: "运行语音转文字"; Flags: nowait postinstall skipifsilent
```

3. 在 Inno Setup 中打开此文件并编译

### 使用 NSIS

类似的过程，需要编写 `.nsi` 脚本文件

## 优化 exe 大小

如果生成的 exe 过大，可以：

1. **使用 UPX 压缩**（可选）：
```bash
pip install upx
# build_windows_app.py 已包含此选项
```

2. **排除不必要的模块**：
```bash
pyinstaller --exclude-module=numpy speech_to_text_unified.py
```

3. **分开模型文件**：
   - 程序单独打包（较小）
   - 模型文件单独下载

## 发布清单

- [ ] exe 文件可正常运行
- [ ] 测试中文输入输出
- [ ] 测试麦克风工作正常
- [ ] 测试 corrections.json 自定义规则
- [ ] 测试 GUI 界面完整
- [ ] 编写 README.md 说明文档
- [ ] 测试在干净的 Windows 环境中运行
- [ ] 上传到分享平台（如微博云盘、百度网盘等）

## 分享和部署

### 制作便携版（最简单）
```bash
# 1. 打包后进入 dist 文件夹
cd dist

# 2. 将所有文件压成 zip
# 右键点击 -> 发送到 -> 压缩文件夹

# 3. 重命名为有意义的名称，如：
# 语音转文字-v1.0.zip
```

用户下载后直接解压即可运行。

### 使用 GitHub Releases
1. 将项目上传到 GitHub
2. 编译生成 exe
3. 在 Releases 页面上传 zip 文件
4. 用户可以直接下载

## 疑难排除

如果还有问题，尝试：

1. **检查 Python 环境**：
```bash
python --version
pip list | findstr PyInstaller
```

2. **查看详细错误**：
```bash
pyinstaller --debug=all speech_to_text_unified.py
```

3. **使用分开打包**（分离模型文件）：
```bash
pyinstaller --onefile --windowed speech_to_text_unified.py
# 然后手动复制 corrections.json 和 vosk-model-small-cn-0.22 到 dist 文件夹
```

祝打包顺利！如有问题欢迎反馈。
