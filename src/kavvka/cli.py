import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint
from rich.table import Table

from .czkawka_helper import (
    setup_logger,
    find_artist_folders,
    create_compare_folder,
    move_matching_folders,
    generate_czkawka_paths,
    save_to_intro_md,
    is_artist_folder
)

# 创建typer应用
app = typer.Typer(
    name="kavvka",
    help="Czkawka辅助工具，用于处理图片文件夹并生成路径",
    add_completion=False,
)

# 创建Rich控制台
console = Console()

def show_header():
    """显示应用标题"""
    console.print(Panel.fit(
        "[bold blue]Kavvka[/bold blue] - [cyan]Czkawka辅助工具[/cyan]",
        border_style="green"
    ))

def get_artist_folder_from_path(path: Path) -> Optional[Path]:
    """从给定路径获取画师文件夹（交互式）
    
    Args:
        path: 输入路径（可以是压缩包或文件夹）
        
    Returns:
        Optional[Path]: 画师文件夹路径
    """
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
                    console.print(f"[green]✓[/green] 找到画师文件夹: [cyan]{current_path}[/cyan]")
                    if Confirm.ask(f"是否使用该画师文件夹?", default=True):
                        return current_path
                    else:
                        break  # 继续搜索当前目录下的其他画师文件夹
            current_path = current_path.parent
        
        # 如果向上查找没有找到或用户拒绝了，则搜索当前目录下的画师文件夹
        artist_folders = []
        for entry in base_path.iterdir():
            if entry.is_dir() and is_artist_folder(entry):
                artist_folders.append(entry)
                    
        if not artist_folders:
            console.print(f"[bold red]❌ 在路径 {base_path} 下未找到画师文件夹[/bold red]")
            return None
            
        # 使用select_artist_folder函数选择画师文件夹
        return select_artist_folder(artist_folders)
                
    except Exception as e:
        console.print(f"[bold red]❌ 获取画师文件夹时出错: {str(e)}[/bold red]")
        return None

def select_artist_folder(artist_folders: List[Path]) -> Path:
    """让用户选择一个画师文件夹
    
    Args:
        artist_folders: 画师文件夹列表
        
    Returns:
        Path: 选择的画师文件夹
    """
    if len(artist_folders) == 1:
        folder = artist_folders[0]
        if Confirm.ask(f"找到画师文件夹: [cyan]{folder}[/cyan]，是否使用?", default=True):
            return folder
    
    # 显示所有找到的画师文件夹
    table = Table(title="找到的画师文件夹")
    table.add_column("序号", style="cyan", no_wrap=True)
    table.add_column("文件夹路径", style="green")
    
    for i, folder in enumerate(artist_folders, 1):
        table.add_row(str(i), str(folder))
    
    console.print(table)
    
    # 让用户选择
    while True:
        choice = Prompt.ask("请选择画师文件夹编号或直接输入路径", default="1")
        try:
            index = int(choice) - 1
            if 0 <= index < len(artist_folders):
                folder = artist_folders[index]
                console.print(f"[green]✓[/green] 已选择: [cyan]{folder}[/cyan]")
                if Confirm.ask("确认使用该画师文件夹?", default=True):
                    return folder
                else:
                    continue
            else:
                console.print("[bold red]❌ 无效的选择，请重试[/bold red]")
        except ValueError:
            # 检查是否输入了路径
            path = Path(choice)
            if path.exists() and is_artist_folder(path):
                console.print(f"[green]✓[/green] 已选择: [cyan]{path}[/cyan]")
                return path
            console.print("[bold red]❌ 请输入有效的数字或画师文件夹路径[/bold red]")

def get_folder_path_interactive() -> Optional[Path]:
    """交互式获取文件夹路径
    
    Returns:
        Optional[Path]: 选择的文件夹路径，如果取消则返回None
    """
    console.print("[cyan]请输入要处理的文件夹路径:[/cyan]")
    while True:
        path_str = Prompt.ask("路径", default="")
        if not path_str:
            if Confirm.ask("是否取消操作?", default=False):
                return None
            continue
        
        # 处理路径字符串
        path_str = path_str.strip().replace('"', '')
        path = Path(path_str)
        
        if path.exists() and path.is_dir():
            return path
        else:
            console.print(f"[bold red]❌ 路径不存在或不是文件夹: {path}[/bold red]")

def get_output_path_interactive(default_path: Path) -> Path:
    """交互式获取输出文件路径
    
    Args:
        default_path: 默认输出路径
        
    Returns:
        Path: 选择的输出路径，如果使用默认路径则返回default_path
    """
    console.print(f"[cyan]默认输出文件路径: [/cyan][green]{default_path}[/green]")
    if Confirm.ask("是否使用默认输出路径?", default=True):
        return default_path
    
    console.print("[cyan]请输入新的输出文件路径:[/cyan]")
    while True:
        path_str = Prompt.ask("输出路径")
        if not path_str:
            return default_path
        
        # 处理路径字符串
        path_str = path_str.strip().replace('"', '')
        path = Path(path_str)
        
        # 确保父目录存在
        try:
            os.makedirs(path.parent, exist_ok=True)
            return path
        except Exception as e:
            console.print(f"[bold red]❌ 无法创建输出目录: {e}[/bold red]")

