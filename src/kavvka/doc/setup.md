你可以通过设置环境变量 `CZKAWKA_CONFIG_PATH`和`CZKAWKA_CACHE_PATH`，让 Czkawka 使用 `D:\scoop\apps\czkawka-gui\config`和`D:\scoop\apps\czkawka-gui\cache` 作为配置和缓存目录。

在 Windows PowerShell 下，启动命令如下：

```
[Environment]::SetEnvironmentVariable("CZKAWKA_CONFIG_PATH", "D:\scoop\apps\czkawka-gui\config", "User")
[Environment]::SetEnvironmentVariable("CZKAWKA_CACHE_PATH", "D:\scoop\apps\czkawka-gui\cache", "User")
```

