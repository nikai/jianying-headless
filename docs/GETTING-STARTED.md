# M5：生成 H.264 视频与普通字幕草稿

本教程适用于 [README 的精确 M5 环境](../README.md#精确环境)，不是通用安装兼容承诺。
本文先创建基础草稿；当前完整范围见 [README](../README.md)。编辑副本和 UI 导出
分别使用正式入口的 `edit`、`ui-export`，后台原生导出仍关闭。

## 源码和工具

源码默认放在 `~/repos/third-party/jianying-headless`。以下安装命令只用于该目录不存在时；
已有目录直接进入，不删除、不覆盖。

```bash
mkdir -p ~/repos/third-party
git clone https://github.com/nikai/jianying-headless.git ~/repos/third-party/jianying-headless
cd ~/repos/third-party/jianying-headless
```

需要 Python 3.9+ 和 FFmpeg / ffprobe；基础草稿无需 pip 依赖、API Key 或付费 ASR。
显式本地 TTF 需在选定 Python 环境安装 `requirements-fonts.txt` 的钉版 fontTools；
蒙版、叠化与 light-shake 仅使用已存在且逐文件匹配固定 catalog 的本机资源，缺失即拒绝。
桥接已验组合为 Apple clang 21.0.0（clang-2100.3.34.2）/ SDK 27.0 / linker 27037.1，
实测系统 macOS 27.0.1。版本相同但库不同仍会拒绝：当前库 SHA 为 `1748fa32…`，
旧官方 13281 / `a490d9a0…` 不适用，也不继承它的 UI 导出、编辑或效果验收。

```bash
python3 tools/build_native_codec.py --check-toolchain
python3 tools/build_native_codec.py
python3 skills/yichen-jianying-edit/scripts/headless_draft.py doctor
```

有多个 Xcode 时可在构建命令加 `--developer-dir /Applications/Xcode.app/Contents/Developer`，
不需要修改系统默认选择。工具链不匹配时保留报错，不把新哈希写入配置。
`doctor` 的成功标志是 `status: ok`、`app_version: 11.6.0` 和正确官方库指纹。

## 计划与隔离构建

用有权使用的本地 H.264/yuv420p 视频编写 JSON：素材必须为 1280×720、1920×1080 或 3840×2160、30 fps，内嵌 AAC。
画布与素材尺寸和帧率相同；其他尺寸、像素格式、帧率、音频编码或无音轨都会拒绝。
下面是 4 秒视频和普通文字的示例，素材须至少 4 秒；替换素材绝对路径并选一个新草稿名。

```json
{
  "schema": "jy14-headless-plan/v1",
  "name": "Joker-basic-draft",
  "canvas": {"width": 1280, "height": 720, "fps": 30},
  "tracks": [
    {"type": "video", "segments": [
      {"source": "/absolute/path/to/source.mp4", "start_us": 0, "duration_us": 4000000}
    ]},
    {"type": "text", "segments": [
      {"text": "普通字幕", "start_us": 0, "duration_us": 4000000, "size": 6, "y": -0.7, "color": "#FFFFFF"}
    ]}
  ]
}
```

将计划保存为 `work/plan.json`，从项目根目录执行：

```bash
python3 skills/yichen-jianying-edit/scripts/headless_draft.py build --plan "$PWD/work/plan.json" --out "$PWD/work/new-build"
python3 skills/yichen-jianying-edit/scripts/headless_draft.py verify-build --build "$PWD/work/new-build"
```

输出目录须不存在。成功返回已验证结构，尚未登记首页；原素材不变。
普通裁切保持 1×，只接受一条视频轨和普通文字轨；不要添加 `speed`、`volume`、
`keyframes`、`font_path`、`mask`、`transition_out`、`text_effect` 等字段。

## 登记和只读回读

首页索引须由剪映自身初始化。登记前保存所有工作并正常退出剪映，不能强制结束进程。
`publish` 仅登记本机首页，不上传网络。

```bash
python3 skills/yichen-jianying-edit/scripts/headless_draft.py publish --build "$PWD/work/new-build" --audit "$PWD/work/new-publish"
python3 skills/yichen-jianying-edit/scripts/headless_draft.py verify --build "$PWD/work/new-build"
```

后续原生验收需单独打开、播放、保存、退出、冷重开再播放，完成后重新执行同一 `verify`。
本适配保留 `185.0.0` → `189.0.0` 保存回读；不接受 `187.0.0` 来源。
`status: verified` 表示结构与素材检查通过，不能代替画面、听感或冷重开证据。
上面的基础示例未指定透明度，回读按默认值1检查；高级样本按计划静态值或关键帧检查。
可见性须保持 true。手动修改超出原计划时回读会拒绝；保留修改，不绕过检查。

## 故障与限制

组件或工具链不匹配时停止，保留日志；草稿已存在时换新名称，不覆盖已有工程。
`JIANYING_HEADLESS_ROOT` 可显式覆盖源码绝对路径；独立 Skill 默认查找上述标准目录，
不依赖 GUI 继承 shell 环境。安装细节见 [Skill README](../skills/yichen-jianying-edit/README.md)。
UI 导出计划以 MOV 为准；MP4 可走已验证的无损转封装，不冒充剪映 MP4 直出。
完整历史记录见 [验证状态](VERIFICATION.md)，旧库结论不迁移到当前 M5 库。
许可见 [LICENSE](../LICENSE)。


## 接着编辑或导出

[计划格式](../skills/yichen-jianying-edit/references/plan-format.md) 给出高级字段；
[编辑副本](../skills/yichen-jianying-edit/references/edit-existing-macos.md) 只修改新副本，
[UI 导出](UI-EXPORT.md) 先冻结计划，再由宿主操作剪映，最后检查实际文件。
每条路径都需保留精确库 SHA、签名、素材绑定和原来源校验；只有单测通过不代表新内容的 GUI 验收。
