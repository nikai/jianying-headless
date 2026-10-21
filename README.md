# Jianying Headless · M5 本地适配

此 fork（[nikai/jianying-headless](https://github.com/nikai/jianying-headless)）只开放
M5 已验证的新建 H.264 视频与普通字幕流程。来源为
[mcncarl/jianying-headless](https://github.com/mcncarl/jianying-headless)，保留原许可证。

支持命令：`doctor`、`build`、`verify-build`、`publish`、`verify`。
`publish` 仅登记到本机剪映首页，不上传网络；须先保存工作并正常退出剪映。
入口拒绝编辑、资源特效、蒙版、转场、自定义字体、动画、复合片段、独立音效轨及所有导出
（含 UI / Windows FFmpeg）。视频自带音频随源片保留，不等于独立音效能力已验收。
计划只接受一条普通视频轨与普通字幕轨，视频保持 1×；不接受图片、GIF 或 HEVC。
素材必须为 1280×720、30 fps 的 H.264/yuv420p，内嵌 AAC 音轨；画布固定 1280×720、30 fps。
无音轨、其他像素格式、编码、尺寸与帧率均拒绝，不自动转码。
回读要求视频和字幕可见、透明度为 1；省略这两个默认字段可接受，修改后拒绝。

## 精确环境

- Apple Silicon M5；本机实测 macOS 27.0.1。
- `/Applications/VideoFusion-macOS.app`，版本与 bundle build 均为 `11.6.0`，
  官方库 SHA-256 为 `1748fa32a09a967b46515a3acb04863a917b445682d06a64c0e9f0a739db01f1`。
- Python 3.9+、FFmpeg / ffprobe、官方 Xcode 工具。
- 桥接组件固定组合：Apple clang 21.0.0（clang-2100.3.34.2）、macOS SDK 27.0、
  linker 27037.1；最低二进制系统版本 26.0 不代表已验收其他系统。
- 精确配置与构建哈希分别见 `engine/runtime_profiles.py`、`bridge/SOURCE_MANIFEST.json`。

旧 11.6 官方 build 13281 / 库 `a490d9a0…` 的验收不适用于此库，旧指纹会被拒绝。
源码保留的 11.5 / 11.4 历史配置不构成本次 M5 的兼容承诺。
不替换官方程序库，不修改账号权益，不以修改固定哈希跳过不匹配。

## 开始使用

已授权源码位置为 `~/repos/third-party/jianying-headless`；如果目录已有检出，直接使用，
不要覆盖。首次安装按 [入门说明](docs/GETTING-STARTED.md) 操作。

```bash
cd ~/repos/third-party/jianying-headless
python3 tools/build_native_codec.py --check-toolchain
python3 tools/build_native_codec.py
python3 skills/yichen-jianying-edit/scripts/headless_draft.py doctor
```

用已授权的本地 H.264 素材编写计划，格式参考
[计划说明](skills/yichen-jianying-edit/references/headless-macos.md)，该页仅描述当前 M5 基础能力。
普通字幕可用 `text`、`size`、`x`、`y`、`color`、`border_color`、`border_width`；
视频只用 `source`、原片裁切与目标时间字段。

```bash
python3 skills/yichen-jianying-edit/scripts/headless_draft.py build --plan /absolute/path/to/plan.json --out "$PWD/work/new-build"
python3 skills/yichen-jianying-edit/scripts/headless_draft.py verify-build --build "$PWD/work/new-build"
python3 skills/yichen-jianying-edit/scripts/headless_draft.py publish --build "$PWD/work/new-build" --audit "$PWD/work/new-publish"
python3 skills/yichen-jianying-edit/scripts/headless_draft.py verify --build "$PWD/work/new-build"
```

输出目录必须是新目录；构建不改原素材或其他草稿。
`verify` 支持本次基础草稿的 `185.0.0` → `189.0.0` 保存回读，不接受旧库的 `187` 迁移。
结构回读不能代替实际播放、人工听感与保存退出后冷重开验收。
历史记录与本地范围的区别见 [验证状态](docs/VERIFICATION.md)。

## 独立 Skill

见 [安装说明](skills/yichen-jianying-edit/README.md)。同仓入口自动定位；
独立安装默认找 `~/repos/third-party/jianying-headless`，不用 GUI 继承终端环境变量。
其他位置用 `JIANYING_HEADLESS_ROOT=/absolute/path/to/checkout` 显式覆盖；覆盖无效即失败。
Skill 与核心源码必须匹配固定哈希。

## 源码检查

```bash
python3 tools/check_package.py
python3 -m unittest discover -s tests -v
```

历史专项测试不代表 M5 新库的原生验收。`work/` 中的本地日志与素材不分发。
官方引擎、账号数据和效果资源不随源码分发。

## 许可与来源

原创部分采用 [个人学习和非商业使用许可](LICENSE)；商业使用需取得作者书面授权。
第三方内容继续适用原许可证，详见 [第三方声明](THIRD_PARTY_NOTICES.md)。
代码许可不包含剪映集成授权、账号权益或素材许可；见 [分发范围](docs/DISTRIBUTION-SCOPE.md)。
