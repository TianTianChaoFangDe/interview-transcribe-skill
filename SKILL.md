---
name: interview-transcribe
description: 将面试录音文件（mp3/m4a/wav/ogg/flac 等）语音转写成文字，整理成"面试官：/回答："一问一答形式的面经，并根据面试全过程给出总结与改进建议。当用户提供面试录音、要求转写面试语音、整理面经、复盘面试时使用。
---

# 面试录音转写与面经整理

把面试录音 → 带时间戳的转写稿 → 一问一答面经 → 总结与建议。

## 工作流程

### 1. 确认输入

- 确认音频文件存在，格式为常见音频格式（.mp3 / .m4a / .wav / .ogg / .flac / .aac / .opus 等）。
- 若用户没说明，默认音频语言为中文、默认在音频所在目录输出结果。
- 若用户只要转写文字、不要整理面经，执行到第 3 步即可交付转写稿。

### 2. 检查并安装依赖

转写依赖 Python 包 faster-whisper（自带音频解码，无需安装 ffmpeg）：

```bash
python -c "import faster_whisper"
```

导入失败则安装：

```bash
python -m pip install -r "<skill目录>/scripts/requirements.txt"
```

### 3. 运行转写脚本

```bash
python "<skill目录>/scripts/transcribe.py" "<音频文件路径>" -l zh -m small
```

- 首次运行会下载模型（small 约 460MB），提前告知用户需要等待；下载完成后自动开始转写。
- **模型下载失败（HuggingFace 连不上/超时）**：通过镜像站下载，在命令前加环境变量（已验证可行）：
  ```bash
  HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 python "<skill目录>/scripts/transcribe.py" ...
  ```
  其中 `HF_HUB_DISABLE_XET=1` 是必须的——镜像站不支持 xet 存储协议，不禁用会报 401。
- CPU 上转写速度约为音频时长的 0.2~0.5 倍，1 小时录音大约需要 10~30 分钟；有 NVIDIA 显卡且已装 CUDA 12 运行库时可加 `--device cuda --compute-type float16` 提速数倍（没装 CUDA 运行库会报 cublas 错误，默认 cpu 即可）。
- 准确率不够时换更大模型 `-m medium` 或 `-m large-v3`；只想快速验证流程用 `-m tiny`。
- 转写结束会打印两个文件路径：`<文件名>.transcript.json`（结构化分段）和 `<文件名>.transcript.txt`（带时间戳的逐行文本）。
- 若转写结果为空或明显错乱：依次尝试 `-l auto`、加 `--no-vad`、换更大的模型。

### 4. 阅读转写稿，整理成一问一答

- 用 Read 工具读取 `.transcript.txt`。文件较长时分段读取（offset/limit），按时间戳顺序处理，不要遗漏中段内容。
- 整理规则（角色判断、文本清理、段落合并）详见 [references/format-guide.md](references/format-guide.md)，必须遵守。
- 核心原则：**忠实还原面试现场**。不虚构转写稿中不存在的内容，不替候选人"优化"回答内容本身；整理的是结构和可读性，不是改写事实。

### 5. 生成总结与建议

基于整理后的完整问答，按 format-guide.md 中"总结与建议"章节的结构撰写：面试概览、表现亮点、暴露问题、重点问题改进建议、后续准备方向。建议要具体、引用面试中的实际问答，避免空泛。

### 6. 输出面经

- 按 [assets/report-template.md](assets/report-template.md) 的骨架填充，保存为 `<音频文件名>_面经.md`，默认放在音频所在目录（用户另有指定则从用户）。
- 告知用户输出文件路径，并提醒：语音转写可能存在错字（尤其技术名词、英文术语），面经开头已附相关说明。

## 注意

- 多位面试官的录音：能从上下文区分时标注"面试官 A/B"，无法区分统一写"面试官"。
- 非面试录音（会议、演讲等）：仍可转写，但整理形式先询问用户，不要硬套问答模板。
- 转写稿包含对话隐私，所有处理均在本地完成，不要把音频或转写内容上传到外部服务。
