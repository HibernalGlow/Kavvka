# 使用说明

- [图形界面](#gui-gtk)
- [命令行界面](#cli)
- [配置/缓存文件](#configcache-files)
- [技巧、提示与已知问题](#tips-tricks-and-known-bugs)
- [工具](#tools)

Czkawka 目前包含三个独立的前端：一个终端应用和两个共享核心模块的图形应用。

## 图形界面 GTK
<img src="https://user-images.githubusercontent.com/41945903/148281103-13c00d08-7881-43e8-b6e3-5178473bce85.png" width="800" />

### 界面概览
图形界面由不同部分组成：
- 1 - 图片预览：用于查找重复文件和相似图片。无法调整大小，但可以禁用。
- 2 - 主选项卡：用于切换工具。
- 3 - 主结果窗口：可选择、删除、配置结果。
- 4 - 底部图片面板：包含对数据执行特定操作的按钮（如选择），或隐藏/显示界面部分。
- 5 - 文本面板：显示执行操作的消息/警告/错误。用户可隐藏。
- 6 - 目录选择面板：用于选择包含或排除的目录，并指定允许的扩展名和文件大小。
- 7 - 按钮：打开关于窗口（显示应用信息）和设置窗口，可自定义扫描。

<img src="https://user-images.githubusercontent.com/41945903/148279809-54ea8684-8bff-436b-af67-ff9859f468f2.png" width="800" />

### 语言翻译
GTK 图形界面支持完整翻译。
目前支持至少 10 种语言（部分为自动翻译，可能不够准确）。

### 打开/操作文件
可通过双击选中文件来打开。

要打开多个文件，按住 CTRL 键选择所需文件，然后在按住该键的同时，左键双击选中项。

要打开包含所选文件的文件夹，右键双击该文件。

要反选文件组中的文件，点击文件的中键即可反选同组其他文件。

### 添加目录

默认情况下，当前路径会被加载为包含目录，排除目录会填充默认路径。

可以通过启动应用时添加参数来覆盖此设置，例如：`czkawka_gui /home /usr --/home/rafal --/home/zaba`，表示检查 `/home` 和 `/usr` 目录，排除 `/home/rafal` 和 `/home/zaba`。

使用额外命令行参数时，退出时保存选项会被禁用，当前目录信息不会自动保存，需手动保存。

支持相对和绝对路径，如可用 `../home` 或 `/home`。

添加路径后，可将一个或多个路径标记为“参考文件夹”。参考文件夹中的文件无法被操作（如选择、移动或删除）。此功能适用于需要保留某文件夹不变，但又想用其与其他文件夹对比的场景。

## 命令行界面
Czkawka 的命令行前端适合自动化任务，如删除空目录。

要获取用法信息，可在控制台输入 `czkawka_cli`

<img src="https://user-images.githubusercontent.com/41945903/103018271-3d64ac80-4545-11eb-975c-2132f2ccf66f.png" width="800" />

你会看到许多使用示例。

如需获取某工具的详细信息，在其名称后加 `-h` 或 `--help`。

<img src="https://user-images.githubusercontent.com/41945903/103018151-0a221d80-4545-11eb-97b2-d7d77b49c735.png" width="800" />

默认所有工具只在控制台输出结果，但可通过特定参数删除文件/参数或保存到文件。

程序返回码：0 表示一切正常，1 表示发生错误，11 表示发现了文件。

## 配置/缓存文件
目前，Czkawka 会在磁盘上存储一些配置和缓存文件：
- `czkawka_gui_config.txt`：存储图形界面配置，可在启动时加载
- `cache_similar_image_SIZE_HASH_FILTER.bin/json`：存储缓存数据和哈希值，避免重复计算。每种算法使用独立文件。
- `cache_broken_files.txt`：存储损坏文件的缓存数据
- `cache_duplicates_HASH.txt`：存储重复文件缓存数据。为避免性能下降，仅存储已完全哈希且大于 5MB 的文件。
- `cache_similar_videos.bin/json`：存储视频文件缓存数据。

可修改 JSON 扩展名的文件（如需迁移或跨设备使用缓存）。需在设置中启用生成 JSON 缓存文件选项。默认优先加载 bin 文件，若缺失则加载 json 文件。

配置文件路径：

Linux - `/home/username/.config/czkawka`  
Mac - `/Users/username/Library/Application Support/pl.Qarmin.Czkawka`  
Windows - `C:\Users\Username\AppData\Roaming\Qarmin\Czkawka\config`

缓存文件路径：

Linux - `/home/username/.cache/czkawka`  
Mac - `/Users/username/Library/Caches/pl.Qarmin.Czkawka`  
Windows - `C:\Users\Username\AppData\Local\Qarmin\Czkawka\cache`

可通过环境变量 `CZKAWKA_CONFIG_PATH` 和 `CZKAWKA_CACHE_PATH` 修改缓存/配置路径，例如：
```
CZKAWKA_CONFIG_PATH="/media/rafal/Ventoy/config" CZKAWKA_CACHE_PATH="/media/rafal/Ventoy/cache" krokiet
```
可通过如下脚本在 U 盘上创建便携版应用：

`open_czkawka.sh` - 与 czkawka/krokiet 二进制文件同目录
```shell
#!/bin/bash

CZKAWKA_CONFIG_PATH="$(dirname \"$(realpath \"$0\")\")/config"
CZKAWKA_CACHE_PATH="$(dirname \"$(realpath \"$0\")\")/cache"

./czkawka_gui
```

## 技巧、提示与已知问题
- **使用 LTO 加速 CPU 密集型任务**
  可通过在 `Cargo.toml` 文件添加/修改如下内容编译应用（小幅提升性能，大幅减小二进制体积）：
```
[profile.release]
lto = "thin" # 或 "fat"
```
- **使用本地 CPU 优化加速 CPU 密集型任务**
  编译时使用本地 CPU 优化可显著提升速度（如 x86_64_v4 上哈希图片速度提升 10-20%）：
```
RUSTFLAGS="-C target-cpu=native" cargo build --release
```
或全局添加到 `~/.cargo/config.toml`
```
[target.x86_64-unknown-linux-gnu]
linker = "clang"
rustflags = [
       "-C", "target-cpu=native",
]

```
- **更快的相似图片检测**
  新的 `fast_image_resize` 功能可加速图片缩放。对大图片提升 30–200%，对小图片无明显提升。9.0 版本起默认启用，可手动关闭。
- **手动添加多个目录**  
  可手动编辑配置文件 `czkawka_gui_config.txt` 添加/删除/修改目录。设置完成后需加载配置。
- **缓存加载/保存慢导致检测变慢**  
  若之前检测过大量文件（数万），则所有信息都会被加载/保存，即使只处理少量文件。可重命名或删除以 `cache_similar_image` 开头的缓存文件，缓存会重新生成且条目更少，加载/保存更快。
- **部分数据列（修改日期、文件大小）在界面中不可见**
  某些列过宽时，部分数据列可能不可见。
  有两种解决方法：
    - 使用水平滚动条滚动视图（如图 1）
    - 缩小其他列宽度（如图 2）
  相关讨论见 https://github.com/qarmin/czkawka/issues/169
![AA](https://user-images.githubusercontent.com/41945903/125684641-728e264a-34ab-41b1-9853-ab45dc25551f.png)
- **打开父文件夹**
    - 可通过右键双击选中项打开其父文件夹，也可左键双击打开。
- **大批量重复文件扫描更快**  
  默认对同尺寸文件分组后计算部分哈希（每个文件前 4KB）。
- 该哈希计算非常快，尤其在 SSD 和多核处理器上。
  但若在 HDD 或慢处理器上扫描数十万/百万文件，此步骤可能耗时较长。
  设置中有“使用预哈希缓存”选项，可缓存此过程。
  默认关闭，因为条目过多会增加加载/保存时间。
- **缓存条目永久保存**  
  每次扫描后，缓存会校验并移除指向不存在文件的条目。
  若扫描外部设备（如 U 盘、移动硬盘）后拔出再插入，可能导致缓存条目被清除。
  设置中有“自动删除过期缓存条目”选项，可关闭。关闭后缓存文件可能变大，可手动点击“移除过期结果”按钮清理。
- **分步扫描**
  若无法一次性扫描所有文件，可中途停止，已计算的哈希/数据会保存到缓存，加快后续扫描。

# 工具

### 重复文件查找

重复文件查找可按预设条件分组搜索文件：

- **按名称** - 按文件名分组，如 `/home/john/cats.txt` 与 `/home/lucy/cats.txt` 会被视为重复。最快但极不可靠，除非明确需求不建议使用。

- **按大小** - 按文件字节数分组。速度与前者相同，结果更好，但也不推荐随意使用。

- **按大小和名称** - 先按大小再按名称分组。与前两种类似，也不可靠。

- **按哈希** - 通过加密哈希判断文件是否一致，几乎 100% 准确。

  这是最慢但最可靠的方式。

  因为只在同尺寸文件组内比对哈希，几乎不可能将不同文件误判为相同。

  包含 3 步：
    - 按尺寸分组 - 唯一尺寸的文件直接排除。

    - 预哈希检查 - 同尺寸组内，使用所有处理器线程并行处理。每个文件读取前 2KB 并哈希，组内唯一哈希的文件被移除。此步骤通常可将查找时间减半。

    - 全哈希比对 - 对剩余文件进行全内容哈希，确保完全一致。

### 空文件
查找空文件非常简单且快速，只需检查文件元数据和长度。

### 空目录
开始时为每个目录创建特殊条目，包括其父路径（除非是用户直接选择的文件夹）及是否为空的标志。初始假定所有目录可能为空。

首先将用户自定义文件夹加入待检查目录池。

逐个检查每个文件夹：

- 若为文件夹，则加入待检查队列，标记为可能为空（FolderEmptiness::Maybe）。
- 若包含文件或子目录，则标记为非空（FolderEmptiness::No），其所有父目录也标记为非空。

示例：

有四个可能为空的文件夹：/cow/、/cow/ear/、/cow/ear/stack/、/cow/ear/flag/。

若 /cow/ear/flag/ 含有文件，则：

- /cow/ear/flag/ 标记为非空。
- 其父目录 /cow/ear/ 和 /cow/ 也标记为非空。
- 但 /cow/ear/stack/ 可能仍为空。

最终所有仍为 FolderEmptiness::Maybe 的目录默认视为空。

### 大文件
遍历指定路径下所有文件，读取其大小。根据模式，显示指定数量的最小或最大文件。

### 临时文件
通过扩展名与预设列表比对查找临时文件。

当前认为临时文件的名称和扩展名有：
```
["#", "thumbs.db", ".bak", "~", ".tmp", ".temp", ".ds_store", ".crdownload", ".part", ".cache", ".dmp", ".download", ".partial"]
```
此方法仅删除最常见的临时文件。更彻底的清理建议使用 BleachBit。

### 无效符号链接
查找无效符号链接需先定位所有符号链接。

找到后，检查每个链接的目标。若目标不存在，则加入无效符号链接列表。

第二种模式尝试检测递归符号链接。
但目前该功能不可用，会错误报告目标不存在。
原本设计是统计符号链接跳转次数，若超过阈值（如 20），则视为递归链接。
### 相同音乐
标签仅限 `artist`、`title`、`year`、`bitrate`、`genre`、`length`。

**流程**
- 收集所有扩展名为 `.mp3`、`.flac`、`.m4a` 的音乐文件
- 读取每个文件的标签

**重复标签模式下**
- 用户选择用于比对的标签组
- 标签如 `artist` 会被简化：
  - 移除所有非字母数字字符
  - 转为小写
  - 若选择近似比对，去除括号内内容（如 `bataty (feat. romba)` 视为 `bataty`）
- 仅收集非空标签

**相似内容模式下**
- 若选择按标题比对，先按简化标题分组，减少需计算哈希的文件数
- 为每个文件生成哈希
- 按用户设定的相似度阈值和最小匹配片段长度比对哈希

所有标签检查完毕后，结果以表格显示。

### 相似图片

该工具用于检测可能因水印、尺寸或压缩伪影不同的相似图片。

目前对未旋转图片效果较好。

#### **流程概览**

1. **收集图片**
  - 收集特定扩展名的图片，包括 RAW、JPEG 等。

2. **加载缓存数据**
  - 加载已计算哈希的缓存，避免重复计算
  - 默认自动移除指向不存在文件的缓存条目（可在设置中关闭）

3. **生成感知哈希**
  - 图片缩放至 8x8、16x16、32x32 或 64x64 像素（在 `image_hasher` 库中）
  - 为未在缓存中的图片计算感知哈希
  - 感知哈希与加密哈希不同，轻微变化会生成相似输出：

    ```
    11110 ==>  AAAAAB  
    11111 ==>  FWNTLW  
    01110 ==>  TWMQLA  
    ```  

    感知哈希对相似图片输出相近：

    ```
    11110 ==>  AAAAAB  
    11111 ==>  AABABB  
    01110 ==>  AAAACB  
    ```  

4. **存储与比对哈希**
  - 哈希数据存储于专用树结构，便于用 [汉明距离](https://en.wikipedia.org/wiki/Hamming_distance) 高效比对。
  - 哈希会保存到文件，下次无需重复计算。
  - 逐一比对哈希，若距离低于用户设定阈值，则视为相似图片并移出待检测池。

#### **哈希与缩放选项**

- 支持五种哈希类型：
  - `Gradient`
  - `Mean`
  - `VertGradient`
  - `Blockhash`
  - `DoubleGradient`

- 哈希前通常会缩放图片。支持的缩放算法：
  - `Lanczos3`
  - `Gaussian`
  - `CatmullRom`
  - `Triangle`
  - `Nearest`

- 支持哈希尺寸：`8x8`、`16x16`、`32x32`、`64x64`
- 缩放方法和哈希尺寸均可在应用内调整。

每种配置会生成独立缓存文件，避免不同设置下结果混淆。

#### **其他功能与注意事项**

- 部分图片可能导致哈希全为 0 或 255，这类图片会被排除但仍存于缓存。
- 提供命令行测试工具。将 `test.jpg` 放入文件夹，运行 `czkawka_cli tester -i` 测试算法。

#### **更快比对模式**
启用后，每对结果仅比对一次，尤其在高相似度阈值下大幅提升性能。

#### **小贴士**
- 哈希尺寸小不一定更快。
- `Blockhash` 是唯一不会缩放图片的算法。
- `Nearest` 缩放算法速度可达其他算法 5 倍，但结果可能较差。
- `fast_image_resize` 功能可加速缩放，但可能略降准确率。

### **相似视频查找器**

该工具与“相似图片”类似，但用于视频文件。

#### **要求与限制**
- 需安装 **FFmpeg**，否则会报错
- 目前仅比较长度几乎相等的视频

#### **流程概览**
  - 按扩展名（.mp4、.mpv、.avi 等）收集视频文件。
  - 用哈希算法处理每个文件。
  - 由外部库实现，流程包括：
    - 提取多帧
    - 为每帧生成感知哈希
  - 生成的哈希会保存到缓存，避免重复计算
  - 按用户设定的相似度阈值比对哈希
  - 返回相似视频分组结果

### 损坏文件
### **损坏或无效文件查找器**

该工具检测损坏或扩展名无效的文件。

- 检查 pdf、音频、音乐和压缩文件
- 打开文件出错则视为损坏（有例外）
- 依赖外部库，可能有误报（如 [此问题](https://github.com/image-rs/jpeg-decoder/issues/130)），建议手动确认

### 错误扩展名
此模式查找内容与扩展名不符的文件。

流程如下：
- 提取当前扩展名，如 `źrebię.zip` → `zip`
- 读取文件前几字节
- 与已知签名比对，判断实际类型，如 `7z`
- 获取 MIME 类型（可能有多个值），如 `Mime::Archive`
- 列出所有关联扩展名，如 `rar, 7z, zip, p7`
- 必要时扩展列表（如 exe、dll 可能签名相似）
- 若当前扩展名在列表中，则大概率正确，否则标记为无效扩展名

在“正确扩展名”列中，Infer 库检测到的扩展名用括号标注，同 MIME 类型的扩展名显示在外部。

![ABC](https://user-images.githubusercontent.com/41945903/167214811-7d811829-6dba-4da0-9788-9e2f780e7279.png)

## 代码覆盖率
如需检查 Czkawka 的代码覆盖率（测试或正常使用），可执行如下命令（支持 Ubuntu 22.04，其他系统仅安装包命令不同）：
```commandline
sudo apt install llvm
cargo install rustfilt

RUSTFLAGS="-C instrument-coverage" cargo run --bin czkawka_gui
llvm-profdata merge -sparse default.profraw -o default.profdata


llvm-cov show   -Xdemangler=rustfilt target/debug/czkawka_gui -format=html -output-dir=report -instr-profile=default.profdata  -ignore-filename-regex="cargo/registry|rustc"
llvm-cov report -Xdemangler=rustfilt target/debug/czkawka_gui              --instr-profile=default.profdata -ignore-filename-regex="cargo/registry" > lcov_report.txt

xdg-open report/index.html
xdg-open lcov_report.txt
```