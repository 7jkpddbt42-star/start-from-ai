#!/usr/bin/env python3
"""
Windows 应用打包脚本
将 speech_to_text_unified.py 打包成独立的 exe 文件
"""

import os
import shutil
import subprocess
import sys

def check_pyinstaller():
    """检查是否安装了 PyInstaller"""
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("请运行: pip install PyInstaller")
        return False

def build_app():
    """打包应用"""
    print("\n开始打包 Windows 应用...")
    
    # PyInstaller 命令
    cmd = [
        'pyinstaller',
        '--name=语音转文字',  # 应用名称
        '--onefile',  # 打包成单个 exe 文件
        '--windowed',  # GUI 应用，不显示控制台窗口
        '--icon=app.ico',  # 图标（如果存在）
        '--add-data=corrections.json:.',  # 包含配置文件
        '--add-data=vosk-model-small-cn-0.22:vosk-model-small-cn-0.22',  # 包含语音模型
        '--hidden-import=vosk',
        '--hidden-import=sounddevice',
        'speech_to_text_unified.py'
    ]
    
    try:
        print(f"运行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        print("\n✓ 打包成功！")
        print(f"exe 文件位置: dist/语音转文字.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False

def create_spec_file():
    """创建更详细的 spec 文件以支持中文路径"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, get_module_file_attribute
import os

block_cipher = None

a = Analysis(
    ['speech_to_text_unified.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('corrections.json', '.'),
        ('vosk-model-small-cn-0.22', 'vosk-model-small-cn-0.22'),
    ],
    hiddenimports=['vosk', 'sounddevice'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='语音转文字',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
)
'''
    
    with open('speech_to_text_unified.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✓ 已创建 speech_to_text_unified.spec 文件")

def main():
    print("=" * 50)
    print("Windows 应用打包工具")
    print("=" * 50)
    
    # 检查依赖
    if not check_pyinstaller():
        return False
    
    # 检查必要文件
    required_files = ['speech_to_text_unified.py', 'corrections.json']
    for f in required_files:
        if not os.path.exists(f):
            print(f"✗ 缺少文件: {f}")
            return False
    
    print("✓ 所有必要文件都存在")
    
    # 检查模型文件
    if not os.path.exists('vosk-model-small-cn-0.22'):
        print("\n⚠ 警告: 未找到语音模型文件")
        print("模型文件应位于: vosk-model-small-cn-0.22")
        print("你可以在打包后手动添加到 dist 文件夹中")
    
    # 创建 spec 文件
    create_spec_file()
    
    # 执行打包
    print("\n" + "=" * 50)
    success = build_app()
    print("=" * 50)
    
    if success:
        print("\n✓ 打包完成！")
        print("\n下一步:")
        print("1. 检查 dist 文件夹中的 语音转文字.exe")
        print("2. 如果模型文件未包含，请手动复制 vosk-model-small-cn-0.22 到 dist 文件夹")
        print("3. 也可以复制 corrections.json 到 dist 文件夹进行自定义")
        return True
    else:
        print("\n✗ 打包失败，请检查错误信息")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
