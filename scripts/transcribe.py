# -*- coding: utf-8 -*-
"""语音转写脚本：将面试录音（mp3/m4a/wav/ogg/flac 等）转写为带时间戳的文本。

依赖：faster-whisper（见 requirements.txt），基于 PyAV 解码，无需单独安装 ffmpeg。

用法：
    python transcribe.py <音频文件路径> [-o 输出目录] [-m 模型] [-l 语言] [--no-vad]

输出（默认写到音频所在目录，可用 -o 指定）：
    <文件名>.transcript.json   结构化分段（含起止时间，供程序处理）
    <文件名>.transcript.txt    每行 [mm:ss] 文本，供模型直接阅读整理

首次运行会自动下载所选模型（small 约 460MB，tiny 约 75MB，large-v3 约 3GB）。
"""

import argparse
import json
import sys
from pathlib import Path

SUPPORTED_EXTS = {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".wma", ".aac", ".mp4", ".webm", ".opus"}


def fmt_timestamp(seconds: float) -> str:
    """把秒数格式化为 [mm:ss] 或 [h:mm:ss]。"""
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def main() -> int:
    # Windows 下管道输出默认走 GBK，强制 UTF-8 让调用方能正确读到中文
    for stream in (sys.stdout, sys.stderr):
        if stream.encoding and stream.encoding.lower() != "utf-8":
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="面试录音转写（faster-whisper）")
    parser.add_argument("audio", help="音频文件路径（mp3/m4a/wav 等）")
    parser.add_argument("-o", "--output-dir", default=None, help="输出目录，默认为音频所在目录")
    parser.add_argument("-m", "--model", default="small",
                        help="模型大小：tiny/base/small/medium/large-v3，默认 small。中文面试建议 small 起步")
    parser.add_argument("-l", "--language", default="zh",
                        help="语言代码（zh/en/ja...），传 auto 表示自动检测，默认 zh")
    parser.add_argument("--device", default="cpu",
                        help="cpu/cuda，默认 cpu。注意：有 N 卡但没装 CUDA 运行库时 auto/cuda 会报 cublas 错误，需先装 CUDA 12 或用 cpu")
    parser.add_argument("--compute-type", default="int8", help="int8/float16/float32，默认 int8（CPU 友好）")
    parser.add_argument("--no-vad", action="store_true", help="关闭 VAD 静音过滤（默认开启，可过滤长时间静音、减少幻听）")
    args = parser.parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.is_file():
        print(f"错误：找不到音频文件：{audio_path}", file=sys.stderr)
        return 1
    if audio_path.suffix.lower() not in SUPPORTED_EXTS:
        print(f"警告：{audio_path.suffix} 不在常见音频格式列表中，仍尝试解码。", file=sys.stderr)

    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else audio_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("错误：未安装 faster-whisper，请先运行：python -m pip install -r scripts/requirements.txt", file=sys.stderr)
        return 1

    print(f"[1/2] 加载模型 {args.model}（device={args.device}, compute_type={args.compute_type}）...", flush=True)
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)

    language = None if args.language.lower() == "auto" else args.language
    # 中文场景下给出初始提示，引导输出简体中文并补上标点，可明显减少繁体字和无标点长句。
    initial_prompt = "以下是普通话面试录音的转写，使用简体中文，带标点。" if language == "zh" else None

    print(f"[2/2] 转写中：{audio_path.name} ...", flush=True)
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=not args.no_vad,
        vad_parameters=dict(min_silence_duration_ms=500),
        initial_prompt=initial_prompt,
    )

    segments = []
    for seg in segments_iter:  # segments_iter 是生成器，遍历时才真正执行转写
        segments.append({
            "id": seg.id,
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })
        print(f"  [{fmt_timestamp(seg.start)}] {seg.text.strip()}", flush=True)

    if not segments:
        print("警告：没有转写出任何内容。音频可能过短、静音过多或语言不匹配（可尝试 -l auto 或 --no-vad）。", file=sys.stderr)

    json_path = out_dir / f"{audio_path.stem}.transcript.json"
    txt_path = out_dir / f"{audio_path.stem}.transcript.txt"

    json_path.write_text(json.dumps({
        "audio": str(audio_path),
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration_seconds": round(info.duration, 2),
        "model": args.model,
        "segments": segments,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    txt_path.write_text(
        "\n".join(f"[{fmt_timestamp(s['start'])}] {s['text']}" for s in segments),
        encoding="utf-8",
    )

    print("-" * 60)
    print(f"转写完成：{len(segments)} 个分段，时长 {fmt_timestamp(info.duration)}，语言 {info.language}（置信度 {info.language_probability:.2f}）")
    print(f"JSON: {json_path}")
    print(f"TXT : {txt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
