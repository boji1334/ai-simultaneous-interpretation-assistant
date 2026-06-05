from __future__ import annotations

import math
import subprocess
import textwrap
import wave
from dataclasses import dataclass
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "demo"
OUTPUT = ASSET_DIR / "final-demo.mp4"
VIDEO_ONLY = ASSET_DIR / "final-demo-video-only.mp4"
NARRATION = ASSET_DIR / "final-demo-narration.wav"
SCENE_AUDIO_DIR = ASSET_DIR / ".demo-video-audio"

WIDTH = 1280
HEIGHT = 720
FPS = 10

FONT_REGULAR = Path("C:/Windows/Fonts/NotoSansSC-VF.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/simhei.ttf")


@dataclass
class Scene:
    title: str
    narration: str
    kind: str
    bullets: list[str]


SCENES = [
    Scene(
        title="AI 同声传译助手",
        kind="opening",
        narration=(
            "大家好，这是我们的 AI 同声传译助手。它面向英文技术分享、国际会议和网课场景，"
            "把单向英文音频流实时翻译成中文字幕，并且能够在后文信息到达后，自动修正前文的识别或翻译错误。"
        ),
        bullets=[
            "题目要求：实时、流畅翻译单向音频流",
            "呈现方式：中文字幕为主，可选语音播报",
            "核心能力：自动纠正之前识别或翻译的错误",
        ],
    ),
    Scene(
        title="系统架构",
        kind="architecture",
        narration=(
            "系统采用 React 前端和 FastAPI 后端。音频事件通过 WebSocket 流式进入，"
            "再经过 ASR Provider、翻译 Provider、字幕状态机和上下文修正引擎。"
            "ASR 和翻译能力可以替换成本地 faster-whisper 或云端接口，原创重点放在状态流转和修正逻辑。"
        ),
        bullets=[
            "Provider 可插拔：Mock、faster-whisper、云端翻译接口",
            "字幕状态：partial、stable、corrected、final",
            "修正链路：术语表 + 滑动窗口 + 版本轨迹",
        ],
    ),
    Scene(
        title="实时字幕流",
        kind="stream",
        narration=(
            "启动实时演示后，字幕不是一次性加载，而是按事件逐条出现。"
            "同一条字幕可以先快速显示临时版本，再变成稳定版本，最后进入最终状态。"
            "这样可以同时兼顾低延迟和可读性。"
        ),
        bullets=[
            "首字幕延迟：约 820 毫秒",
            "字幕可从临时状态升级为最终状态",
            "最终字幕可导出为 Markdown 或 SRT",
        ],
    ),
    Scene(
        title="修正能力：黄金时刻",
        kind="correction",
        narration=(
            "重点看修正能力。系统一开始把 tension mechanism 翻译成张力机制，"
            "这是一个看似合理但在上下文中错误的翻译。后文出现 attention mechanism 后，"
            "滑动窗口和术语表共同触发回溯修正，把前文改成注意力机制，并保留修正前文本、触发原因和版本变化。"
        ),
        bullets=[
            "修正前：这个模型使用张力机制来判断哪些词更重要。",
            "修正后：这个模型使用注意力机制来判断哪些词更重要。",
            "修正记录：1480ms，v1 -> v2，attention mechanism",
        ],
    ),
    Scene(
        title="同步素材同传",
        kind="synced",
        narration=(
            "为了保证比赛演示稳定，我们的主 demo 使用自写英文脚本生成的 TTS 音频。"
            "播放器按真实音频时间显示双语字幕：中文同传在上，英文原文在下。"
            "十四秒左右先出现错误译文，二十一秒左右后文到达后，播放器浮层会闪现已修正字幕。"
        ),
        bullets=[
            "自写素材：无版权风险，可复现",
            "严格同步：音频 currentTime 驱动字幕显示",
            "展示题目核心：实时翻译 + 后文触发修正",
        ],
    ),
    Scene(
        title="可审计输出",
        kind="audit",
        narration=(
            "右侧面板会展示修正时间线、字幕版本轨迹、术语表、量化指标和会后总结。"
            "这让自动修正不再是一次静默覆盖，而是可解释、可审计、可复盘的工程行为。"
        ),
        bullets=[
            "修正时间线：触发原因、延迟、前后版本",
            "量化指标：首字幕延迟、修正延迟、术语命中率",
            "会后总结：关键点、术语、修正说明",
        ],
    ),
    Scene(
        title="工程与提交质量",
        kind="quality",
        narration=(
            "工程侧已经提供测试、单服务冒烟、提交前审计和完整 README。"
            "仓库通过多个小 PR 持续迭代，主分支保持可运行。"
            "最终评审时，评委可以直接运行脚本，复现同步同传、自动修正、导出和总结能力。"
        ),
        bullets=[
            "后端测试：26 个用例通过",
            "单服务复现：http://127.0.0.1:8000",
            "PR 记录：MVP、时间同步、双语浮层、同步素材",
        ],
    ),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size=size)


