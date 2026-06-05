from __future__ import annotations

import math
import os
import re
import subprocess
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
FPS = 12
TTS_PROVIDER = os.getenv("DEMO_TTS_PROVIDER", "auto").strip().lower()
TTS_VOICE = os.getenv("DEMO_TTS_VOICE", "zh-CN-XiaoxiaoNeural")
TTS_RATE = os.getenv("DEMO_TTS_RATE", "+7%")
TTS_PITCH = os.getenv("DEMO_TTS_PITCH", "+4Hz")
TTS_VOLUME = os.getenv("DEMO_TTS_VOLUME", "+0%")

FONT_REGULAR = Path("C:/Windows/Fonts/NotoSansSC-VF.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/simhei.ttf")

INK = "#172234"
MUTED = "#667386"
BG = "#f5f8fc"
NAVY = "#111d2f"
GREEN = "#1d8f6f"
GOLD = "#f4d35e"
BLUE = "#2f6fd6"
LINE = "#d8e2ee"


@dataclass
class Scene:
    title: str
    claim: str
    narration: str
    kind: str
    bullets: list[str]


SCENES = [
    Scene(
        title="AI 同声传译助手",
        claim="把单向英文音频流实时翻译成中文，并能回头修正前文错误。",
        kind="cover",
        narration=(
            "大家好，先用一分钟看清楚我们的作品。"
            "这是 AI 同声传译助手，面向英文演讲、技术分享、国际会议和网课。"
            "它不是等整段音频结束再翻译，而是边听、边出中文字幕。"
            "更关键的是，当后文信息来了，它会主动回头修正前面翻错的内容。"
        ),
        bullets=["实时中文字幕", "上下文回溯修正", "可复现演示材料"],
    ),
    Scene(
        title="核心难点",
        claim="同传不是简单串联 ASR 和翻译，真正难点是低延迟与后文纠错同时成立。",
        kind="challenge",
        narration=(
            "这个题目的难点，其实不在于把 ASR 和翻译接口串起来。"
            "真正难的是两个目标同时成立：字幕要快，不能让用户等；但翻译又要能根据后文纠错。"
            "所以我们采用先跟上、再修正的策略。先给用户可读字幕，再用上下文做局部回溯。"
        ),
        bullets=["低延迟：先显示 partial / stable", "高准确：后文触发 corrected", "低打扰：只修正局部字幕"],
    ),
    Scene(
        title="系统架构",
        claim="Provider 可替换，核心原创逻辑集中在字幕状态机和修正引擎。",
        kind="architecture",
        narration=(
            "架构上，前端用 React，后端用 FastAPI 和 WebSocket。"
            "音频事件流进来以后，会依次经过 ASR、翻译、字幕状态机和修正引擎。"
            "ASR 和翻译都做成 Provider，可替换、可降级。"
            "我们的原创重点，放在字幕状态流转、上下文修正和版本轨迹上。"
        ),
        bullets=["React / Vite / TypeScript", "FastAPI / WebSocket", "Mock、faster-whisper、云翻译可切换"],
    ),
    Scene(
        title="实时字幕流",
        claim="同一条字幕从临时、稳定、已修正到最终状态，完整回应“实时”和“修正”。",
        kind="stream",
        narration=(
            "进入实时字幕流，可以看到字幕是一条一条出现的。"
            "每条字幕都有状态：先是 partial，随后 stable。"
            "如果后文证明前面理解错了，它会变成 corrected。"
            "最后进入 final，并用于 SRT 或 Markdown 导出。"
        ),
        bullets=["首字幕延迟约 820ms", "状态：partial -> stable -> corrected -> final", "最终字幕支持 Markdown / SRT 导出"],
    ),
    Scene(
        title="修正能力",
        claim="后文出现 attention mechanism 后，系统把“张力机制”回溯修正为“注意力机制”。",
        kind="correction",
        narration=(
            "这是 Demo 的黄金时刻。"
            "系统一开始把 tension mechanism 翻成了张力机制，听上去合理，但在这个技术语境里是错的。"
            "当后面出现 attention mechanism，术语表和滑动窗口会重新判断语义。"
            "于是系统回头把前面的译文修正为注意力机制，并记录触发原因、延迟和版本变化。"
        ),
        bullets=["修正延迟：1480ms", "版本变化：v1 -> v2", "修正记录可审计"],
    ),
    Scene(
        title="同步素材同传",
        claim="主 demo 使用自写英文音频，字幕由播放时间驱动，避免公开视频时间轴错位。",
        kind="synced",
        narration=(
            "为了让评委稳定复现，我们主 Demo 使用自写英文脚本生成音频。"
            "播放器不是预加载整段翻译，而是根据真实播放时间推进字幕。"
            "中文同传显示在上方，英文原文显示在下方。"
            "先让错误译文出现，再让后文触发修正，这样题目的核心要求会非常直观。"
        ),
        bullets=["自写音频：无版权风险", "字幕跟随 currentTime", "中文在上，英文在下"],
    ),
    Scene(
        title="演示闭环",
        claim="修正时间线、版本轨迹、术语表、指标、导出和总结构成完整产品闭环。",
        kind="audit",
        narration=(
            "我们没有把修正做成一次静默覆盖。"
            "右侧面板会展示修正时间线、版本轨迹、术语命中、量化指标和会后总结。"
            "也就是说，评委不仅能看到字幕变对了，还能看到它为什么变、什么时候变、从哪个版本变到哪个版本。"
        ),
        bullets=["修正时间线：原因、延迟、版本", "量化指标：首字幕延迟、术语命中率", "会后复盘：总结、关键词、导出"],
    ),
    Scene(
        title="工程质量",
        claim="项目已具备可运行主分支、测试、CI、冒烟验收、README 和 demo 视频。",
        kind="quality",
        narration=(
            "最后看工程质量。"
            "项目已经提供后端测试、前端构建、单服务冒烟和提交前审计。"
            "仓库通过多个小 PR 持续交付，主分支始终保持可运行。"
            "评委可以直接根据 README，复现同步同传、自动修正、导出和总结能力。"
        ),
        bullets=["26 个后端测试通过", "单服务地址：http://127.0.0.1:8000", "README、Release 视频、PR 记录齐备"],
    ),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size=size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def tokens(text: str) -> list[str]:
    pattern = r"[A-Za-z0-9][A-Za-z0-9_+./:()%-]*|[\u4e00-\u9fff]|[^\s]"
    return re.findall(pattern, text)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        current = ""
        for token in tokens(paragraph):
            joiner = "" if not current or re.fullmatch(r"[\u4e00-\u9fff]|[^\w\s]", token) else " "
            candidate = f"{current}{joiner}{token}" if current else token
            if text_size(draw, candidate, fnt)[0] <= width:
                current = candidate
                continue
            if current:
                lines.append(current)
            if text_size(draw, token, fnt)[0] <= width:
                current = token
            else:
                current = ""
                chunk = ""
                for char in token:
                    candidate = chunk + char
                    if text_size(draw, candidate, fnt)[0] <= width:
                        chunk = candidate
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = char
                current = chunk
        if current:
            lines.append(current)
    return lines


def draw_fit_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    max_size: int,
    min_size: int,
    fill: str,
    bold: bool = False,
    align: str = "left",
    valign: str = "top",
    line_gap: int = 6,
) -> int:
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    chosen_font = font(min_size, bold)
    chosen_lines = wrap_text(draw, text, chosen_font, width)
    chosen_gap = max(2, min(line_gap, 5))
    for size in range(max_size, min_size - 1, -1):
        fnt = font(size, bold)
        lines = wrap_text(draw, text, fnt, width)
        gap = max(2, int(size * 0.22))
        total = len(lines) * size + max(0, len(lines) - 1) * gap
        if total <= height and all(text_size(draw, line, fnt)[0] <= width for line in lines):
            chosen_font = fnt
            chosen_lines = lines
            chosen_gap = gap
            break
    total_height = len(chosen_lines) * chosen_font.size + max(0, len(chosen_lines) - 1) * chosen_gap
    y = y1
    if valign == "middle":
        y = y1 + max(0, (height - total_height) // 2)
    elif valign == "bottom":
        y = y2 - total_height
    for line in chosen_lines:
        line_width = text_size(draw, line, chosen_font)[0]
        x = x1
        if align == "center":
            x = x1 + max(0, (width - line_width) // 2)
        elif align == "right":
            x = x2 - line_width
        draw.text((x, y), line, font=chosen_font, fill=fill)
        y += chosen_font.size + chosen_gap
    return y


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None, radius: int = 8) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2 if outline else 1)


