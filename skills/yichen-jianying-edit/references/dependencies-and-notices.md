# 运行依赖与来源

- 当前核心 fork：<https://github.com/nikai/jianying-headless>；
  原始来源：<https://github.com/mcncarl/jianying-headless>。
  Skill 安装器不提供核心运行环境，安装路径见 [Skill README](../README.md)。
- 剪映专业版是用户单独安装的闭源依赖。官方库、字体、效果包、缓存媒体和账号权益
  不随 Skill 分发。内部接口调用不代表官方 SDK 或集成许可。
- 核心桥接头文件参考 MIT 许可的 <https://github.com/wenshui330/jy-draftc>；
  历史适配器曾使用 Apache-2.0 的 <https://github.com/GuanYixuan/pyJianYingDraft>。
  完整声明和许可证保留在核心项目。
- FFmpeg、Python 和 Xcode 是外部工具，各自条款仍适用。基础字幕使用默认系统字体，
  不需要可选字体解析器；自定义字体和音效不在当前能力范围内。
- 现有源码保留历史 ASR、Openverse 和音频处理辅助脚本；它们不属于本地适配的操作流程，
  本页不提供安装或执行指引。Skill 不包含凭据，也不从聊天、剪贴板或浏览器寻找令牌。
- 历史第三方音效属于各自作者，不在代码许可范围内。CC BY / CC BY-NC 需要署名，
  CC BY-NC 禁止商用，取得文件不等于获得许可；当前基础流程不获取或添加这些音效。

代码许可证只覆盖明示有权许可的部分，不授予剪映程序库、账号或媒体素材权利。
原创部分沿用 [个人学习和非商业使用条款](../LICENSE)，商业用途须取得作者明确书面授权。
第三方内容保留原许可，单独收录 Skill 不将整包改为 MIT / Apache-2.0 授权。
