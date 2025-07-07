#!/usr/bin/env python
"""
Kavvka测试脚本

用法：
    python test_kavvka.py <基础路径> [输出文件路径]
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kavvka.czkawka_helper import process_folder_for_czkawka, setup_logger

def main():
    """主函数"""
    # 设置日志
    logger = setup_logger(app_name="kavvka_test")
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("用法: python test_kavvka.py <基础路径> [输出文件路径]")
        return 1
    
    # 获取基础路径
    base_path = Path(sys.argv[1])
    if not base_path.exists():
        print(f"❌ 基础路径不存在: {base_path}")
        return 1
    
    # 获取输出文件路径（可选）
    output_file = None
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    
    # 处理文件夹
    success, paths_str = process_folder_for_czkawka(base_path, output_file)
    
    if success:
        print(f"✅ 处理成功！")
        if output_file:
            print(f"路径已保存到: {output_file}")
        print(f"生成的路径: {paths_str}")
        
        # 显示如何在Czkawka中使用
        print("\n在Czkawka中使用:")
        print("1. 打开Czkawka")
        print("2. 在'包含目录'中手动添加以下路径:")
        print(f"   {paths_str}")
        print("3. 使用Czkawka的重复文件或相似图片功能进行比较")
        return 0
    else:
        print("❌ 处理失败，请查看日志获取详细信息")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 