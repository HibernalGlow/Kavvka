# Kavvka

Kavvka是一个Czkawka辅助工具，用于处理图片文件夹并生成路径。

## 功能

- 自动查找画师文件夹（包含`[]`标记的文件夹）
- 创建`#compare`文件夹，用于存放需要比较的文件夹
- 将符合条件的文件夹（画师文件夹外的其他文件夹）移动到`#compare`文件夹
- 生成用分号连接的两个路径（画师文件夹和比较文件夹），保存到`intro.md`文件
- 与Czkawka对接，不需要启动`process_artist_folder`和`process_duplicates`

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
# 基本用法
python main.py /path/to/your/folder

# 指定输出文件
python main.py /path/to/your/folder --output /path/to/output.md
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
   python main.py /path/to/your/folder
   ```

2. 打开Czkawka，在"包含目录"中手动添加生成的路径
   - 路径格式：`/path/to/artist_folder;/path/to/#compare`
   - 注意：不要添加引号

3. 使用Czkawka的重复文件或相似图片功能进行比较

## 注意事项

- 画师文件夹必须包含`[]`标记，例如：`[画师名]作品集`
- 路径中不能包含引号
- 默认输出文件为`src/kavvka/doc/intro.md`
