import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Optional
import logging
import shutil
from datetime import datetime

def setup_logger(app_name="app", project_root=None, console_output=True):
    """配置日志系统
    
    Args:
        app_name: 应用名称，用于日志目录
        project_root: 项目根目录，默认为当前文件所在目录
        console_output: 是否输出到控制台，默认为True
        
    Returns:
        logging: 配置好的 logging 模块
    """
    # 获取项目根目录
    if project_root is None:
        project_root = Path(__file__).parent.resolve()
    
    # 配置基本日志格式
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 使用 datetime 构建日志路径
    current_time = datetime.now()
    date_str = current_time.strftime("%Y-%m-%d")
    hour_str = current_time.strftime("%H")
    minute_str = current_time.strftime("%M%S")
    
    # 构建日志目录和文件路径
    log_dir = os.path.join(project_root, "logs", app_name, date_str, hour_str)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{minute_str}.log")
    
    # 添加文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logging.getLogger().addHandler(file_handler)
    
    # 如果不需要控制台输出，移除默认的StreamHandler
    if not console_output:
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                logging.getLogger().removeHandler(handler)
                break
    
    logging.info(f"日志系统已初始化，应用名称: {app_name}")
    return logging

def load_config(config_path=None):
    """从配置文件加载配置
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认路径
        
    Returns:
        dict: 配置字典
    """
    # 如果未指定配置文件路径，则使用默认路径
    if config_path is None:
        config_path = Path(__file__).parent / "config.json"
    else:
        config_path = Path(config_path)
        
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logging.info(f"✅ 已加载配置文件: {config_path}")
            return config
        else:
            logging.warning(f"⚠️ 配置文件不存在: {config_path}，将使用默认配置")
            return {}
    except Exception as e:
        logging.error(f"❌ 加载配置文件时出错: {e}，将使用默认配置")
        return {}

def is_artist_folder(path: Path) -> bool:
    """判断是否为画师文件夹（包含[]标记）
    
    Args:
        path: 路径对象
    
    Returns:
        bool: 是否为画师文件夹
    """
    return '[' in path.name and ']' in path.name

def find_artist_folders(base_path: Path) -> List[Path]:
    """查找给定路径下的所有画师文件夹
    
    Args:
        base_path: 基础路径
        
    Returns:
        List[Path]: 找到的画师文件夹列表
    """
    artist_folders = []
    
    try:
        # 确保路径存在
        base_path = Path(base_path).resolve()
        if not base_path.exists():
            logging.error(f"路径不存在: {base_path}")
            return []
            
        # 如果基础路径本身是画师文件夹，直接添加
        if is_artist_folder(base_path):
            artist_folders.append(base_path)
            
        # 遍历基础路径下的所有目录
        for entry in base_path.iterdir():
            if entry.is_dir() and is_artist_folder(entry):
                artist_folders.append(entry)
                
        logging.info(f"在 {base_path} 下找到 {len(artist_folders)} 个画师文件夹")
        return artist_folders
        
    except Exception as e:
        logging.error(f"查找画师文件夹时出错: {e}")
        return []

def create_compare_folder(base_path: Path) -> Optional[Path]:
    """在基础路径下创建比较文件夹
    
    Args:
        base_path: 基础路径
        
    Returns:
        Optional[Path]: 创建的比较文件夹路径，如果创建失败则返回None
    """
    try:
        compare_folder = base_path / "#compare"
        compare_folder.mkdir(exist_ok=True)
        logging.info(f"创建比较文件夹: {compare_folder}")
        return compare_folder
    except Exception as e:
        logging.error(f"创建比较文件夹时出错: {e}")
        return None

def move_matching_folders(source_path: Path, compare_folder: Path, exclude_folders: List[Path]) -> List[Path]:
    """将符合条件的文件夹移动到比较文件夹
    
    Args:
        source_path: 源路径
        compare_folder: 比较文件夹路径
        exclude_folders: 排除的文件夹列表（画师文件夹）
        
    Returns:
        List[Path]: 移动后的文件夹路径列表
    """
    moved_folders = []
    
    try:
        # 确保路径存在
        if not source_path.exists() or not compare_folder.exists():
            logging.error(f"源路径或比较文件夹不存在")
            return []
            
        # 将排除文件夹转换为绝对路径，便于比较
        exclude_paths = [folder.resolve() for folder in exclude_folders]
        
        # 遍历源路径下的所有目录
        for entry in source_path.iterdir():
            if not entry.is_dir():
                continue
                
            # 如果是比较文件夹本身，跳过
            if entry.resolve() == compare_folder.resolve():
                continue
                
            # 如果在排除列表中，跳过
            if entry.resolve() in exclude_paths:
                logging.info(f"跳过排除的文件夹: {entry}")
                continue
                
            # 移动文件夹到比较文件夹
            try:
                target_path = compare_folder / entry.name
                
                # 如果目标路径已存在，添加时间戳后缀
                if target_path.exists():
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    target_path = compare_folder / f"{entry.name}_{timestamp}"
                
                # 移动文件夹
                shutil.move(str(entry), str(target_path))
                logging.info(f"已移动文件夹: {entry} -> {target_path}")
                moved_folders.append(target_path)
                
            except Exception as e:
                logging.error(f"移动文件夹 {entry} 时出错: {e}")
        
        return moved_folders
        
    except Exception as e:
        logging.error(f"移动匹配文件夹时出错: {e}")
        return []

