import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import logging
from datetime import datetime
import shutil
import pyperclip  # 用于复制到剪贴板

# 尝试导入依赖，如果不存在则提供友好的错误信息
try:
    from loguru import logger
    from rich.console import Console
    from rich.tree import Tree
    from rich.panel import Panel
    from rich import print as rprint
    from rich.prompt import Confirm
    import typer
    from rich.json import JSON
except ImportError as e:
    module_name = str(e).split("'")[1]
    print(f"错误: 缺少必要的依赖 '{module_name}'")
    print("请安装所需依赖: pip install loguru pyperclip rich typer")
    sys.exit(1)

# 创建rich控制台
console = Console()

# 创建typer应用
app = typer.Typer(help="Kavvka - Czkawka辅助工具，用于处理图片文件夹并生成路径")

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
logger = setup_logger(app_name="kavvka", console_output=True)

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
    console.print(f"[green]✅ 创建比较文件夹:[/green] [cyan]{compare_folder}[/cyan]")
    return compare_folder

def move_folders_to_compare(folders_to_move: List[Path], artist_folder: Path, compare_folder: Path, force: bool = False) -> Dict[str, Any]:
    """将指定的文件夹移动到#compare文件夹
    
    Args:
        folders_to_move: 要移动的文件夹列表
        artist_folder: 画师文件夹路径
        compare_folder: 比较文件夹路径
        force: 是否强制移动，不询问确认
        
    Returns:
        Dict[str, Any]: 包含移动结果的JSON格式数据
    """
    moved_folders = []
    result_data = {
        "artist_folder": str(artist_folder),
        "compare_folder": str(compare_folder),
        "folders_to_move": [str(f) for f in folders_to_move],
        "moved_folders": [],
        "success": True,
        "message": "",
        "error_folders": []
    }
    
    # 如果没有需要移动的文件夹，直接返回
    if not folders_to_move:
        logger.info("❌ 没有需要移动的文件夹")
        result_data["success"] = False
        result_data["message"] = "没有需要移动的文件夹"
        return result_data
    
    # 创建文件夹树结构
    tree = Tree(f"[bold blue]{artist_folder}[/bold blue]")
    artist_node = tree.add(f"[bold green]{artist_folder.name}[/bold green] (画师文件夹)")
    compare_node = tree.add(f"[bold cyan]#compare[/bold cyan] (比较文件夹)")
    
    # 添加到树结构中
    for entry in folders_to_move:
        target_path = compare_folder / entry.name
        
        # 如果目标路径已存在，添加时间戳后缀
        if target_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            target_path = compare_folder / f"{entry.name}_{timestamp}"
        
        folder_node = tree.add(f"[bold red]{entry.name}[/bold red] (将移动到 #compare)")
        compare_node.add(f"[bold yellow]{target_path.name}[/bold yellow] (移动后)")
    
    # 显示树结构
    console.print("\n将执行以下文件夹移动操作:")
    console.print(tree)
    console.print(f"\n共有 [bold red]{len(folders_to_move)}[/bold red] 个文件夹将被移动到 [bold cyan]#compare[/bold cyan] 文件夹")
    
    # 询问用户是否确认移动
    if not force and not Confirm.ask("是否确认移动上述文件夹?"):
        logger.info("❌ 用户取消移动操作")
        result_data["success"] = False
        result_data["message"] = "用户取消移动操作"
        return result_data
    
    # 执行移动操作
    for entry in folders_to_move:
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
            
            # 添加到结果数据中
            result_data["moved_folders"].append({
                "source": str(entry),
                "target": str(target_path),
                "success": True
            })
            
        except Exception as e:
            logger.error(f"❌ 移动文件夹 {entry} 时出错: {e}")
            result_data["error_folders"].append({
                "folder": str(entry),
                "error": str(e)
            })
    
    result_data["success"] = len(moved_folders) > 0
    result_data["message"] = f"成功移动了 {len(moved_folders)} 个文件夹"
    
    return result_data

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
    """批量获取所有路径对应的画师文件夹和同级文件夹
    
    Args:
        paths: 输入路径列表
        
    Returns:
        dict: 路径到(画师文件夹, 同级文件夹列表)的映射
    """
    path_to_folders = {}
    path_to_selected = {}
    path_to_siblings = {}  # 存储同级文件夹
    
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
        
        # 获取同级文件夹（除了画师文件夹和#compare外的所有文件夹）
        path_obj = Path(path)
        if path_obj.is_dir():
            parent_dir = path_obj.parent
            siblings = []
            for entry in parent_dir.iterdir():
                if (entry.is_dir() and 
                    entry.resolve() != path_obj.resolve() and 
                    entry.name != "#compare" and 
                    not (('[' in entry.name) and (']' in entry.name))):
                    siblings.append(entry)
            path_to_siblings[path] = siblings
    
    # 显示所有路径和对应的画师文件夹
    while True:
        console.print("\n[bold cyan]当前所有路径及其对应的画师文件夹:[/bold cyan]")
        
        for i, path in enumerate(path_to_folders.keys(), 1):
            # 创建每个路径的树结构
            path_tree = Tree(f"[bold blue]{i}. 路径: {path}[/bold blue]")
            
            # 添加当前选择的画师文件夹（绿色高亮）
            current_folder = path_to_selected[path]
            path_tree.add(f"[bold green]当前选择: {current_folder}[/bold green]")
            
            # 添加可选的画师文件夹
            folders_node = path_tree.add("[bold yellow]可选的画师文件夹:[/bold yellow]")
            for j, folder in enumerate(path_to_folders[path], 1):
                style = "bold green" if folder == current_folder else "white"
                folders_node.add(f"[{style}]{j}. {folder}[/{style}]")
            
            # 添加同级文件夹
            if path in path_to_siblings and path_to_siblings[path]:
                siblings_node = path_tree.add("[bold magenta]同级文件夹 (将被移动):[/bold magenta]")
                for sibling in path_to_siblings[path]:
                    siblings_node.add(f"[red]{sibling.name}[/red]")
                
            # 显示树
            console.print(path_tree)
        
        # 让用户选择是否需要修改
        console.print("\n[bold cyan]操作提示:[/bold cyan]")
        console.print("- 输入 [bold]'序号 画师文件夹序号'[/bold] 来修改对应关系（例如：[bold]'1 2'[/bold] 表示修改第1个路径为其第2个画师文件夹）")
        console.print("- 直接回车确认所有选择")
        console.print("- 输入 [bold red]q[/bold red] 退出")
        
        choice = input("\n请输入选择: ").strip()
        
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
                    console.print("[bold red]❌ 无效的画师文件夹序号[/bold red]")
            else:
                console.print("[bold red]❌ 无效的路径序号[/bold red]")
        except ValueError:
            console.print("[bold red]❌ 输入格式错误，请使用'序号 画师文件夹序号'的格式[/bold red]")
    
    # 返回包含画师文件夹和同级文件夹的结果
    result = {}
    for path, artist_folder in path_to_selected.items():
        siblings = path_to_siblings.get(path, [])
        result[path] = (artist_folder, siblings)
    
    return result

