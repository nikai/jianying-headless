# M5 本机基础草稿

本页只适用于本地 11.6.0 / `1748fa32…` 库。精确身份由 `doctor` 检查，
旧库 `a490d9a0…` 生成的 build 也会在验证和登记时被拒绝；版本字符串相同不足以复用。
支持一条 H.264 视频轨和普通字幕轨，时间均为整数微秒；完整示例见 [计划格式](plan-format.md)。
素材和画布均限 1280×720、30 fps；素材必须为 yuv420p 并内嵌 AAC。
其他像素格式、音频编码、尺寸、帧率和无音轨输入均拒绝，不自动转码。

## 入口

入口为本 Skill 的 `scripts/headless_draft.py`。同仓自动定位核心；独立安装默认找
`~/repos/third-party/jianying-headless`，其他位置用 `JIANYING_HEADLESS_ROOT` 指定绝对路径。
Skill 核验核心代码哈希，官方程序库和私人素材不随包分发。

以下 `SKILL`、`WORK` 为待替换的绝对路径；输出使用本次 `work/` 下的新目录。
只在已授权本机登记且剪映正常退出后运行登记命令。

```bash
python3 SKILL/scripts/headless_draft.py doctor
python3 SKILL/scripts/headless_draft.py build --plan WORK/plan.json --out WORK/build
python3 SKILL/scripts/headless_draft.py verify-build --build WORK/build
python3 SKILL/scripts/headless_draft.py publish --build WORK/build --audit WORK/publish-audit
python3 SKILL/scripts/headless_draft.py verify --build WORK/build --report WORK/after-native-save.json
```

`build` 只写隔离目录；`publish` 只登记本机首页，不上传网络。
`verify` 是只读结构检查，支持本机基础草稿的 `185→189` 保存回读。
回读要求默认透明度 1 和可见性 true，省略字段时按默认值判断。
实际播放、人工听感、保存退出和冷重开仍需单独完成，不能从 `verified` 推断。

## 能力边界

仅使用上述五个命令。编辑既有草稿、复合片段、所有导出、独立音效/BGM、资源特效、
自定义字体、关键帧、蒙版、转场、变速、HEVC、图片和 GIF 均未开放。
视频自带音频随素材保留。旧库高级验收记录不作为当前操作指引。
需要超出范围的任务时向宿主报告缺口，保留已有草稿，不换入口绕过能力门。