def base_slide(scene: Scene, index: int, dark: bool = False) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), NAVY if dark else BG)
    draw = ImageDraw.Draw(img)
    if not dark:
        draw.rectangle((0, 0, WIDTH, 84), fill=NAVY)
        draw.text((52, 24), "AI 同声传译助手", font=font(27, True), fill="#ffffff")
        draw.text((1060, 28), f"{index + 1:02d} / {len(SCENES):02d}", font=font(20), fill="#b8cbe3")
        draw_fit_text(draw, (52, 112, 780, 166), scene.title, 39, 30, INK, bold=True)
        draw_fit_text(draw, (54, 166, 760, 222), scene.claim, 21, 16, "#536176", line_gap=3)
    return img, draw


def draw_side_notes(draw: ImageDraw.ImageDraw, bullets: list[str]) -> None:
    x, y, w = 842, 154, 350
    draw.text((x, y - 42), "评审看点", font=font(24, True), fill=INK)
    for item in bullets:
        rounded(draw, (x, y, x + w, y + 82), "#ffffff", LINE, 8)
        draw.ellipse((x + 18, y + 29, x + 38, y + 49), fill=GREEN)
        draw_fit_text(draw, (x + 54, y + 16, x + w - 18, y + 68), item, 22, 15, "#243247", bold=True, valign="middle")
        y += 102


