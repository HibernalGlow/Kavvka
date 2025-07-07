from pathlib import Path
import sys
import argparse
from src.kavvka.czkawka_helper import process_folder_for_czkawka, setup_logger

def parse_args():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='Kavvka - Czkawka辅助工具')
    parser.add_argument('path', type=str, help='要处理的基础路径')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径（默认为src/kavvka/doc/intro.md）')
    return parser.parse_args()

def main():
    """主函数"""
    # 设置日志
    logger = setup_logger(app_name="kavvka_main")
    
    # 解析命令行参数
    args = parse_args()
    
    # 获取基础路径
    base_path = Path(args.path)
    if not base_path.exists():
        print(f"❌ 基础路径不存在: {base_path}")
        return 1
    
    # 获取输出文件路径（可选）
    output_file = None
    if args.output:
        output_file = Path(args.output)
    else:
        # 默认输出到intro.md
        output_file = Path(__file__).parent / "src" / "kavvka" / "doc" / "intro.md"
    
    # 处理文件夹
    success, paths_str = process_folder_for_czkawka(base_path, output_file)
    
    if success:
        print(f"✅ 处理成功！路径已保存到: {output_file}")
        print(f"生成的路径: {paths_str}")
        return 0
    else:
        print("❌ 处理失败，请查看日志获取详细信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
