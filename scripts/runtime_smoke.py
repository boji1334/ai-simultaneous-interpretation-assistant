import asyncio
import json
import sys
from typing import Any

import httpx
from websockets import connect


BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
WS_BASE = BASE_URL.replace("http://", "ws://").replace("https://", "wss://")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def wait_for_health() -> None:
    async with httpx.AsyncClient(timeout=2.0) as client:
        for _ in range(40):
            try:
                response = await client.get(f"{BASE_URL}/health")
                if response.status_code == 200 and response.json().get("status") == "ok":
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.25)
    raise TimeoutError("Backend health endpoint did not become ready.")


async def check_http_endpoints() -> None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        index = await client.get(BASE_URL)
        assert_true(index.status_code == 200, "Single-service index page failed.")
        assert_true("AI 同声传译助手" in index.text, "Index page did not include app title.")

        transcript = (await client.get(f"{BASE_URL}/api/demo/transcript")).json()
        segments = transcript["segments"]
        assert_true(len(segments) == 5, "Expected five final demo subtitle segments.")
        corrected = next(segment for segment in segments if segment["id"] == "seg-003")
        assert_true(corrected["status"] == "corrected", "Expected seg-003 to be corrected.")
        assert_true("注意力机制" in corrected["translatedText"], "Corrected subtitle missing target term.")

        diagnostics = (await client.get(f"{BASE_URL}/api/providers/diagnostics")).json()
        provider_items = diagnostics["diagnostics"]
        assert_true(len(provider_items) == 2, "Expected two provider diagnostics.")
        assert_true(all(item["ready"] for item in provider_items), "Default mock providers should be ready.")

        snapshot = (await client.get(f"{BASE_URL}/api/demo/snapshot")).json()
        assert_true(snapshot["metrics"]["correctionLatencyMs"] == 1480, "Correction latency metric missing.")
        assert_true(snapshot["corrections"][0]["segmentId"] == "seg-003", "Correction trace missing.")
        assert_true(
            any(revision["segmentId"] == "seg-003" and revision["version"] == 2 for revision in snapshot["revisions"]),
            "Subtitle revision history missing corrected version.",
        )
        assert_true(snapshot["summary"]["title"], "Summary missing from snapshot.")

        export_payload = (await client.get(f"{BASE_URL}/api/demo/export?format=srt")).json()
        assert_true("00:00:07,700 --> 00:00:11,500" in export_payload["content"], "SRT export invalid.")

        video_source = (await client.get(f"{BASE_URL}/api/video-demo/source")).json()
        assert_true(video_source["mediaType"] == "audio", "Synchronized demo source should be audio.")
        assert_true(video_source["mediaUrl"] == "/api/demo/audio", "Synchronized demo media URL invalid.")
        assert_true("Original competition demo text" in video_source["license"], "Demo source license missing.")

        demo_audio = await client.get(f"{BASE_URL}/api/demo/audio")
        assert_true(demo_audio.status_code == 200, "Demo audio endpoint failed.")
        assert_true(demo_audio.headers["content-type"].startswith("audio/wav"), "Demo audio content type invalid.")

        video_snapshot = (await client.get(f"{BASE_URL}/api/video-demo/snapshot")).json()
        assert_true(len(video_snapshot["segments"]) == 5, "Synchronized demo should expose five timed segments.")
        assert_true(video_snapshot["segments"][-1]["endTime"] >= 30, "Synchronized demo subtitles stop before audio end.")
        video_corrected = next(segment for segment in video_snapshot["segments"] if segment["id"] == "video-003")
        assert_true(video_corrected["status"] == "corrected", "Video demo did not expose corrected segment.")
        assert_true("注意力机制" in video_corrected["translatedText"], "Video demo correction missing target term.")


async def check_demo_websocket() -> None:
    events: list[dict[str, Any]] = []
    async with connect(f"{WS_BASE}/ws/demo?speed=4") as websocket:
        while True:
            event = json.loads(await websocket.recv())
            events.append(event)
            if event["type"] == "done":
                break

    assert_true(any(event["type"] == "metric" for event in events), "Demo stream missing metrics.")
    assert_true(
        any(event.get("segment", {}).get("status") == "corrected" for event in events),
        "Demo stream missing corrected subtitle.",
    )
    assert_true(any(event["type"] == "correction" for event in events), "Demo stream missing correction trace.")


async def check_video_demo_websocket() -> None:
    events: list[dict[str, Any]] = []
    async with connect(f"{WS_BASE}/ws/video-demo?speed=4") as websocket:
        while True:
            event = json.loads(await websocket.recv())
            events.append(event)
            if event["type"] == "done":
                break

    assert_true(any(event["type"] == "metric" for event in events), "Video demo stream missing metrics.")
    assert_true(
        any(event.get("segment", {}).get("id") == "video-003" and event.get("segment", {}).get("status") == "corrected" for event in events),
        "Video demo stream missing corrected attention subtitle.",
    )
    assert_true(any(event["type"] == "correction" for event in events), "Video demo stream missing correction trace.")


async def check_audio_stream_websocket() -> None:
    events: list[dict[str, Any]] = []
    async with connect(f"{WS_BASE}/ws/audio-stream") as websocket:
        for _ in range(8):
            event = json.loads(await websocket.recv())
            events.append(event)
            await websocket.send(b"audio-chunk")

            if any(item.get("segment", {}).get("status") == "corrected" for item in events):
                break

        await websocket.send("stop")
        while events[-1]["type"] != "done":
            events.append(json.loads(await websocket.recv()))

    assert_true([event["type"] for event in events[:2]] == ["session", "glossary"], "Audio stream setup invalid.")
    assert_true(any(event["type"] == "segment" for event in events), "Audio stream missing subtitle segment.")
    assert_true(
        any(event.get("segment", {}).get("status") == "corrected" for event in events),
        "Audio stream missing corrected subtitle.",
    )
    assert_true(any(event["type"] == "correction" for event in events), "Audio stream missing correction trace.")
    assert_true(events[-1]["type"] == "done", "Audio stream did not finish cleanly.")


async def main() -> None:
    await wait_for_health()
    await check_http_endpoints()
    await check_demo_websocket()
    await check_video_demo_websocket()
    await check_audio_stream_websocket()
    print("Runtime smoke checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