def generate_czkawka_paths(artist_folder: Path, compare_folder: Path) -> str:
    """生成czkawka路径字符串（用分号连接）
    
    Args:
        artist_folder: 画师文件夹路径
        compare_folder: 比较文件夹路径
        
    Returns:
        str: 用分号连接的路径字符串
    """
    return f"{artist_folder};{compare_folder}"

def save_to_intro_md(paths_str: str, output_file: Path) -> bool:
    """将路径字符串保存到intro.md文件
    
    Args:
        paths_str: 路径字符串
        output_file: 输出文件路径
        
    Returns:
        bool: 是否保存成功
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(paths_str)
        logging.info(f"已将路径保存到: {output_file}")
        return True
    except Exception as e:
        logging.error(f"保存路径到文件时出错: {e}")
        return False

def process_folder_for_czkawka(base_path: Path, output_file: Path) -> Tuple[bool, Optional[str]]:
    """处理文件夹，准备czkawka路径
    
    Args:
        base_path: 基础路径
        output_file: 输出文件路径
        
    Returns:
        Tuple[bool, Optional[str]]: 
            - 是否处理成功
            - 生成的路径字符串（如果成功）
    """
    try:
        # 查找画师文件夹
        artist_folders = find_artist_folders(base_path)
        if not artist_folders:
            logging.error(f"未找到画师文件夹")
            return False, None
            
        # 选择第一个画师文件夹（或让用户选择）
        artist_folder = artist_folders[0]
        if len(artist_folders) > 1:
            print("\n找到多个画师文件夹:")
            for i, folder in enumerate(artist_folders, 1):
                print(f"{i}. {folder}")
                
            while True:
                try:
                    choice = input("\n请选择画师文件夹编号 (直接回车选择第一个): ").strip()
                    if not choice:
                        break
                        
                    index = int(choice) - 1
                    if 0 <= index < len(artist_folders):
                        artist_folder = artist_folders[index]
                        break
                    else:
                        print("❌ 无效的选择，请重试")
                except ValueError:
                    print("❌ 请输入有效的数字")
        
        # 创建比较文件夹
        compare_folder = create_compare_folder(base_path)
        if not compare_folder:
            return False, None
            
        # 移动符合条件的文件夹到比较文件夹
        moved_folders = move_matching_folders(base_path, compare_folder, [artist_folder])
        
        # 生成czkawka路径字符串
        paths_str = generate_czkawka_paths(artist_folder, compare_folder)
        
        # 保存路径字符串到输出文件
        if not save_to_intro_md(paths_str, output_file):
            return False, paths_str
        
        return True, paths_str
        
    except Exception as e:
        logging.error(f"处理文件夹时出错: {e}")
        return False, None

def main():
    """主函数"""
    # 设置日志
    setup_logger(app_name="czkawka_helper")
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("用法: python -m kavvka.czkawka_helper <基础路径> [输出文件路径]")
        return
        
    # 获取基础路径
    base_path = Path(sys.argv[1])
    if not base_path.exists():
        logging.error(f"基础路径不存在: {base_path}")
        return
        
    # 获取输出文件路径
    output_file = None
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        # 默认输出到intro.md
        output_file = Path(__file__).parent / "doc" / "intro.md"
    
    # 确保输出目录存在
    try:
        os.makedirs(output_file.parent, exist_ok=True)
    except Exception as e:
        logging.error(f"无法创建输出目录: {e}")
        return
        
    # 处理文件夹
    success, paths_str = process_folder_for_czkawka(base_path, output_file)
    
    if success:
        print(f"✅ 处理成功！路径已保存到: {output_file}")
        print(f"生成的路径: {paths_str}")
    else:
        print("❌ 处理失败，请查看日志获取详细信息")

if __name__ == "__main__":
    main() 