# M5 计划格式

直接编写 `jy14-headless-plan/v1`，不经过历史口播编译/转换入口。
素材使用有权使用的本地 H.264/yuv420p 视频：限 1280×720、1920×1080 或 3840×2160，均为30 fps、内嵌 AAC。
画布与源片尺寸/帧率匹配；不接受无音轨、非 AAC、其他像素格式或未测画布/帧率。
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

- 时间单位均为整数微秒。一条主视频轨放第一位，可多段，连续、顺序排列、不重叠；字幕和音频不超过主轨时长。
- 媒体段用 `source/start_us/duration_us/source_start_us/source_duration_us`；原片时长等于目标时长，保持1×。
- 视频可加静态 `x/y/scale/rotation/opacity/volume`。位置为归一化坐标、旋转为度，
  透明度0–1、音量0–4、缩放.01–10；视频可用这六通道的普通线性关键帧。
  关键帧源片起点为0、速度1，第一点 at_us=0，后续按时间递增且不越段尾。
- 普通文字段可用 `text/size/x/y/color/border_color/border_width/opacity/font_path`。
  颜色为 `#RRGGBB`；显式字体只接受静态本地 TTF（Monaco 已实测），需钉版 fontTools。
  检查字形覆盖、解析结构、字节和所有字体路径绑定；不会静默换字体。文字关键帧与字体动画未开放。
- 独立 `audio` 轨只接受 AAC 文件及固定 `volume`，不接受音频关键帧、变速或非 AAC。
- 视频可加 `mask`，shape 为 `circle/rectangle/line/mirror/star/heart`；配置由既有校验限制，
  非自定义矢量形状。`line` 为半平面，不支持 width/height 控制。
- 相邻主视频可用 `transition_out` 的固定 `dissolve`。帧数须为偶数，源片须有足够前后手柄；
  不接受 repeat-edge 回退，不能给最后一段添加出转场。400ms 已实测。
- 最多一条 `effect` 轨，仅 `name: light-shake`、默认参数（range=.15、speed=.33）。
  不从旧实现继承自定义参数或其他效果；不提供 filter/text_effect/复合/图片/GIF/HEVC/变速。

视频线性关键帧示例（其余五通道使用同一 at_us/value 格式）：

```json
{"keyframes":{"x":[{"at_us":0,"value":-0.25},{"at_us":2000000,"value":0.25}]}}
```

蒙版与出转场分别写在视频段，light-shake 写在 effect 轨：

```json
{"mask":{"shape":"circle"}}
```

```json
{"transition_out":{"name":"dissolve","duration_us":400000}}
```

```json
{"type":"effect","segments":[{"name":"light-shake","start_us":0,"duration_us":4000000}]}
```

资源固定 ID、目录与 catalog 逐文件 SHA 保持不变；缺失或不同字节就拒绝，不下载替代包。
原生保存后可能转为本机 cache 绑定，回读仍核对字节；资源不打包入仓，也不因此取得分发或商用权。

调用及验收见 [草稿流程](headless-macos.md)。
