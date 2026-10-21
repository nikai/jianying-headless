# M5 基础计划格式

直接编写 `jy14-headless-plan/v1`，不经过历史口播编译/转换入口。
素材使用有权使用的本地 H.264/yuv420p 视频：限 1280×720、30 fps，内嵌 AAC。
画布固定 1280×720、30 fps；不接受无音轨、其他音频编码、像素格式、尺寸或帧率。
下面示例需要至少 4 秒素材；替换素材绝对路径，使用未登记过的新名称。

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

- 时间单位均为整数微秒。一条主视频轨放在第一位，片段连续、顺序排列、不重叠。
- 视频段仅使用 `source`、`start_us`、`duration_us`、`source_start_us`、`source_duration_us`。
  原片裁切时长与目标时长相等，保持 1×。省略原片起点时从 0 开始，省略原片时长时沿用目标时长。
- 字幕轨使用 `text` 类型，片段仅使用 `text`、`start_us`、`duration_us`、`size`、
  `x`、`y`、`color`、`border_color`、`border_width`。字幕范围不超过主视频总长。
- 颜色用 `#RRGGBB`，字体沿用默认系统字体。视频自带 AAC 音频保留。
- 视频和字幕保持默认透明度 1、可见性 true；保存回读也核对这些默认值。
- 不添加音频轨、音量字段、变速、图片、HEVC、自定义字体、动画、特效或复合结构。

调用及验收见 [基础流程](headless-macos.md)。需要转写或更复杂的剪辑时向宿主报告，
本适配不提供高级脚本的可执行流程。