def draw_pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: str) -> None:
    x, y = xy
    w = text_size(draw, text, font(22, True))[0] + 44
    rounded(draw, (x, y, x + w, y + 48), color, None, 24)
    draw_fit_text(draw, (x + 20, y + 8, x + w - 20, y + 40), text, 22, 18, "#ffffff", bold=True, align="center")


def draw_cover(scene: Scene, index: int) -> Image.Image:
    img, draw = base_slide(scene, index, dark=True)
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=NAVY)
    draw.rectangle((0, 0, 14, HEIGHT), fill=GREEN)
    draw_fit_text(draw, (82, 88, 760, 160), "题目二", 30, 24, "#6ee7b7", bold=True)
    draw_fit_text(draw, (82, 162, 850, 276), scene.title, 66, 52, "#ffffff", bold=True)
    draw_fit_text(draw, (86, 292, 810, 372), scene.claim, 30, 23, "#cfe0f3", bold=True)
    draw_pill(draw, (84, 430), "实时", GREEN)
    draw_pill(draw, (214, 430), "中文呈现", BLUE)
    draw_pill(draw, (390, 430), "自动修正", "#c49513")
    rounded(draw, (842, 118, 1166, 520), "#18263b", "#31445d", 8)
    draw_fit_text(draw, (884, 160, 1128, 232), "Demo 主线", 34, 28, "#ffffff", bold=True)
    draw_fit_text(draw, (884, 252, 1120, 438), "单向音频流\n实时中文字幕\n后文触发回溯修正\n版本轨迹可审计", 28, 20, "#d9e8f8", bold=True, line_gap=10)
    return img


