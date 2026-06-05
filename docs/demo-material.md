# Demo Material

Use self-written English text for the demo audio to avoid copyright risk and to keep the correction moment stable.

## Source Text

The current demo text is stored in:

```text
assets/demo/demo-script.en.txt
```

## Recommended Recording Flow

1. Use the text in `assets/demo/demo-script.en.txt`.
2. Use the committed `assets/demo/demo-en.wav` for the main synchronized demo.
3. Regenerate the WAV from the text if you need to change narration timing.
4. Mention in the README or PR description that the demo audio is self-written/generated for this competition.
5. Avoid using TED, YouTube, course, or conference audio unless you have explicit permission.

## External Video Policy

The competition topic explicitly mentions speeches, technical talks, international conferences, and online courses. The main demo uses self-written generated audio because the audio, English source text, and Chinese interpretation can be synchronized exactly. External public video remains useful as secondary material, but it should not be the primary demo unless its transcript timing is verified.

Use only material that is legally safe for a public demo:

- Prefer self-recorded video or generated video from the original script.
- Prefer public-domain or Creative Commons videos with visible license pages.
- Keep attribution in the README, PR description, or demo video narration.
- Do not use TED, YouTube, paid course, or conference recordings unless permission is explicit.

Recommended public sample:

```text
Title: Welcome (6.002x-1).webm
Source: Wikimedia Commons
License: Creative Commons Attribution-Share Alike 4.0
Scenario: MITx online course welcome video
```

This sample is appropriate for demonstrating the "watching an English online course with Chinese interpretation subtitles" workflow after its timing has been verified. The app keeps the default self-written synchronized demo because it is deterministic and designed to highlight the required automatic correction capability.

To download the public sample for local recording:

```powershell
.\scripts\download-demo-video.ps1
```

Default output:

```text
assets/demo/external-course-demo.webm
```

The downloaded video is ignored by Git. Keep the script, source page, license, and attribution in the repository as the reproducible trail.

## Offline WAV Generation

On Windows, generate a local WAV file with the system speech synthesizer:

```powershell
.\scripts\generate-demo-audio.ps1
```

Default output:

```text
assets/demo/demo-en.wav
```

This audio is generated from original text in this repository and is suitable for recording the demo video. The repository currently includes the WAV so judges can run the synchronized demo immediately after cloning.

## Narrated Demo Video Generation

The repository includes a script that generates a narrated MP4 from the demo storyboard:

```powershell
python -m pip install imageio-ffmpeg
python scripts\generate-demo-video.py
```

Default output:

```text
assets/demo/final-demo.mp4
```

The generated MP4 is ignored by Git and can be uploaded to a public release, Bilibili, or cloud drive. The current submitted video is hosted here:

```text
https://github.com/boji1334/ai-simultaneous-interpretation-assistant/releases/download/demo-video-v1/final-demo.mp4
```

## Correction Moment

The source intentionally contains this pair:

```text
The model uses a tension mechanism to decide which words matter.
But after the next words arrive, it becomes clear that the speaker means attention mechanism.
```

This lets the system first show a plausible wrong translation and then correct it after the later context arrives:

```text
张力机制 -> 注意力机制
```
