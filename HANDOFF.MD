# 构建排障

## CMake 的 Lemon 宿主包

`LEMON_ROOT` 取 [Lemon 锁文件](cmake/lemon.lock.json) 对应的 vcpkg-cache 恢复回执中的 `root`。CMake 从这个目录查找 Lemon 和 `share/lemon/lempar.c`。用 `ninja -C build/native-release-user -t query snmp/asn1/parser.c` 可以同时核对语法文件、可执行文件和模板三个输入。Android 的目标 triplet 用于库依赖，Lemon 恢复选择 CI runner 的宿主平台。

在 Windows 上，LLVM-MinGW 和 MSVC 的 Release preset 各通过 37 项 CTest。Android ARM64 和 x64 交叉构建均使用 Windows 宿主 Lemon，安装的共享库通过 16 KiB ELF 对齐检查。缺少 `LEMON_ROOT` 时，CMake 在配置阶段报错。

## re2c 缓存路径

Slate 通过 `.env` 的 `SALTSNET_RE2C_ROOT` 读取 vcpkg-cache 恢复 `Qigao.Re2c.Binary` 后在 `receipt.json` 中报告的 `root`。VS Code 的 Slate 扩展将进程环境传给 CLI，已打开的窗口会继续携带启动时的共享 `RE2C_ROOT`。用 `slate doctor --preset tests` 确认 `SALTSNET_RE2C_ROOT` 来自仓库 `.env`。CMake 通过 `RE2C_ROOT` 接收相同安装路径。

## SNMP ASN.1 头文件搜索顺序

当 `mib_compiler.c` 或 `scanner.re` 通过 Slate 编译时，如果报 `g_parse_state` 未声明，检查 `out/` 下所选 preset 的 `compile_commands.json`。SaltsBase SDK 和本仓库的 `snmp/asn1/include` 都提供 `ast.h` 与 `mib_compiler.h`。Slate 0.1.14 先收集依赖的头文件目录，SDK 的同名头文件可能先被选中。CMake 把这组 SDK 目录作为系统头文件目录处理。

`snmp/asn1/module.json` 将自己的头文件目录放在首个公开依赖 `saltsnet_snmp_support_headers` 中。两套 Windows x64 工具链均通过完整构建、37 项正式测试和安装验证。用 `slate gen --preset release --build-dir out/slate-explain --explain saltsnet_snmp_support` 可复查生效的头文件路径与顺序。
