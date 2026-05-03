@echo off
chcp 65001 >nul
echo ========================================
echo Windows 应用打包工具
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ 未找到 Python，请先安装 Python 3.7 以上版本
    pause
    exit /b 1
)

echo ✓ Python 已安装

REM 检查 PyInstaller
pip show PyInstaller >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠ 开始安装依赖包...
    pip install PyInstaller vosk sounddevice
    if errorlevel 1 (
        echo ✗ 安装失败
        pause
        exit /b 1
    )
)

echo ✓ 依赖已就绪

REM 检查文件
if not exist "speech_to_text_unified.py" (
    echo ✗ 缺少文件: speech_to_text_unified.py
    pause
    exit /b 1
)

if not exist "corrections.json" (
    echo ✗ 缺少文件: corrections.json
    pause
    exit /b 1
)

echo ✓ 所有必要文件已检查

echo.
echo ========================================
echo 开始打包...
echo ========================================
echo.

REM 清理旧的构建文件
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del *.spec

REM 执行打包
pyinstaller --name=语音转文字 --onefile --windowed ^
    --add-data="corrections.json;." ^
    --hidden-import=vosk ^
    --hidden-import=sounddevice ^
    speech_to_text_unified.py

if errorlevel 1 (
    echo.
    echo ✗ 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ 打包成功！
echo ========================================
echo.
echo exe 文件位置: dist\语音转文字.exe
echo.
echo 下一步操作:
echo 1. 如果需要语音识别，请复制 vosk-model-small-cn-0.22 文件夹到 dist 文件夹
echo 2. 可选：将 corrections.json 复制到 dist 文件夹（用户可自定义规则）
echo 3. 将 dist 文件夹压缩，即可分享或部署
echo.
pause
