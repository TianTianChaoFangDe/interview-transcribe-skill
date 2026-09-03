# interview-transcribe

面试录音转写与面经整理的 Skill：把面试录音 → 带时间戳的转写稿 → 一问一答面经 → 总结与改进建议。

## 功能

- 支持常见音频格式：mp3 / m4a / wav / ogg / flac / aac / opus 等
- 基于 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 本地转写，无需 ffmpeg，录音不上传云端
- 输出"面试官：/回答："一问一答形式的面经，并给出复盘总结与改进建议

## 使用方式

这是一个 Skill，将本目录放入你所使用的 AI 工具的 skills 目录即可被自动识别调用；也可以直接手动运行转写脚本：

```bash
pip install -r scripts/requirements.txt
python scripts/transcribe.py "<音频文件路径>" -l zh -m small
```

首次运行会下载 whisper 模型（small 约 460MB）；国内网络如 HuggingFace 连不上，可参考 `SKILL.md` 中的镜像方案。

## 目录结构

```
├── SKILL.md                  # Skill 主入口（工作流程说明）
├── scripts/
│   ├── transcribe.py         # 转写脚本
│   └── requirements.txt      # Python 依赖
├── references/
│   └── format-guide.md       # 面经格式规范
└── assets/
    └── report-template.md    # 面经报告模板
```

详细工作流程见 [SKILL.md](SKILL.md)。
