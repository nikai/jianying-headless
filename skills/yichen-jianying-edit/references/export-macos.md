# 剪映 UI 导出与本地 MP4 转封装

后台 native ExportService 对当前官方库 ABI 不匹配，正式入口不开放。
当前已验交付为剪映 UI 渲染 MOV/H.264/AAC；plan/verify 不控制 UI，也不渲染画面。
`SKILL/BUILD/WORK` 替换为绝对路径，BUILD 可为新建或受支持编辑副本的 build。

```bash
python3 SKILL/scripts/headless_draft.py ui-export plan --build BUILD --out WORK/new-export-job
```

宿主核对当前草稿，按冻结计划在剪映导出：MOV、原始分辨率、30fps、指定本地目录。
保留视频内 AAC；独立音频文件导出、一键超清、分享和云备份保持关闭。
完成文件后关闭导出完成页，不点发布。

```bash
python3 SKILL/scripts/headless_draft.py ui-export verify --job WORK/new-export-job --video WORK/render.mov --report WORK/new-export-report.json
```

验证冻结的 build、live 草稿、当前库、画布/帧率/音频、精确帧数与完整解码。
每次保留新 attempt；计划与旧结果不覆盖。实际画面和声音仍需检查，结构与解码不替代它们。
UI 保存会修改本次输出草稿的备份/封面/时间线，verify 报告变化；编辑副本的原来源仍须不变。

需要 MP4 时可将已经核验的 MOV 无损转封装到全新文件：

```bash
ffmpeg -n -i WORK/render.mov -map 0:v:0 -map '0:a:0?' -c copy -movflags +faststart WORK/render.mp4
ffmpeg -v error -xerror -i WORK/render.mp4 -f null -
ffprobe -v error -show_streams -show_format -of json WORK/render.mp4
```

此时 renderer=剪映导出窗口，container_writer=FFmpeg stream copy；不是剪映 MP4 直出，
也不是后台原生导出。1080p/4K 合成样本已按流比较压缩包内容/顺序一致并完整解码；
新交付仍需核对尺寸、帧率、时长、声音和画面。更完整的验收语义见核心 `docs/UI-EXPORT.md`。
