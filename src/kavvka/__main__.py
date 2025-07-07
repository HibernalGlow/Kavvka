import sys
from .cli import app, interactive

if __name__ == "__main__":
    # 如果没有提供参数，直接进入交互模式
    if len(sys.argv) == 1:
        sys.exit(interactive())
    else:
        sys.exit(app()) 