def draw_challenge(scene: Scene, index: int) -> Image.Image:
    img, draw = base_slide(scene, index)
    cards = [
        ("低延迟", "先给用户可读字幕", "#e6f5ef", GREEN),
        ("后文信息", "语义到达后重新判断", "#fff6d8", "#c49513"),
        ("局部修正", "只更新最近相关字幕", "#eaf1ff", BLUE),
    ]
    x = 68
    for title, body, fill, accent in cards:
        rounded(draw, (x, 292, x + 224, 512), fill, "#cfd9e6", 8)
        draw.rectangle((x, 292, x + 224, 302), fill=accent)
        draw_fit_text(draw, (x + 24, 334, x + 200, 386), title, 32, 24, INK, bold=True, align="center")
        draw_fit_text(draw, (x + 26, 406, x + 198, 470), body, 22, 16, "#46556a", bold=True, align="center", valign="middle")
        x += 250
    draw_side_notes(draw, scene.bullets)
    return img


def draw_architecture(scene: Scene, index: int) -> Image.Image:
    img, draw = base_slide(scene, index)
    labels = ["音频流", "ASR", "翻译", "状态机", "修正引擎", "字幕 UI"]
    x, y = 64, 330
    w = 96
    gap = 34
    for i, label in enumerate(labels):
        rounded(draw, (x, y, x + w, y + 82), "#ffffff", "#cfd9e6", 8)
        draw_fit_text(draw, (x + 8, y + 22, x + w - 8, y + 58), label, 20, 14, INK, bold=True, align="center", valign="middle")
        if i < len(labels) - 1:
            draw.line((x + w + 8, y + 41, x + w + gap - 8, y + 41), fill=GREEN, width=5)
            draw.polygon([(x + w + gap - 8, y + 41), (x + w + gap - 24, y + 31), (x + w + gap - 24, y + 51)], fill=GREEN)
        x += w + gap
    rounded(draw, (92, 492, 752, 594), "#ffffff", LINE, 8)
    draw_fit_text(draw, (126, 518, 718, 560), "核心原创：字幕状态机 + 上下文修正引擎 + 可审计版本轨迹", 26, 20, INK, bold=True, align="center", valign="middle")
    draw_side_notes(draw, scene.bullets)
    return img


def subtitle_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    status: str,
    zh: str,
    en: str,
    accent: str,
    fill: str = "#ffffff",
) -> None:
    x1, y1, x2, y2 = box
    rounded(draw, box, fill, "#ccd8e6", 8)
    draw.rectangle((x1, y1, x1 + 8, y2), fill=accent)
    draw_fit_text(draw, (x1 + 24, y1 + 12, x2 - 24, y1 + 40), status, 18, 14, accent, bold=True)
    draw_fit_text(draw, (x1 + 24, y1 + 48, x2 - 24, y1 + 86), en, 18, 13, "#5d6a7b")
    draw_fit_text(draw, (x1 + 24, y1 + 86, x2 - 24, y2 - 18), zh, 24, 17, INK, bold=True)


def draw_stream(scene: Scene, index: int) -> Image.Image:
    img, draw = base_slide(scene, index)
    subtitle_card(draw, (74, 244, 752, 360), "partial · v1", "大家早上好，今天我们将探索实时 AI 同声传译。", "Good morning everyone ...", "#778397")
    subtitle_card(draw, (74, 384, 752, 500), "stable · v1", "这个模型使用张力机制来判断哪些词更重要。", "The model uses a tension mechanism ...", BLUE)
    subtitle_card(draw, (74, 524, 752, 640), "final · v1", "术语表帮助系统保持技术术语一致。", "A small glossary keeps terms consistent.", GREEN)
    draw_side_notes(draw, scene.bullets)
    return img