def generate_czkawka_paths(input_folder: Path, compare_folder: Path) -> Dict[str, Any]:
    """生成czkawka路径字符串（用分号连接）
    
    Args:
        input_folder: 输入的路径（画集文件夹）
        compare_folder: 比较文件夹路径
        
    Returns:
        Dict[str, Any]: 包含路径信息的JSON格式数据
    """
    # 确保路径字符串不包含转义字符问题
    input_path = str(input_folder).replace('\\', '/')
    compare_path = str(compare_folder).replace('\\', '/')
    paths_str = f"{input_path};{compare_path}"
    
    return {
        "input_folder": input_path,
        "compare_folder": compare_path,
        "combined_path": paths_str
    }

def display_path_panel(paths_data: Dict[str, Any]):
    """在终端显示路径面板，并复制到剪贴板
    
    Args:
        paths_data: 包含路径信息的JSON格式数据
    """
    paths_str = paths_data["combined_path"]
    
    # 复制到剪贴板
    try:
        pyperclip.copy(paths_str)
        logger.info("✅ 路径已复制到剪贴板")
    except Exception as e:
        logger.error(f"❌ 复制到剪贴板失败: {e}")
    
    # 显示路径面板
    panel = Panel(
        f"[bold white]{paths_str}[/bold white]", 
        title="[bold green]Czkawka 路径 (已复制到剪贴板)[/bold green]",
        border_style="cyan",
        expand=False
    )
    console.print(panel)

