# Demo Material

Use self-written English text for the demo audio to avoid copyright risk and to keep the correction moment stable.

## Source Text

The current demo text is stored in:

```text
assets/demo/demo-script.en.txt
```

## Recommended Recording Flow

1. Use the text in `assets/demo/demo-script.en.txt`.
2. Generate or record an English audio file from that text.
3. Keep the audio file name simple, for example `demo-en.wav`.
4. Mention in the README or PR description that the demo audio is self-written/generated for this competition.
5. Avoid using TED, YouTube, course, or conference audio unless you have explicit permission.

## Offline WAV Generation

On Windows, generate a local WAV file with the system speech synthesizer:

```powershell
.\scripts\generate-demo-audio.ps1
```

Default output:

```text
assets/demo/demo-en.wav
```

This audio is generated from original text in this repository and is suitable for recording the demo video. If the final repository should stay lightweight, keep the script and text as the source of truth and regenerate the WAV locally when needed.

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