def draw_correction(scene: Scene, index: int, progress: float) -> Image.Image:
    img, draw = base_slide(scene, index)
    subtitle_card(draw, (78, 238, 744, 370), "stable · v1", "这个模型使用张力机制来判断哪些词更重要。", "The model uses a tension mechanism ...", BLUE)
    draw.line((410, 402, 410, 468), fill="#c49513", width=5)
    draw.polygon([(410, 468), (394, 446), (426, 446)], fill="#c49513")
    draw_fit_text(draw, (120, 410, 700, 454), "后文出现 attention mechanism 后触发回溯修正", 25, 18, "#8b5d08", bold=True, align="center")
    if progress > 0.42:
        subtitle_card(draw, (78, 484, 744, 628), "corrected · v2", "这个模型使用注意力机制来判断哪些词更重要。", "The model uses a tension mechanism ...", "#c49513", "#fff9df")
    else:
        rounded(draw, (78, 484, 744, 628), "#ffffff", "#d7e1ec", 8)
        draw_fit_text(draw, (118, 528, 704, 580), "等待后续上下文...", 30, 22, MUTED, bold=True, align="center", valign="middle")
    draw_side_notes(draw, scene.bullets)
    return img


def draw_synced(scene: Scene, index: int, progress: float) -> Image.Image:
    img, draw = base_slide(scene, index)
    rounded(draw, (70, 234, 792, 622), "#111827", "#26364d", 8)
    draw_fit_text(draw, (112, 270, 340, 302), "AI TECH TALK", 20, 16, "#6ee7b7", bold=True)
    draw_fit_text(draw, (112, 318, 670, 366), "Real-time AI Interpretation", 38, 28, "#ffffff", bold=True)
    draw_fit_text(draw, (112, 374, 702, 410), "Original English audio · synchronized Chinese interpretation", 20, 15, "#bfd2e8", bold=True)
    for i, h in enumerate([28, 56, 40, 76, 50, 64, 34, 72]):
        x = 126 + i * 28
        draw.rounded_rectangle((x, 486 - h, x + 13, 486), radius=6, fill=GOLD)
    corrected = progress > 0.50
    rounded(draw, (112, 500, 750, 600), "#081320", "#40536d", 8)
    status = "已修正 · v2" if corrected else "稳定 · v1"
    zh = "这个模型使用注意力机制来判断哪些词更重要。" if corrected else "这个模型使用张力机制来判断哪些词更重要。"
    draw_fit_text(draw, (136, 514, 736, 538), status, 17, 13, "#9ee7ca" if corrected else "#c8d8ef", bold=True)
    draw_fit_text(draw, (136, 542, 736, 572), zh, 24, 18, "#ffffff", bold=True)
    draw_fit_text(draw, (136, 574, 736, 594), "The model uses a tension mechanism ...", 15, 12, "#dce8f5", bold=True)
    draw.rectangle((70, 640, 792, 660), fill="#dce8f5")
    draw.rectangle((70, 640, 70 + int(722 * progress), 660), fill=GREEN)
    draw_side_notes(draw, scene.bullets)
    return img


def draw_audit(scene: Scene, index: int) -> Image.Image:
    img, draw = base_slide(scene, index)
    items = [
        ("修正时间线", "触发原因、修正延迟、v1 -> v2"),
        ("版本轨迹", "每条字幕保留状态与译文变化"),
        ("导出总结", "Markdown / SRT / 会后总结"),
    ]
    y = 246
    for title, body in items:
        rounded(draw, (82, y, 742, y + 104), "#ffffff", LINE, 8)
        draw_fit_text(draw, (116, y + 18, 330, y + 48), title, 26, 20, GREEN, bold=True)
        draw_fit_text(draw, (116, y + 56, 704, y + 86), body, 23, 17, INK, bold=True)
        y += 130
    draw_side_notes(draw, scene.bullets)
    return img


def draw_quality(scene: Scene, index: int) -> Image.Image:
    img, draw = base_slide(scene, index)
    rounded(draw, (88, 234, 752, 598), NAVY, "#26364d", 8)
    checks = [
        "26 backend tests passed",
        "Frontend production build passed",
        "Single-service smoke passed",
        "README + demo video link ready",
        "Continuous PR history complete",
    ]
    y = 276
    for item in checks:
        draw.ellipse((130, y + 8, 154, y + 32), fill="#6ee7b7")
        draw_fit_text(draw, (174, y, 690, y + 42), item, 25, 18, "#eef6ff", bold=True, valign="middle")
        y += 58
    draw_side_notes(draw, scene.bullets)
    return img


