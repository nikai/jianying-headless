# 编辑基础草稿的独立副本

来源限当前库支持的185/189、基础单时间线 H.264/yuv420p+AAC 与普通文字。
画布/源片符合 [计划矩阵](plan-format.md)。含复合、资源特效、动画、关键帧、自定义字体、
曲线变速或未知复杂节点的来源明确拒绝；旧187 schema 不接受。
来源逐文件保持只读，副本保留原生未修改字段，不静默抹掉未知内容来通过校验。

先保存并正常退出剪映。`SKILL/SOURCE/WORK` 替换为绝对路径：

```bash
python3 SKILL/scripts/headless_draft.py edit inspect --draft SOURCE --out WORK/inspection.json
```

从 inspection 的 source 和实际 segment/material ID 编写 `jy14-edit-plan/v1`：

```json
{
  "schema":"jy14-edit-plan/v1",
  "name":"Joker-edit-copy",
  "source":{"draft_path":"SOURCE","draft_id":"FROM_INSPECTION","timeline_sha256":"FROM_INSPECTION"},
  "operations":[
    {"op":"replace_text","id":"TEXT_MATERIAL_ID","text":"新的普通文字"},
    {"op":"set_segment","id":"VIDEO_SEGMENT_ID","set":{"volume":0.25,"duration_us":3000000,"source_duration_us":3000000}}
  ]
}
```

`set_segment` 仅允许 `start_us/duration_us/source_start_us/source_duration_us/volume`，
实际类型仍由既有校验限制；改裁切时保持1×和源片区间合法。文字可改目标起止时间。
不开放 replace_media、duplicate/remove、字体/滤镜替换、复合创建或变速。

```bash
python3 SKILL/scripts/headless_draft.py edit build --plan WORK/edit-plan.json --out WORK/edit-build
python3 SKILL/scripts/headless_draft.py edit verify-build --build WORK/edit-build
python3 SKILL/scripts/headless_draft.py edit publish --build WORK/edit-build --audit WORK/edit-publish
python3 SKILL/scripts/headless_draft.py edit verify --build WORK/edit-build --report WORK/edit-after-cold-reopen.json
```

只有已授权本机登记且关闭检查通过后才执行 publish；副本名称必须全新。
源 ID/SHA 或来源文件变化即停止，重新 inspect，不修改旧 build 记录冒充当前库。
副本需实际播放、保存退出、冷重开再回读。先完成副本验收，再考虑打开原来源：
打开来源本身可能产生原生备份和保存变化，使副本的来源不变检查失败。
导出副本用 [UI 导出](export-macos.md)，不改来源草稿。
