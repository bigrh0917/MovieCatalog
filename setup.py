import os
import sys
from PyInstaller.__main__ import run

# 确保当前工作目录是脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 定义PyInstaller的参数
args = [
    'main.py',  # 主脚本
    '--name=电影目录管理系统',  # 应用程序名称
    '--onefile',  # 生成单个可执行文件
    '--windowed',  # 不显示控制台窗口
    '--icon=NONE',  # 可以替换为自定义图标
    '--add-data=movies.db;.',  # 添加数据库文件
    '--add-data=movie;movie',  # 添加movie文件夹
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不询问确认
]

# 运行PyInstaller
run(args)

print('打包完成！可执行文件位于dist文件夹中。')