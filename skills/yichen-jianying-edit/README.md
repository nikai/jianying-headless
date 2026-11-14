# yichen-jianying-edit · M5 本地安装

本 Skill 随 Joker 维护的 [nikai/jianying-headless](https://github.com/nikai/jianying-headless)
源码提供，包含固定哈希入口和操作说明。
不复制官方程序库，不包含完整引擎。

1. 将源码检出到 `~/repos/jianying-headless`；已有检出直接使用。
2. 在核心目录运行 `python3 tools/build_native_codec.py`，精确工具链见核心 README。
3. 安装完整 Skill 目录，不只复制 `SKILL.md`；安装与注册由宿主执行。
4. 独立入口默认找上述标准目录，同仓入口自动定位，不依赖 GUI 继承 shell 环境。
   其他位置可用 `JIANYING_HEADLESS_ROOT=/absolute/path/to/checkout` 显式覆盖，
   覆盖路径不正确即停止，不回退到其他检出。

```bash
python3 /absolute/path/to/yichen-jianying-edit/scripts/headless_draft.py doctor
```

需要 Apple Silicon M5、Python 3.9+、FFmpeg / ffprobe，以及 `doctor` 能精确识别的 11.6.0 官方库。
完整工具链为 Apple clang 21.0.0（clang-2100.3.34.2）/ SDK 27.0 / linker 27037.1；
这是本机适配，不是任意 Mac 或同版本安装包的兼容承诺。

两个 profile 均支持基础五命令和受限 `edit`。基础新建支持720p/1080p/UHD4K 30fps、
匹配尺寸 H.264/yuv420p+AAC 和普通字幕。`1748fa32…` 已验静态变换、视频六通道线性关键帧、独立 AAC、
静态 TTF、六种蒙版、叠化和默认 light-shake。TTF 需 `requirements-fonts.txt` 的钉版依赖。
编辑只新建基础来源的副本。`ui-export` 仅适用于 `1748fa32…`，实际为 MOV/H.264/AAC，需宿主操作剪映。
后台 ExportService、变速、字体动画、复合片段和 Windows 保持关闭。
资源可能依赖原生缓存，缺失即拒绝，不随包分发。细节统一见 [计划格式](references/plan-format.md)。
官方 build 13281 / `a490d9a0…` 使用 `jy14-headless-macos-11.6.0-13281`，仅开放基础草稿和受限编辑。
详见 [SKILL.md](SKILL.md)。Skill 与核心源码须匹配，不能跳过固定哈希校验。

原创部分采用 [个人学习和非商业使用条款](LICENSE)，商业用途须取得作者明确书面授权。
第三方内容保留原许可证；不授予剪映程序库、账号、素材或服务使用权。
