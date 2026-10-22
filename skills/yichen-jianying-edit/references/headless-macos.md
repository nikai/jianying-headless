# M5 本机草稿流程

仅适用于本地 11.6.0 / `1748fa32…` 精确库。先运行 `doctor`，
计划与编码/画布矩阵见 [计划格式](plan-format.md)。不自动转码；旧库 build 不作为当前证据。

以下 `SKILL` 和 `WORK` 替换为绝对路径，输出使用本次不存在的新目录。

```bash
python3 SKILL/scripts/headless_draft.py build --plan WORK/plan.json --out WORK/build
python3 SKILL/scripts/headless_draft.py verify-build --build WORK/build
python3 SKILL/scripts/headless_draft.py publish --build WORK/build --audit WORK/publish-audit
python3 SKILL/scripts/headless_draft.py verify --build WORK/build --report WORK/after-cold-reopen.json
```

`build` 只写隔离目录；`publish` 仅在任务授权且剪映正常退出时登记本机首页。
`verify` 只读核对当前库的 `185→189` 保存回读、镜像、素材与计划节点。
可见性须保持 true；透明度与计划静态值或关键帧一致。只有计划内的字体、资源与关键帧可接受。

实际播放、保存退出和冷重开是独立验收；导出见 [UI 导出](export-macos.md)，
编辑原有基础草稿见 [编辑副本](edit-existing-macos.md)。
部分资源保存后绑定到经过字节校验的原生缓存；保留本机缓存，不能承诺草稿完全独立迁移。
