from collections import deque

from app.models import DemoEvent
from app.services.demo_stream import build_demo_events


class AudioStreamEventPump:
    """Turn incoming audio chunks into subtitle events for the stream protocol."""

    def __init__(self, events_per_chunk: int = 2) -> None:
        events = build_demo_events()
        self.events_per_chunk = events_per_chunk
        self._started = False
        self._done_sent = False
        self._setup_events = deque(event for event in events if event.type in {"session", "glossary"})
        self._subtitle_events = deque(event for event in events if event.type not in {"session", "glossary", "done"})
        self._done_event = next(event for event in events if event.type == "done")

    def start(self) -> list[DemoEvent]:
        if self._started:
            return []
        self._started = True
        return [self._without_delay(event) for event in self._drain_setup()]

    def push_audio_chunk(self, audio: bytes) -> list[DemoEvent]:
        if not audio or self._done_sent:
            return []

        events: list[DemoEvent] = []
        for _ in range(self.events_per_chunk):
            if not self._subtitle_events:
                break
            events.append(self._without_delay(self._subtitle_events.popleft()))
        return events

    def finish(self) -> list[DemoEvent]:
        if self._done_sent:
            return []

        self._done_sent = True
        remaining = [self._without_delay(event) for event in self._subtitle_events]
        self._subtitle_events.clear()
        return [*remaining, self._without_delay(self._done_event)]

    def _drain_setup(self) -> list[DemoEvent]:
        events = list(self._setup_events)
        self._setup_events.clear()
        return events

    @staticmethod
    def _without_delay(event: DemoEvent) -> DemoEvent:
        return event.model_copy(update={"delay_ms": 0})
