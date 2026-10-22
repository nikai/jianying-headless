# Jianying Headless · M5 本地适配

此 fork（[nikai/jianying-headless](https://github.com/nikai/jianying-headless)）保留
[mcncarl/jianying-headless](https://github.com/mcncarl/jianying-headless) 的原许可证，
只从正式入口开放当前精确 M5 库已实测的能力。

- 新建：720p / 1080p / UHD4K、30 fps，一条连续主视频轨可多段，普通字幕轨；
  输入为同尺寸同帧率 H.264/yuv420p，内嵌 AAC，保持 1×。
- 已验高级项：视频静态位置、缩放、旋转、透明度、音量和这六个通道的线性关键帧，
  独立 AAC 轨的固定音量，静态本地 TTF 字体、六种蒙版、dissolve 和默认参数 light-shake。
  字体依赖可选的钉版 fontTools，检查字形覆盖、文件字节与绑定；资源缺失即拒绝。
- `edit` 只从基础 H.264/AAC/普通文字来源创建独立副本，操作限文字替换、片段时间、
  原片裁切和音量；来源保持只读，仅支持 `185/189` schema。
- `ui-export plan/verify` 为剪映自己的导出窗口制定计划、检查实际 MOV/H.264/AAC 文件，
  不操作 UI。已验证的 MOV→MP4 无损转封装不重做画面，见 [导出说明](docs/UI-EXPORT.md)。

命令为 `doctor/build/verify-build/publish/verify`、`edit`、`ui-export`；完整参数用 `--help`。
`publish` 仅登记本机首页，不上传网络，须先保存工作并正常退出剪映。
后台 native ExportService 仍关闭：未修改 helper 对当前库实际返回 ABI 不匹配。
HEVC、照片/GIF、变速、未测画布/帧率、无音轨、非 AAC、字体动画、复合片段与 Windows
均不从正式入口开放。旧 profile 的历史代码不构成当前能力许可。

2026-10-22 八份合成样本的 UI 打开、播放、保存、退出、冷重开、MOV 导出和完整解码
由宿主完成；单测不能代替这些事实。声音有增益量化检查，未声明主观听感通过。
部分资源保存后依赖本机原生缓存，不能据此承诺草稿完全可迁移；不打包本机缓存。
验收范围和限制见 [验证状态](docs/VERIFICATION.md)。M1 无剪映，仅部署源码/skill。

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
[计划说明](skills/yichen-jianying-edit/references/headless-macos.md)，该页连接当前 M5 各条操作路径。
普通字幕、静态 TTF、音频与高级字段见 [计划格式](skills/yichen-jianying-edit/references/plan-format.md)；
编辑副本见 [编辑说明](skills/yichen-jianying-edit/references/edit-existing-macos.md)。

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