def synthesize_scene_audio(scene: Scene, index: int) -> Path:
    SCENE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    text_path = SCENE_AUDIO_DIR / f"scene-{index:02d}.txt"
    wav_path = SCENE_AUDIO_DIR / f"scene-{index:02d}.wav"
    text_path.write_text(scene.narration, encoding="utf-8")
    ps = f"""
Add-Type -AssemblyName System.Speech
$text = Get-Content -LiteralPath '{text_path}' -Raw -Encoding UTF8
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.SelectVoice('Microsoft Huihui Desktop')
$speaker.Rate = 0
$speaker.Volume = 100
$speaker.SetOutputToWaveFile('{wav_path}')
$speaker.Speak($text)
$speaker.Dispose()
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        check=True,
        cwd=ROOT,
    )
    return wav_path


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def combine_wavs(paths: list[Path], output: Path) -> None:
    params = None
    silence_seconds = 0.25
    with wave.open(str(output), "wb") as out:
        for index, path in enumerate(paths):
            with wave.open(str(path), "rb") as src:
                if params is None:
                    params = src.getparams()
                    out.setparams(params)
                elif src.getparams()[:3] != params[:3]:
                    raise RuntimeError(f"Incompatible WAV params: {path}")
                out.writeframes(src.readframes(src.getnframes()))
                if index < len(paths) - 1:
                    silence_frames = int(src.getframerate() * silence_seconds)
                    out.writeframes(b"\x00" * silence_frames * src.getnchannels() * src.getsampwidth())


def wrap(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        current = ""
        for char in paragraph:
            candidate = current + char
            if draw.textbbox((0, 0), candidate, font=font_obj)[2] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = char
        if current:
            lines.append(current)
    return lines


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None, radius: int = 8) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2 if outline else 1)


def text_block(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font_obj: ImageFont.FreeTypeFont, fill: str, max_width: int, line_gap: int = 8) -> int:
    x, y = xy
    for line in wrap(draw, text, font_obj, max_width):
        draw.text((x, y), line, font=font_obj, fill=fill)
        y += font_obj.size + line_gap
    return y


def base_scene(scene: Scene, index: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), "#f4f7fb")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 92), fill="#122033")
    draw.text((48, 28), "AI 同声传译助手", font=font(30, True), fill="#ffffff")
    draw.text((1010, 32), f"Demo {index + 1}/{len(SCENES)}", font=font(20), fill="#c7d8ec")
    draw.text((48, 118), scene.title, font=font(42, True), fill="#172234")
    return img, draw


def draw_bullets(draw: ImageDraw.ImageDraw, bullets: list[str], x: int, y: int, width: int) -> None:
    body = font(25)
    for item in bullets:
        rounded(draw, (x, y, x + width, y + 72), "#ffffff", "#d8e2ee")
        draw.ellipse((x + 20, y + 23, x + 40, y + 43), fill="#1d8f6f")
        text_block(draw, (x + 58, y + 18), item, body, "#243247", width - 82, 4)
        y += 88


def draw_architecture(draw: ImageDraw.ImageDraw) -> None:
    labels = ["音频流", "ASR", "翻译", "状态机", "修正引擎", "字幕 UI"]
    x = 92
    y = 310
    w = 155
    for label in labels:
        rounded(draw, (x, y, x + w, y + 84), "#ffffff", "#cad6e5")
        draw.text((x + 28, y + 24), label, font=font(25, True), fill="#172234")
        if label != labels[-1]:
            draw.line((x + w + 12, y + 42, x + w + 48, y + 42), fill="#2e7d61", width=5)
            draw.polygon([(x + w + 48, y + 42), (x + w + 32, y + 32), (x + w + 32, y + 52)], fill="#2e7d61")
        x += w + 60


def draw_subtitle_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], status: str, zh: str, en: str, accent: str) -> None:
    x1, y1, x2, y2 = box
    rounded(draw, box, "#ffffff", "#d7e1ec")
    draw.rectangle((x1, y1, x1 + 8, y2), fill=accent)
    draw.text((x1 + 24, y1 + 16), status, font=font(20, True), fill=accent)
    text_block(draw, (x1 + 24, y1 + 48), en, font(20), "#526073", x2 - x1 - 48, 3)
    text_block(draw, (x1 + 24, y1 + 90), zh, font(26, True), "#162033", x2 - x1 - 48, 4)


def draw_media_stage(draw: ImageDraw.ImageDraw, corrected: bool) -> None:
    rounded(draw, (82, 206, 828, 626), "#111827", "#26364d")
    draw.text((126, 254), "AI TECH TALK", font=font(20, True), fill="#6ee7b7")
    draw.text((126, 294), "Real-time AI Interpretation", font=font(40, True), fill="#ffffff")
    draw.text((126, 350), "Original English audio · synchronized Chinese interpretation", font=font(21), fill="#bfd2e8")
    bars = [36, 62, 44, 80, 50, 66, 38, 72]
    for i, h in enumerate(bars):
        x = 135 + i * 24
        draw.rounded_rectangle((x, 448 - h, x + 12, 448), radius=6, fill="#f4d35e")
    rounded(draw, (110, 488, 800, 604), "#081320", "#3c4d66")
    status = "已修正 · v2" if corrected else "稳定 · v1"
    zh = "这个模型使用注意力机制来判断哪些词更重要。" if corrected else "这个模型使用张力机制来判断哪些词更重要。"
    en = "The model uses a tension mechanism to decide which words matter."
    draw.text((132, 506), status, font=font(18, True), fill="#9ee7ca" if corrected else "#c8d8ef")
    draw.text((132, 536), zh, font=font(27, True), fill="#ffffff")
    draw.text((132, 572), en, font=font(18, True), fill="#dce8f5")
    if corrected:
        draw.text((110, 628), "修正前：这个模型使用张力机制来判断哪些词更重要。", font=font(18), fill="#8b5d08")


def render_scene(scene: Scene, index: int, progress: float) -> Image.Image:
    img, draw = base_scene(scene, index)
    draw_bullets(draw, scene.bullets, 780, 170, 420)

    if scene.kind == "opening":
        rounded(draw, (78, 190, 710, 600), "#ffffff", "#d6e2ef")
        draw.text((118, 234), "题目二", font=font(30, True), fill="#1d8f6f")
        text_block(draw, (118, 292), "通过 AI 能力，将单向音频流实时、流畅地翻译成中文，以字幕或语音形式呈现。系统需具备修正能力，能够自动纠正之前识别或翻译的错误。", font(31, True), "#172234", 520, 12)
    elif scene.kind == "architecture":
        draw_architecture(draw)
    elif scene.kind == "stream":
        draw_subtitle_card(draw, (78, 184, 720, 314), "临时 · v1", "大家早上好，今天我们将探索实时 AI 同声传译。", "Good morning everyone, today we will explore real-time AI interpretation.", "#778397")
        draw_subtitle_card(draw, (78, 342, 720, 472), "稳定 · v1", "这个模型使用张力机制来判断哪些词更重要。", "The model uses a tension mechanism to decide which words matter.", "#2f6fd6")
        draw_subtitle_card(draw, (78, 500, 720, 630), "最终 · v1", "一个小型术语表可以帮助系统保持技术术语翻译一致。", "A small glossary helps the system keep technical terms consistent.", "#2e7d61")
    elif scene.kind == "correction":
        corrected = progress > 0.46
        draw_subtitle_card(draw, (82, 190, 700, 350), "稳定 · v1", "这个模型使用张力机制来判断哪些词更重要。", "The model uses a tension mechanism to decide which words matter.", "#2f6fd6")
        arrow = "后文出现 attention mechanism 后触发回溯修正"
        draw.text((116, 382), arrow, font=font(24, True), fill="#8b5d08")
        if corrected:
            draw_subtitle_card(draw, (82, 426, 700, 612), "已修正 · v2", "这个模型使用注意力机制来判断哪些词更重要。", "The model uses a tension mechanism to decide which words matter.", "#c49513")
    elif scene.kind == "synced":
        draw_media_stage(draw, corrected=progress > 0.5)
        rounded(draw, (82, 640, 828, 668), "#dfe9f5", None)
        marker_x = 82 + int(746 * min(max(progress, 0), 1))
        draw.rectangle((82, 640, marker_x, 668), fill="#1d8f6f")
        draw.text((94, 646), "音频播放时间驱动字幕显示", font=font(15, True), fill="#172234")
    elif scene.kind == "audit":
        draw_subtitle_card(draw, (78, 190, 700, 330), "修正时间线", "触发：后续上下文出现 attention mechanism；延迟：1480ms；版本：v1 -> v2。", "Correction trace keeps the reason, latency, and version history.", "#c49513")
        draw_subtitle_card(draw, (78, 370, 700, 522), "会后总结", "系统自动输出关键点、术语和修正说明，方便课后复盘。", "Summary, glossary, correction notes, and transcript export.", "#2e7d61")
    elif scene.kind == "quality":
        rounded(draw, (88, 198, 700, 580), "#162033", "#26364d")
        lines = [
            "✓ 26 backend tests passed",
            "✓ Frontend production build passed",
            "✓ Single-service smoke passed",
            "✓ README documents original boundaries",
            "✓ PR history shows continuous delivery",
        ]
        for i, line in enumerate(lines):
            draw.text((126, 242 + i * 58), line, font=font(27, True), fill="#e7f3ff")
    return img


def render_video(scene_durations: list[float]) -> None:
    writer = imageio.get_writer(
        str(VIDEO_ONLY),
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=8,
    )
    try:
        for index, (scene, duration) in enumerate(zip(SCENES, scene_durations)):
            frames = max(1, math.ceil(duration * FPS))
            for frame in range(frames):
                progress = frame / max(frames - 1, 1)
                writer.append_data(np.asarray(render_scene(scene, index, progress)))
    finally:
        writer.close()


def mux_audio() -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(VIDEO_ONLY),
            "-i",
            str(NARRATION),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            str(OUTPUT),
        ],
        check=True,
    )


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    audio_paths = [synthesize_scene_audio(scene, index) for index, scene in enumerate(SCENES)]
    durations = [wav_duration(path) + 0.25 for path in audio_paths]
    combine_wavs(audio_paths, NARRATION)
    render_video(durations)
    mux_audio()
    print(f"Generated demo video: {OUTPUT}")


if __name__ == "__main__":
    main()
