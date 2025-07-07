# Kavvka

Kavvka是一个Czkawka辅助工具，用于处理图片文件夹并生成路径。

## 功能

- 自动查找画师文件夹（包含`[]`标记的文件夹）
- 创建`#compare`文件夹，用于存放需要比较的文件夹
- 将符合条件的文件夹（画师文件夹外的其他文件夹）移动到`#compare`文件夹
- 生成用分号连接的两个路径（画师文件夹和比较文件夹），保存到`intro.md`文件
- 与Czkawka对接，不需要启动`process_artist_folder`和`process_duplicates`
- 支持命令行和交互式界面（使用Rich和Typer）

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/kavvka.git
cd kavvka

# 安装依赖
pip install -e .
```

## 使用方法

### 命令行使用

```bash
# 直接进入交互模式（无需提供路径参数）
python -m kavvka
python -m kavvka interactive

# 基本用法（交互式界面，需提供路径）
python -m kavvka process /path/to/your/folder

# 非交互式模式
python -m kavvka process /path/to/your/folder --no-interactive

# 指定输出文件
python -m kavvka process /path/to/your/folder --output /path/to/output.md

# 查看帮助
python -m kavvka --help
python -m kavvka process --help
```

### 简化命令（安装后）

```bash
# 直接进入交互模式
kavvka
kavvka interactive

# 提供路径参数
kavvka process /path/to/your/folder

# 查看帮助
kavvka --help
```

### 作为模块使用

```python
from pathlib import Path
from src.kavvka.czkawka_helper import process_folder_for_czkawka

# 处理文件夹
base_path = Path("/path/to/your/folder")
output_file = Path("/path/to/output.md")  # 可选
success, paths_str = process_folder_for_czkawka(base_path, output_file)

if success:
    print(f"处理成功！生成的路径: {paths_str}")
else:
    print("处理失败")
```

## 交互式界面

Kavvka提供了美观的交互式界面，使用Rich库实现：

- 彩色输出和格式化文本
- 进度条和加载动画
- 表格展示画师文件夹列表
- 交互式提示和确认
- 支持直接进入交互模式，无需提供路径参数

### 交互式流程

1. 启动交互模式：`python -m kavvka`
2. 输入要处理的文件夹路径
3. 确认或修改输出文件路径
4. 选择画师文件夹
5. 程序自动处理并生成路径

## 工作流程

1. 扫描指定目录，查找画师文件夹（包含`[]`标记的文件夹）
2. 如果找到多个画师文件夹，让用户选择一个
3. 在指定目录下创建`#compare`文件夹
4. 将指定目录下的其他文件夹（除了画师文件夹）移动到`#compare`文件夹
5. 生成两个路径的字符串，用分号连接：`画师文件夹路径;#compare文件夹路径`
6. 将路径字符串保存到`intro.md`文件

## 与Czkawka配合使用

1. 运行Kavvka生成路径：
   ```bash
   python -m kavvka
   ```

2. 打开Czkawka，在"包含目录"中手动添加生成的路径
   - 路径格式：`/path/to/artist_folder;/path/to/#compare`
   - 注意：不要添加引号

3. 使用Czkawka的重复文件或相似图片功能进行比较

## 注意事项

- 画师文件夹必须包含`[]`标记，例如：`[画师名]作品集`
- 路径中不能包含引号
- 默认输出文件为`src/kavvka/doc/intro.md`
