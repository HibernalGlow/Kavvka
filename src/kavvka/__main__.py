import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List
import logging
from datetime import datetime
import shutil
import pyperclip  # 用于复制到剪贴板

# 尝试导入依赖，如果不存在则提供友好的错误信息
try:
    from loguru import logger
except ImportError as e:
    module_name = str(e).split("'")[1]
    print(f"错误: 缺少必要的依赖 '{module_name}'")
    print("请安装所需依赖: pip install loguru pyperclip")
    sys.exit(1)

def parse_args():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='图片过滤工具')
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--workers', '-w', type=int, default=2, help='线程数')
    parser.add_argument('--force-update', '-f', action='store_true', help='强制更新哈希值')
    return parser.parse_args()

def setup_logger(app_name="app", project_root=None, console_output=True):
    """配置 Loguru 日志系统
    
    Args:
        app_name: 应用名称，用于日志目录
        project_root: 项目根目录，默认为当前文件所在目录
        console_output: 是否输出到控制台，默认为True
        
    Returns:
        logger: 配置好的 logger 实例
    """
    # 获取项目根目录
    if project_root is None:
        project_root = Path(__file__).parent.resolve()
    
    # 清除默认处理器
    logger.remove()
    
    # 有条件地添加控制台处理器（简洁版格式）
    if console_output:
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <blue>{elapsed}</blue> | <level>{level.icon} {level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
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
    logger.add(
        log_file,
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {elapsed} | {level.icon} {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,     )
    
    logger.info(f"日志系统已初始化，应用名称: {app_name}")
    return logger

# 设置日志
logger = setup_logger(app_name="artfilter", console_output=True)

# 加载配置文件
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
            logger.info(f"✅ 已加载配置文件: {config_path}")
            return config
        else:
            logger.warning(f"⚠️ 配置文件不存在: {config_path}，将使用默认配置")
            # 返回默认配置
            return {
                "worker_count": 2,
                "force_update": False,
            }
    except Exception as e:
        logger.error(f"❌ 加载配置文件时出错: {e}，将使用默认配置")
        # 返回默认配置
        return {
            "worker_count": 2,
            "force_update": False,
        }

# 解析命令行参数
args = parse_args()

# 加载配置
CONFIG = load_config(args.config)

# 使用命令行参数覆盖配置文件中的设置
if args.workers is not None:
    CONFIG["worker_count"] = args.workers
    logger.info(f"✅ 使用命令行参数设置线程数: {args.workers}")
    
if args.force_update:
    CONFIG["force_update"] = True
    logger.info(f"✅ 使用命令行参数设置强制更新: {CONFIG['force_update']}")

WORKER_COUNT = CONFIG.get("worker_count", 2)
FORCE_UPDATE = CONFIG.get("force_update", False)

def normalize_path(path_str):
    """规范化路径字符串，处理转义字符和特殊字符
    
    Args:
        path_str: 路径字符串
        
    Returns:
        str: 规范化后的路径字符串
    """
    # 移除引号
    path_str = path_str.strip().replace('"', '').replace("'", "")
    
    # 将反斜杠替换为正斜杠（在Windows上也有效）
    path_str = path_str.replace('\\', '/')
    
    # 处理特殊字符的转义
    path_str = path_str.replace('[', '\\[').replace(']', '\\]')
    
    return path_str

def get_artist_folder_from_path(path: Path) -> Optional[Path]:
    """从给定路径获取画师文件夹
    
    Args:
        path: 输入路径（可以是压缩包或文件夹）
        
    Returns:
        Optional[Path]: 画师文件夹路径
    """
    def is_artist_folder(p: Path) -> bool:
        """判断是否为画师文件夹"""
        return '[' in p.name and ']' in p.name
    
    try:
        path = Path(path).resolve()
        
        # 如果是压缩包，使用其所在目录
        if path.is_file() and path.suffix.lower() in ['.zip', '.7z', '.rar']:
            base_path = path.parent
        else:
            base_path = path
            
        # 向上查找画师文件夹
        current_path = base_path
        while current_path != current_path.parent:
            if is_artist_folder(current_path):
                if current_path.exists():
                    logger.info(f'✅ 找到画师文件夹: {current_path}')
                    confirm = input('是否使用该画师文件夹？(Y/n/输入新路径): ').strip()
                    if not confirm or confirm.lower() == 'y':
                        return current_path
                    elif confirm.lower() == 'n':
                        break  # 继续搜索当前目录下的其他画师文件夹
                    elif os.path.exists(confirm):
                        new_path = Path(confirm)
                        if is_artist_folder(new_path):
                            return new_path
                        else:
                            logger.info('❌ 输入的路径不是画师文件夹（需要包含[]标记）')
                            break
                    else:
                        logger.info('❌ 输入的路径不存在')
                        break
            current_path = current_path.parent
        
        # 如果向上查找没有找到或用户拒绝了，则搜索当前目录下的画师文件夹
        artist_folders = []
        for entry in base_path.iterdir():
            if entry.is_dir() and is_artist_folder(entry):
                artist_folders.append(entry)
                    
        if not artist_folders:
            logger.info(f'❌ 在路径 {base_path} 下未找到画师文件夹')
            return None
            
        if len(artist_folders) == 1:
            logger.info(f'✅ 找到画师文件夹: {artist_folders[0]}')
            confirm = input('是否使用该画师文件夹？(Y/n/输入新路径): ').strip()
            if not confirm or confirm.lower() == 'y':
                return artist_folders[0]
            elif confirm.lower() == 'n':
                return None
            elif os.path.exists(confirm):
                new_path = Path(confirm)
                if is_artist_folder(new_path):
                    return new_path
                else:
                    logger.info('❌ 输入的路径不是画师文件夹（需要包含[]标记）')
                    return None
            else:
                logger.info('❌ 输入的路径不存在')
                return None
            
        logger.info("\n找到以下画师文件夹:")
        for i, folder in enumerate(artist_folders, 1):
            logger.info(f"{i}. {folder}")
            
        # 让用户选择或输入新路径
        while True:
            choice = input("\n请选择画师文件夹编号或直接输入新路径 (输入n跳过，直接回车确认第一个): ").strip()
            if not choice:
                return artist_folders[0]
            elif choice.lower() == 'n':
                return None
                
            # 如果输入的是路径
            if os.path.exists(choice):
                new_path = Path(choice)
                if is_artist_folder(new_path):
                    return new_path
                else:
                    logger.info('❌ 输入的路径不是画师文件夹（需要包含[]标记）')
                    continue
                    
            # 如果输入的是编号
            try:
                index = int(choice) - 1
                if 0 <= index < len(artist_folders):
                    folder = artist_folders[index]
                    logger.info(f'✅ 已选择: {folder}')
                    confirm = input('是否使用该画师文件夹？(Y/n/输入新路径): ').strip()
                    if not confirm or confirm.lower() == 'y':
                        return folder
                    elif confirm.lower() == 'n':
                        continue
                    elif os.path.exists(confirm):
                        new_path = Path(confirm)
                        if is_artist_folder(new_path):
                            return new_path
                        else:
                            logger.info('❌ 输入的路径不是画师文件夹（需要包含[]标记）')
                            continue
                    else:
                        logger.info('❌ 输入的路径不存在')
                        continue
                logger.info('❌ 无效的选择，请重试')
            except ValueError:
                logger.info('❌ 请输入有效的数字或路径')
                
    except Exception as e:
        logger.info(f'❌ 获取画师文件夹时出错: {e}')
        return None

def create_compare_folder(base_path: Path) -> Path:
    """创建比较文件夹
    
    Args:
        base_path: 基础路径
        
    Returns:
        Path: 比较文件夹路径
    """
    compare_folder = base_path / "#compare"
    compare_folder.mkdir(exist_ok=True)
    logger.info(f"✅ 创建比较文件夹: {compare_folder}")
    return compare_folder

def move_folders_to_compare(base_path: Path, artist_folder: Path) -> List[Path]:
    """将除了画师文件夹外的其他同级文件夹移动到#compare文件夹
    
    Args:
        base_path: 基础路径
        artist_folder: 画师文件夹路径
        
    Returns:
        List[Path]: 移动后的文件夹路径列表
    """
    compare_folder = create_compare_folder(base_path)
    moved_folders = []
    
    # 遍历基础路径下的所有目录
    for entry in base_path.iterdir():
        # 跳过非目录、画师文件夹本身和#compare文件夹
        if not entry.is_dir() or entry.resolve() == artist_folder.resolve() or entry.name == "#compare":
            continue
        
        # 移动文件夹到#compare
        try:
            target_path = compare_folder / entry.name
            
            # 如果目标路径已存在，添加时间戳后缀
            if target_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                target_path = compare_folder / f"{entry.name}_{timestamp}"
            
            # 移动文件夹
            shutil.move(str(entry), str(target_path))
            logger.info(f"✅ 已移动文件夹: {entry} -> {target_path}")
            moved_folders.append(target_path)
            
        except Exception as e:
            logger.error(f"❌ 移动文件夹 {entry} 时出错: {e}")
    
    return moved_folders

def find_artist_folders_for_path(path: Path) -> List[Path]:
    """查找给定路径可能对应的画师文件夹列表
    
    Args:
        path: 输入路径
        
    Returns:
        List[Path]: 可能的画师文件夹列表
    """
    def is_artist_folder(p: Path) -> bool:
        """判断是否为画师文件夹"""
        return '[' in p.name and ']' in p.name
    
    try:
        path = Path(path).resolve()
        artist_folders = []
        
        # 如果是压缩包，使用其所在目录
        if path.is_file() and path.suffix.lower() in ['.zip', '.7z', '.rar']:
            base_path = path.parent
        else:
            base_path = path
            
        # 向上查找画师文件夹
        current_path = base_path
        while current_path != current_path.parent:
            if is_artist_folder(current_path) and current_path.exists():
                artist_folders.append(current_path)
            current_path = current_path.parent
        
        # 搜索当前目录下的画师文件夹
        for entry in base_path.iterdir():
            if entry.is_dir() and is_artist_folder(entry):
                artist_folders.append(entry)
                
        return artist_folders
        
    except Exception as e:
        print(f'❌ 查找画师文件夹时出错: {e}')
        return []

def batch_get_artist_folders(paths: List[str]) -> dict:
    """批量获取所有路径对应的画师文件夹
    
    Args:
        paths: 输入路径列表
        
    Returns:
        dict: 路径到画师文件夹的映射
    """
    path_to_folders = {}
    path_to_selected = {}
    
    # 首先收集所有路径可能的画师文件夹
    for path in paths:
        if not os.path.exists(path):
            logger.info(f"❌ 路径不存在: {path}")
            continue
            
        folders = find_artist_folders_for_path(Path(path))
        if not folders:
            logger.info(f"❌ 未找到画师文件夹: {path}")
            continue
            
        path_to_folders[path] = folders
        # 默认选择第一个找到的画师文件夹
        path_to_selected[path] = folders[0]
    
    # 显示所有路径和对应的画师文件夹
    while True:
        print("\n当前所有路径及其对应的画师文件夹:")
        for i, path in enumerate(path_to_folders.keys(), 1):
            print(f"\n{i}. 路径: {path}")
            print(f"   当前选择的画师文件夹: {path_to_selected[path]}")
            print("   可选的画师文件夹:")
            for j, folder in enumerate(path_to_folders[path], 1):
                print(f"      {j}. {folder}")
        
        # 让用户选择是否需要修改
        choice = input("\n请输入'序号 画师文件夹序号'来修改对应关系（例如：'1 2'表示修改第1个路径为其第2个画师文件夹）\n直接回车确认所有选择，输入q退出: ").strip()
        
        if not choice:
            break
        elif choice.lower() == 'q':
            return {}
            
        try:
            path_idx, folder_idx = map(int, choice.split())
            if 1 <= path_idx <= len(paths):
                path = list(path_to_folders.keys())[path_idx - 1]
                folders = path_to_folders[path]
                if 1 <= folder_idx <= len(folders):
                    path_to_selected[path] = folders[folder_idx - 1]
                    logger.info(f"✅ 已更新: {path} -> {folders[folder_idx - 1]}")
                else:
                    logger.info("❌ 无效的画师文件夹序号")
            else:
                logger.info("❌ 无效的路径序号")
        except ValueError:
            logger.info("❌ 输入格式错误，请使用'序号 画师文件夹序号'的格式")
    
    return path_to_selected

def generate_czkawka_paths(artist_folder: Path, compare_folder: Path) -> str:
    """生成czkawka路径字符串（用分号连接）
    
    Args:
        artist_folder: 画师文件夹路径
        compare_folder: 比较文件夹路径
        
    Returns:
        str: 用分号连接的路径字符串
    """
    # 确保路径字符串不包含转义字符问题
    artist_path = str(artist_folder).replace('\\', '/')
    compare_path = str(compare_folder).replace('\\', '/')
    return f"{artist_path};{compare_path}"

def display_path_panel(paths_str: str):
    """在终端显示路径面板，并复制到剪贴板
    
    Args:
        paths_str: 路径字符串
    """
    # 复制到剪贴板
    try:
        pyperclip.copy(paths_str)
        logger.info("✅ 路径已复制到剪贴板")
    except Exception as e:
        logger.error(f"❌ 复制到剪贴板失败: {e}")
    
    # 显示路径面板
    print("\n" + "=" * 80)
    print("Czkawka 路径 (已复制到剪贴板)")
    print("=" * 80)
    print(paths_str)
    print("=" * 80 + "\n")

def main():
    """主函数"""
    # 获取路径列表
    print("请输入要处理的路径（每行一个，输入空行结束）:")
    paths = []
    while True:
        path = input().strip().replace('"', '')
        if not path:
            break
        paths.append(path)
    if not paths:
        print("❌ 未输入任何路径")
        return
        
    print("🚀 开始处理...")
    
    # 批量获取并确认画师文件夹
    path_to_artist = batch_get_artist_folders(paths)
    if not path_to_artist:
        print("❌ 用户取消操作")
        return
    
    # 处理每个路径
    success_count = 0
    total_count = len(path_to_artist)
    
    for i, (path, artist_folder) in enumerate(path_to_artist.items(), 1):
        logger.info(f"=== 处理第 {i}/{total_count} 个路径 ===")
        logger.info(f"路径: {path}")
        logger.info(f"画师文件夹: {artist_folder}")
        
        # 更新进度
        progress = int((i - 1) / total_count * 100)
        logger.info(f"总路径数: {total_count} 已处理: {i-1} 成功: {success_count} 总进度: {progress}%")
        
        # 创建比较文件夹
        path_obj = Path(path)
        compare_folder = create_compare_folder(artist_folder)
        
        # 将除了画师文件夹外的其他同级文件夹移动到#compare文件夹
        moved_folders = move_folders_to_compare(path_obj, artist_folder)
        logger.info(f"✅ 已移动 {len(moved_folders)} 个文件夹到比较文件夹")
        
        # 生成czkawka路径字符串并显示
        paths_str = generate_czkawka_paths(artist_folder, compare_folder)
        display_path_panel(paths_str)
        
        success_count += 1
        
        # 更新最终进度
        progress = int(i / total_count * 100)
        logger.info(f"总路径数: {total_count} 已处理: {i} 成功: {success_count} 总进度: {progress}%")
            
    logger.info(f"✅ 所有处理完成: 成功 {success_count}/{total_count}")

# 兼容新的CLI方式
from .cli import app, interactive

if __name__ == "__main__":
    # 如果没有提供参数，直接使用原始的main函数
    if len(sys.argv) == 1:
        main()
    # 否则使用新的CLI
    else:
        # 如果第一个参数是-i或--interactive，使用交互模式
        if len(sys.argv) > 1 and sys.argv[1] in ['-i', '--interactive']:
            sys.exit(interactive())
        else:
            sys.exit(app()) 