def render_scene(scene: Scene, index: int, progress: float) -> Image.Image:
    if scene.kind == "cover":
        return draw_cover(scene, index)
    if scene.kind == "challenge":
        return draw_challenge(scene, index)
    if scene.kind == "architecture":
        return draw_architecture(scene, index)
    if scene.kind == "stream":
        return draw_stream(scene, index)
    if scene.kind == "correction":
        return draw_correction(scene, index, progress)
    if scene.kind == "synced":
        return draw_synced(scene, index, progress)
    if scene.kind == "audit":
        return draw_audit(scene, index)
    if scene.kind == "quality":
        return draw_quality(scene, index)
    raise ValueError(f"Unknown scene kind: {scene.kind}")


def convert_audio_to_wav(input_path: Path, wav_path: Path) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-ac",
            "1",
            "-ar",
            "22050",
            "-acodec",
            "pcm_s16le",
            str(wav_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def synthesize_edge_scene_audio(scene: Scene, index: int, wav_path: Path) -> Path:
    import asyncio

    import edge_tts

    mp3_path = SCENE_AUDIO_DIR / f"scene-{index:02d}.mp3"

    async def save_audio() -> None:
        communicate = edge_tts.Communicate(
            text=scene.narration,
            voice=TTS_VOICE,
            rate=TTS_RATE,
            pitch=TTS_PITCH,
            volume=TTS_VOLUME,
        )
        await communicate.save(str(mp3_path))

    asyncio.run(save_audio())
    convert_audio_to_wav(mp3_path, wav_path)
    return wav_path


def synthesize_sapi_scene_audio(scene: Scene, text_path: Path, wav_path: Path) -> Path:
    safe_text_path = str(text_path).replace("'", "''")
    safe_wav_path = str(wav_path).replace("'", "''")
    SCENE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ps = f"""
Add-Type -AssemblyName System.Speech
$text = Get-Content -LiteralPath '{safe_text_path}' -Raw -Encoding UTF8
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.SelectVoice('Microsoft Huihui Desktop')
$speaker.Rate = 1
$speaker.Volume = 100
$speaker.SetOutputToWaveFile('{safe_wav_path}')
$speaker.Speak($text)
$speaker.Dispose()
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        check=True,
        cwd=ROOT,
    )
    return wav_path


def synthesize_scene_audio(scene: Scene, index: int) -> Path:
    SCENE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    text_path = SCENE_AUDIO_DIR / f"scene-{index:02d}.txt"
    wav_path = SCENE_AUDIO_DIR / f"scene-{index:02d}.wav"
    text_path.write_text(scene.narration, encoding="utf-8")

    if TTS_PROVIDER in {"auto", "edge", "neural"}:
        try:
            print(f"Scene {index + 1}: Edge Neural TTS ({TTS_VOICE}, rate {TTS_RATE}, pitch {TTS_PITCH})")
            return synthesize_edge_scene_audio(scene, index, wav_path)
        except Exception as exc:
            if TTS_PROVIDER in {"edge", "neural"}:
                raise
            print(f"Scene {index + 1}: Edge Neural TTS unavailable ({exc}); falling back to Windows SAPI.")

    print(f"Scene {index + 1}: Windows SAPI fallback (Microsoft Huihui Desktop)")
    return synthesize_sapi_scene_audio(scene, text_path, wav_path)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def combine_wavs(paths: list[Path], output: Path) -> None:
    params = None
    silence_seconds = 0.35
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


def render_video(scene_durations: list[float]) -> None:
    writer = imageio.get_writer(
        str(VIDEO_ONLY),
        fps=FPS,
        codec="libx264",
        quality=9,
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
    durations = [wav_duration(path) + 0.35 for path in audio_paths]
    combine_wavs(audio_paths, NARRATION)
    render_video(durations)
    mux_audio()
    print(f"Generated demo video: {OUTPUT}")


if __name__ == "__main__":
    main()