def process_folder_interactive(base_path: Path, output_file: Path) -> Tuple[bool, Optional[str]]:
    """交互式处理文件夹
    
    Args:
        base_path: 基础路径
        output_file: 输出文件路径
        
    Returns:
        Tuple[bool, Optional[str]]: 
            - 是否处理成功
            - 生成的路径字符串（如果成功）
    """
    try:
        # 显示处理的路径
        console.print(f"处理路径: [cyan]{base_path}[/cyan]")
        
        # 使用原有逻辑获取画师文件夹
        with console.status("[cyan]查找画师文件夹中...[/cyan]", spinner="dots"):
            artist_folder = get_artist_folder_from_path(base_path)
        
        if not artist_folder:
            console.print("[bold red]❌ 未找到画师文件夹[/bold red]")
            return False, None
        
        console.print(f"[green]✓[/green] 已选择画师文件夹: [cyan]{artist_folder}[/cyan]")
        
        # 创建比较文件夹
        with console.status("[cyan]创建比较文件夹中...[/cyan]", spinner="dots"):
            compare_folder = create_compare_folder(base_path)
        
        if not compare_folder:
            console.print("[bold red]❌ 创建比较文件夹失败[/bold red]")
            return False, None
        
        console.print(f"[green]✓[/green] 已创建比较文件夹: [cyan]{compare_folder}[/cyan]")
        
        # 移动符合条件的文件夹
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]移动符合条件的文件夹...[/cyan]", total=None)
            moved_folders = move_matching_folders(base_path, compare_folder, [artist_folder])
            progress.update(task, completed=True)
        
        console.print(f"[green]✓[/green] 已移动 [cyan]{len(moved_folders)}[/cyan] 个文件夹到比较文件夹")
        
        # 生成czkawka路径字符串
        paths_str = generate_czkawka_paths(artist_folder, compare_folder)
        console.print(f"[green]✓[/green] 生成路径: [cyan]{paths_str}[/cyan]")
        
        # 保存路径字符串到输出文件
        with console.status(f"[cyan]保存路径到 {output_file} 中...[/cyan]", spinner="dots"):
            success = save_to_intro_md(paths_str, output_file)
        
        if success:
            console.print(f"[green]✓[/green] 已保存路径到: [cyan]{output_file}[/cyan]")
            return True, paths_str
        else:
            console.print(f"[bold red]❌ 保存路径到 {output_file} 失败[/bold red]")
            return False, paths_str
        
    except Exception as e:
        console.print(f"[bold red]❌ 处理文件夹时出错: {str(e)}[/bold red]")
        return False, None

@app.command()
def process(
    path: Optional[Path] = typer.Argument(None, help="要处理的基础路径"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径（默认为src/kavvka/doc/intro.md）"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-n", help="是否使用交互式模式"),
):
    """处理文件夹，准备czkawka路径"""
    # 设置日志
    logger = setup_logger(app_name="kavvka_cli", console_output=not interactive)
    
    # 显示标题
    if interactive:
        show_header()
    
    # 获取基础路径
    base_path = path
    if interactive and base_path is None:
        base_path = get_folder_path_interactive()
        if base_path is None:
            console.print("[yellow]已取消操作[/yellow]")
            return 1
    elif base_path is None:
        print("❌ 错误: 在非交互式模式下必须提供路径参数")
        return 1
    
    # 获取输出文件路径（可选）
    output_file = None
    if output is None:
        # 默认输出到intro.md
        module_path = Path(__file__).parent
        default_output = module_path / "doc" / "intro.md"
        
        if interactive:
            output_file = get_output_path_interactive(default_output)
        else:
            output_file = default_output
    else:
        output_file = Path(output)
        
        # 确保父目录存在
        try:
            os.makedirs(output_file.parent, exist_ok=True)
        except Exception as e:
            if interactive:
                console.print(f"[bold red]❌ 无法创建输出目录: {e}[/bold red]")
            else:
                print(f"❌ 无法创建输出目录: {e}")
            return 1
    
    # 根据模式处理文件夹
    if interactive:
        success, paths_str = process_folder_interactive(base_path, output_file)
    else:
        from .czkawka_helper import process_folder_for_czkawka
        success, paths_str = process_folder_for_czkawka(base_path, output_file)
    
    # 显示结果
    if success:
        if interactive:
            console.print("\n[bold green]✅ 处理成功！[/bold green]")
            console.print(f"路径已保存到: [cyan]{output_file}[/cyan]")
            console.print(f"生成的路径: [cyan]{paths_str}[/cyan]")
            
            # 显示如何在Czkawka中使用
            console.print("\n[bold yellow]在Czkawka中使用:[/bold yellow]")
            console.print("1. 打开Czkawka")
            console.print("2. 在'包含目录'中手动添加以下路径:")
            console.print(f"   [cyan]{paths_str}[/cyan]")
            console.print("3. 使用Czkawka的重复文件或相似图片功能进行比较")
        else:
            print(f"✅ 处理成功！路径已保存到: {output_file}")
            print(f"生成的路径: {paths_str}")
        return 0
    else:
        if interactive:
            console.print("[bold red]❌ 处理失败，请查看日志获取详细信息[/bold red]")
        else:
            print("❌ 处理失败，请查看日志获取详细信息")
        return 1

@app.command()
def interactive():
    """直接进入交互模式，无需提供路径参数"""
    return process(path=None, interactive=True)

@app.callback()
def callback():
    """Kavvka - Czkawka辅助工具
    
    用于处理图片文件夹并生成路径，与Czkawka对接。
    """
    pass

if __name__ == "__main__":
    app() 