@app.command()
def process(
    paths: List[str] = typer.Argument(None, help="要处理的路径列表"),
    force: bool = typer.Option(False, "--force", "-f", help="强制移动文件夹，不询问确认"),
    output_json: bool = typer.Option(False, "--json", "-j", help="以JSON格式输出结果")
):
    """处理指定的路径，查找画师文件夹并移动其他文件夹到#compare文件夹"""
    if not paths:
        console.print("[bold red]❌ 未提供任何路径[/bold red]")
        return
        
    console.print("\n[bold green]🚀 开始处理...[/bold green]")
    
    # 批量获取并确认画师文件夹
    path_to_artist = batch_get_artist_folders(paths)
    if not path_to_artist:
        console.print("[bold red]❌ 用户取消操作[/bold red]")
        return
    
    # 处理每个路径
    success_count = 0
    total_count = len(path_to_artist)
    
    # 用于收集所有处理结果的JSON数据
    all_results = {
        "all_combined_paths": [] , # 新增：收集所有combined_path
        "total_paths": total_count,
        "success_count": 0,
        "results": [],
    }
    
    # 记录第一个输入的文件夹路径，用于保存JSON文件
    first_artist_folder = None
    
    for i, (path, (artist_folder, siblings)) in enumerate(path_to_artist.items(), 1):
        # 记录第一个画师文件夹
        if i == 1:
            first_artist_folder = artist_folder
            
        console.rule(f"[bold blue]处理第 {i}/{total_count} 个路径[/bold blue]")
        console.print(f"[cyan]路径:[/cyan] [white]{path}[/white]")
        console.print(f"[cyan]画师文件夹:[/cyan] [green]{artist_folder}[/green]")
        
        # 更新进度
        progress = int((i - 1) / total_count * 100)
        console.print(f"[cyan]总路径数:[/cyan] [white]{total_count}[/white] [cyan]已处理:[/cyan] [white]{i-1}[/white] [cyan]成功:[/cyan] [green]{success_count}[/green] [cyan]总进度:[/cyan] [yellow]{progress}%[/yellow]")
        
        # 创建比较文件夹
        compare_folder = create_compare_folder(artist_folder)
        
        # 收集当前路径的处理结果
        path_result = {
            "path": str(path),
            "artist_folder": str(artist_folder),
            "compare_folder": str(compare_folder),
            "move_result": None,
            "czkawka_paths": None,
            "success": False
        }
        
        # 移动同级文件夹到#compare文件夹
        move_result = move_folders_to_compare(siblings, artist_folder, compare_folder, force)
        path_result["move_result"] = move_result
        
        if move_result["success"]:
            console.print(f"[green]✅ 已移动 {len(move_result['moved_folders'])} 个文件夹到比较文件夹[/green]")
        
        # 生成czkawka路径字符串并显示（使用输入路径而不是画师文件夹）
        paths_data = generate_czkawka_paths(Path(path), compare_folder)
        path_result["czkawka_paths"] = paths_data
        display_path_panel(paths_data)
        
        # 收集combined_path
        all_results["all_combined_paths"].append(paths_data["combined_path"])
        
        # 更新成功状态
        path_result["success"] = True
        success_count += 1
        
        # 添加到总结果中
        all_results["results"].append(path_result)
        
        # 更新最终进度
        progress = int(i / total_count * 100)
        console.print(f"[cyan]总路径数:[/cyan] [white]{total_count}[/white] [cyan]已处理:[/cyan] [white]{i}[/white] [cyan]成功:[/cyan] [green]{success_count}[/green] [cyan]总进度:[/cyan] [yellow]{progress}%[/yellow]")
    
    # 更新总结果
    all_results["success_count"] = success_count
    
    # 输出总结
    console.print(f"\n[bold green]✅ 所有处理完成: 成功 {success_count}/{total_count}[/bold green]")
    
    # 如果需要，输出完整的JSON结果
    if output_json or True:  # 默认总是输出JSON
        # console.print("\n[bold cyan]完整处理结果 (JSON):[/bold cyan]")
        # console.print(JSON.from_data(all_results))
        
        # 将JSON结果保存到文件
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 确定保存路径：第一个画师文件夹下
        if first_artist_folder:
            json_file = first_artist_folder / f"kavvka_result_{timestamp}.json"
        else:
            json_file = Path(f"kavvka_result_{timestamp}.json")
            
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        console.print(f"[green]✅ 结果已保存到文件: {json_file}[/green]")
        
        # 生成并显示所有combined_path的合并结果
        if all_results["all_combined_paths"]:
            # 使用三引号格式化输出，每行一个路径
            all_paths = "\n".join(all_results["all_combined_paths"])
            
            console.print("\n[bold cyan]所有Czkawka路径合集:[/bold cyan]")
            console.print("[bold green]===== 复制以下内容 =====[/bold green]")
            print(all_paths)  # 直接使用print，不带任何格式化，便于复制
            console.print("[bold green]======================[/bold green]")
            
            # 复制所有路径到剪贴板
            try:
                pyperclip.copy(all_paths)
                console.print("[green]✅ 所有路径已复制到剪贴板[/green]")
            except Exception as e:
                logger.error(f"❌ 复制到剪贴板失败: {e}")

            # 新增：保存一份 toml 文件，使用三引号保存所有路径
            try:
                import toml
            except ImportError:
                console.print("[yellow]未安装 toml，正在尝试安装...[/yellow]")
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'toml'])
                import toml
            
            # 生成单个路径集合（按分号拆分）
            single_paths = []
            for combined_path in all_results["all_combined_paths"]:
                # 按分号拆分每个合并路径
                paths_in_combined = combined_path.split(';')
                single_paths.extend(paths_in_combined)
            
            single_paths_str = "\n".join(single_paths)
            
            # 保存到同一个 toml 文件，包含三个字段
            toml_file = str(json_file).replace('.json', '.toml')
            single_paths_joined = ";".join(single_paths)
            with open(toml_file, 'w', encoding='utf-8') as f:
                f.write(f'all_combined_paths = """\n{all_paths}\n"""\n\n')
                f.write(f'single_paths = """\n{single_paths_str}\n"""\n\n')
                f.write(f'single_paths_joined = """\n{single_paths_joined}\n"""\n')
            console.print(f"[green]✅ 路径合集已保存为 toml 文件: {toml_file}[/green]")
    
    return all_results

@app.command()
def main(
    output_json: bool = typer.Option(False, "--json", "-j", help="以JSON格式输出结果")
):
    """交互式处理路径，查找画师文件夹并移动其他文件夹到#compare文件夹"""
    # 显示欢迎信息
    console.print("\n[bold green]欢迎使用 Kavvka - Czkawka 辅助工具[/bold green]")
    console.print("[cyan]用于处理图片文件夹并生成路径[/cyan]\n")
    
    # 获取路径列表
    console.print("[bold yellow]请输入要处理的路径（每行一个，输入空行结束）:[/bold yellow]")
    paths = []
    while True:
        path = input().strip().replace('"', '')
        if not path:
            break
        paths.append(path)
    if not paths:
        console.print("[bold red]❌ 未输入任何路径[/bold red]")
        return
        
    # 调用处理函数
    return process(paths, output_json=output_json)

# 入口点
if __name__ == "__main__":
    main()
