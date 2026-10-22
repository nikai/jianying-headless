---
name: yichen-jianying-edit
description: 在精确匹配的 M5 剪映环境新建视频字幕与已验高级样本、编辑独立草稿副本，并制定和核验剪映 UI MOV 导出。需要 nikai/jianying-headless 核心检出；后台原生导出与复合片段不开放。
---

# M5 剪映草稿与 UI 导出

1. 按 [安装说明](README.md) 定位核心项目。默认源码为
   `~/repos/third-party/jianying-headless`，同仓入口自动定位；其他位置用
   `JIANYING_HEADLESS_ROOT=/absolute/path/to/checkout` 明确指定，失效即停。
2. 用 `scripts/headless_draft.py doctor` 核对 11.6.0 / `1748fa32…` 精确库和 codec。
   完整签名仍由真实写入与 UI 导出验收校验；不修改固定 SHA 或用旧库结论替代。
3. 新建时读 [流程](references/headless-macos.md) 和 [计划格式](references/plan-format.md)，
   在新 `work/` 目录 `build` → `verify-build`。素材和输出范围以计划格式为准。
   本地 TTF 必须有字形覆盖；资源缺失或哈希不符就报告，不下载替代包或改 catalog。
4. 编辑时读 [编辑副本](references/edit-existing-macos.md)，走
   `edit inspect` → 新计划 → `edit build` → `edit verify-build`。
   只读原来源，范围限基础视频/文字及文字替换、时间、裁切、音量；复杂来源明确拒绝。
5. 本机登记仅在任务授权且剪映已保存并退出时，用对应的 `publish` 或 `edit publish`。
   这是本机首页登记，不上传网络；后续实际播放、保存、退出、冷重开由宿主完成。
6. 导出时读 [UI 导出](references/export-macos.md)，走 `ui-export plan`，
   宿主在剪映按计划导出本地 MOV，再 `ui-export verify`。关闭分享和云备份。
   UI 由剪映渲染；可另做无损 MOV→MP4 转封装，不称为剪映 MP4 直出。
7. 用对应 `verify` 回读；报告实际画面检查、增益测量、听感、冷重开和文件解码分别完成了什么。
   `verified` 是结构检查，不自动证明实际画面和声音符合需求。

后台 native ExportService、复合片段、变速、字体动画、HEVC、照片/GIF、未测帧率/画布、
非 AAC 和 Windows 不从入口开放。历史参考文档不扩大当前许可。
2026-10-22 的宿主原生验收只证明当前精确 M5 合成样本；M1 无剪映，只部署源码/skill。

许可与依赖见 [说明](references/dependencies-and-notices.md)，官方库、字体与本机缓存不随源码分发。
