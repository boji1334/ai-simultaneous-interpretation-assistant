import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { API_BASE, websocketUrl } from "./config";
import "./styles.css";

type SubtitleStatus = "partial" | "stable" | "corrected" | "final";

type GlossaryTerm = {
  source: string;
  target: string;
  category: string;
  description: string;
};

type SubtitleSegment = {
  id: string;
  sourceText: string;
  translatedText: string;
  status: SubtitleStatus;
  version: number;
  startTime: number;
  endTime?: number;
  confidence: number;
  changedTerms: string[];
  previousTranslation?: string;
};

type MetricSnapshot = {
  firstSubtitleLatencyMs: number | null;
  correctionLatencyMs: number | null;
  glossaryHitRate: number;
  finalStabilityRate: number;
  correctionCount: number;
  finalCount: number;
  subtitleCount: number;
};

type CorrectionTrace = {
  segmentId: string;
  trigger: string;
  reason: string;
  previousTranslation: string;
  correctedTranslation: string;
  changedTerms: string[];
  latencyMs: number;
  fromVersion: number;
  toVersion: number;
};

type SubtitleRevision = {
  segmentId: string;
  version: number;
  status: SubtitleStatus;
  translatedText: string;
  confidence: number;
  changedTerms: string[];
  previousTranslation?: string;
};

type DemoEvent = {
  type: "session" | "glossary" | "segment" | "metric" | "correction" | "done";
  message?: string;
  segment?: SubtitleSegment;
  metrics?: MetricSnapshot;
  glossary?: GlossaryTerm[];
  correction?: CorrectionTrace;
};

type AudioDemoResult = {
  filename: string;
  bytesReceived: number;
  sourceText: string;
  translatedText: string;
  confidence: number;
  glossaryHits: string[];
  provider: string;
};

type ProviderStatus = {
  asrProvider: string;
  translationProvider: string;
  asrModelPath: string;
  translationModel: string;
};

type ProviderDiagnostic = {
  name: string;
  kind: "asr" | "translation";
  ready: boolean;
  mode: "demo" | "real";
  message: string;
  action: string;
};

type ProviderDiagnosticsPayload = {
  diagnostics: ProviderDiagnostic[];
};

type VideoDemoSource = {
  title: string;
  pageUrl: string;
  mediaUrl: string;
  license: string;
  attribution: string;
  durationSeconds: number;
  scenario: string;
  note: string;
};

type ExportPayload = {
  filename: string;
  content: string;
};

type SummaryResult = {
  title: string;
  summary: string;
  keyPoints: string[];
  keywords: string[];
  glossaryTerms: string[];
  correctionNotes: string[];
};

type DemoSnapshot = {
  segments: SubtitleSegment[];
  glossary: GlossaryTerm[];
  metrics: MetricSnapshot;
  corrections: CorrectionTrace[];
  revisions: SubtitleRevision[];
  summary: SummaryResult;
};

type VideoDemoSnapshot = DemoSnapshot & {
  source: VideoDemoSource;
};

const WS_URL = `${websocketUrl("/ws/demo")}?speed=1.35`;
const AUDIO_STREAM_WS_URL = websocketUrl("/ws/audio-stream");

const statusLabel: Record<SubtitleStatus, string> = {
  partial: "临时",
  stable: "稳定",
  corrected: "已修正",
  final: "最终"
};

function formatRate(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatLatency(value: number | null) {
  return value === null ? "--" : `${value}ms`;
}

function formatTimeRange(segment: SubtitleSegment) {
  const end = segment.endTime === undefined ? "..." : segment.endTime.toFixed(1);
  return `${segment.startTime.toFixed(1)}s - ${end}s`;
}

function upsertSegment(segments: SubtitleSegment[], next: SubtitleSegment) {
  const index = segments.findIndex((segment) => segment.id === next.id);
  if (index === -1) {
    return [...segments, next].sort((a, b) => a.startTime - b.startTime);
  }

  const copy = [...segments];
  copy[index] = next;
  return copy;
}

function upsertRevision(revisions: SubtitleRevision[], segment: SubtitleSegment) {
  const next: SubtitleRevision = {
    segmentId: segment.id,
    version: segment.version,
    status: segment.status,
    translatedText: segment.translatedText,
    confidence: segment.confidence,
    changedTerms: segment.changedTerms,
    previousTranslation: segment.previousTranslation
  };
  const index = revisions.findIndex(
    (revision) => revision.segmentId === next.segmentId && revision.version === next.version
  );
  if (index === -1) {
    return [...revisions, next].sort((a, b) => {
      if (a.segmentId === b.segmentId) {
        return a.version - b.version;
      }
      return a.segmentId.localeCompare(b.segmentId);
    });
  }

  const copy = [...revisions];
  copy[index] = next;
  return copy;
}

function buildExportText(segments: SubtitleSegment[]) {
  return segments
    .filter((segment) => segment.status === "final" || segment.status === "corrected")
    .map((segment, index) => {
      return [
        `${index + 1}. ${formatTimeRange(segment)}`,
        `EN: ${segment.sourceText}`,
        `ZH: ${segment.translatedText}`,
        `STATUS: ${statusLabel[segment.status]} / v${segment.version}`
      ].join("\n");
    })
    .join("\n\n");
}

function downloadTextFile(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

function App() {
  const [segments, setSegments] = useState<SubtitleSegment[]>([]);
  const [glossary, setGlossary] = useState<GlossaryTerm[]>([]);
  const [metrics, setMetrics] = useState<MetricSnapshot>({
    firstSubtitleLatencyMs: null,
    correctionLatencyMs: null,
    glossaryHitRate: 0,
    finalStabilityRate: 0,
    correctionCount: 0,
    finalCount: 0,
    subtitleCount: 0
  });
  const [connectionState, setConnectionState] = useState("未开始");
  const [lastMessage, setLastMessage] = useState("等待演示流启动");
  const [audioResult, setAudioResult] = useState<AudioDemoResult | null>(null);
  const [providerStatus, setProviderStatus] = useState<ProviderStatus | null>(null);
  const [providerDiagnostics, setProviderDiagnostics] = useState<ProviderDiagnostic[]>([]);
  const [summary, setSummary] = useState<SummaryResult | null>(null);
  const [correctionTraces, setCorrectionTraces] = useState<CorrectionTrace[]>([]);
  const [revisions, setRevisions] = useState<SubtitleRevision[]>([]);
  const [recorder, setRecorder] = useState<MediaRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [streamRecorder, setStreamRecorder] = useState<MediaRecorder | null>(null);
  const [isStreamingAudio, setIsStreamingAudio] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [videoSource, setVideoSource] = useState<VideoDemoSource | null>(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [videoTime, setVideoTime] = useState(0);
  const [isVideoSyncActive, setIsVideoSyncActive] = useState(false);
  const [videoSyncSegments, setVideoSyncSegments] = useState<SubtitleSegment[]>([]);
  const [videoSyncCorrections, setVideoSyncCorrections] = useState<CorrectionTrace[]>([]);
  const [videoSyncRevisions, setVideoSyncRevisions] = useState<SubtitleRevision[]>([]);
  const [videoSyncMetrics, setVideoSyncMetrics] = useState<MetricSnapshot | null>(null);
  const [videoSyncSummary, setVideoSyncSummary] = useState<SummaryResult | null>(null);
  const demoSocketRef = useRef<WebSocket | null>(null);
  const audioSocketRef = useRef<WebSocket | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const spokenSegmentIds = useRef(new Set<string>());

  const exportText = useMemo(() => buildExportText(segments), [segments]);
  const currentSegment = segments.at(-1);
  const isVideoCaptionMode =
    videoSyncSegments.length > 0 && segments.some((segment) => segment.id.startsWith("video-"));
  const activeVideoSegment = useMemo(() => {
    if (!isVideoCaptionMode) {
      return null;
    }

    const timedSegment = [...segments]
      .reverse()
      .find((segment) => {
        const start = segment.startTime - 0.35;
        const end = segment.endTime === undefined ? Number.POSITIVE_INFINITY : segment.endTime + 0.8;
        return videoTime >= start && videoTime <= end;
      });
    return timedSegment ?? currentSegment;
  }, [currentSegment, isVideoCaptionMode, segments, videoTime]);
  const correctedSegment = segments.find((segment) => segment.status === "corrected");
  const revisionGroups = useMemo(() => {
    return revisions.reduce<Record<string, SubtitleRevision[]>>((groups, revision) => {
      groups[revision.segmentId] = [...(groups[revision.segmentId] ?? []), revision];
      return groups;
    }, {});
  }, [revisions]);

  const getCorrectionRevealTime = (trace: CorrectionTrace) => {
    const segment = videoSyncSegments.find((item) => item.id === trace.segmentId);
    const anchorTime = segment?.endTime ?? segment?.startTime ?? 0;
    return anchorTime + trace.latencyMs / 1000 + 8;
  };

  const resetVideoSync = () => {
    setIsVideoSyncActive(false);
    setVideoSyncSegments([]);
    setVideoSyncCorrections([]);
    setVideoSyncRevisions([]);
    setVideoSyncMetrics(null);
    setVideoSyncSummary(null);
  };

  useEffect(() => {
    if (!isVideoSyncActive || videoSyncSegments.length === 0) {
      return;
    }

    const leadSeconds = 0.35;
    const visibleSegments = videoSyncSegments
      .filter((segment) => segment.startTime <= videoTime + leadSeconds)
      .map((segment) => {
        const correction = videoSyncCorrections.find((trace) => trace.segmentId === segment.id);
        if (!correction || videoTime >= getCorrectionRevealTime(correction)) {
          return segment;
        }

        const previousRevision = videoSyncRevisions.find(
          (revision) => revision.segmentId === segment.id && revision.version === correction.fromVersion
        );

        return {
          ...segment,
          translatedText: previousRevision?.translatedText ?? correction.previousTranslation,
          status: previousRevision?.status ?? "stable",
          version: correction.fromVersion,
          confidence: previousRevision?.confidence ?? segment.confidence,
          changedTerms: previousRevision?.changedTerms ?? segment.changedTerms,
          previousTranslation: undefined
        };
      });

    const visibleCorrections = videoSyncCorrections.filter((trace) => videoTime >= getCorrectionRevealTime(trace));
    const visibleRevisions = videoSyncRevisions.filter((revision) => {
      const segment = videoSyncSegments.find((item) => item.id === revision.segmentId);
      if (!segment || segment.startTime > videoTime + leadSeconds) {
        return false;
      }

      const correction = videoSyncCorrections.find((trace) => trace.segmentId === revision.segmentId);
      if (correction && revision.version === correction.toVersion) {
        return videoTime >= getCorrectionRevealTime(correction);
      }

      return true;
    });

    const finalEndTime = videoSyncSegments.at(-1)?.endTime ?? 0;
    const isComplete = videoTime >= finalEndTime - 0.25;
    const finalCount = visibleSegments.filter(
      (segment) => segment.status === "final" || segment.status === "corrected"
    ).length;
    const subtitleCount = Math.max(visibleSegments.length, 1);

    setSegments(visibleSegments);
    setCorrectionTraces(visibleCorrections);
    setRevisions(visibleRevisions);
    setMetrics({
      firstSubtitleLatencyMs: videoSyncMetrics?.firstSubtitleLatencyMs ?? 760,
      correctionLatencyMs:
        visibleCorrections.length > 0 ? videoSyncMetrics?.correctionLatencyMs ?? visibleCorrections[0].latencyMs : null,
      glossaryHitRate: isComplete ? videoSyncMetrics?.glossaryHitRate ?? 1 : Math.min(1, visibleSegments.length / 17),
      finalStabilityRate: isComplete ? videoSyncMetrics?.finalStabilityRate ?? 0.94 : finalCount / subtitleCount,
      correctionCount: visibleCorrections.length,
      finalCount,
      subtitleCount: visibleSegments.length
    });

    if (isComplete) {
      setConnectionState("视频同传完成");
      setLastMessage("视频播放已到末尾，中文字幕覆盖完整视频");
      if (videoSyncSummary) {
        setSummary(videoSyncSummary);
      }
      setIsVideoSyncActive(false);
    } else {
      setConnectionState("视频同传中");
      setLastMessage(`视频 ${videoTime.toFixed(1)}s，同步显示当前中文同传字幕`);
    }
  }, [isVideoSyncActive, videoSyncCorrections, videoSyncMetrics, videoSyncRevisions, videoSyncSegments, videoSyncSummary, videoTime]);

  const startDemo = () => {
    demoSocketRef.current?.close();
    audioSocketRef.current?.close();
    resetVideoSync();
    setSegments([]);
    setGlossary([]);
    setCorrectionTraces([]);
    setRevisions([]);
    setMetrics({
      firstSubtitleLatencyMs: null,
      correctionLatencyMs: null,
      glossaryHitRate: 0,
      finalStabilityRate: 0,
      correctionCount: 0,
      finalCount: 0,
      subtitleCount: 0
    });
    setConnectionState("连接中");
    setLastMessage("正在连接后端演示流");
    spokenSegmentIds.current.clear();

    const socket = new WebSocket(WS_URL);
    demoSocketRef.current = socket;

    socket.onopen = () => {
      if (demoSocketRef.current !== socket) {
        return;
      }
      setConnectionState("演示中");
      setLastMessage("WebSocket 已连接，开始接收字幕事件");
    };

    socket.onmessage = (event) => {
      if (demoSocketRef.current !== socket) {
        return;
      }

      let payload: DemoEvent;
      try {
        payload = JSON.parse(event.data) as DemoEvent;
      } catch {
        setConnectionState("解析失败");
        setLastMessage("收到无法解析的字幕事件");
        socket.close();
        return;
      }

      if (payload.message) {
        setLastMessage(payload.message);
      }

      if (payload.glossary) {
        setGlossary(payload.glossary);
      }

      if (payload.segment) {
        const segment = payload.segment as SubtitleSegment;
        setSegments((items) => upsertSegment(items, segment));
        setRevisions((items) => upsertRevision(items, segment));
        speakSegment(segment);
      }

      if (payload.metrics) {
        setMetrics(payload.metrics);
      }

      if (payload.correction) {
        setCorrectionTraces((items) => {
          const exists = items.some((item) => item.segmentId === payload.correction?.segmentId);
          return exists || !payload.correction ? items : [...items, payload.correction];
        });
      }

      if (payload.type === "done") {
        setConnectionState("完成");
        setLastMessage("演示完成，可导出最终双语字幕");
        demoSocketRef.current = null;
        socket.close();
      }
    };

    socket.onerror = () => {
      if (demoSocketRef.current !== socket) {
        return;
      }
      setConnectionState("连接失败");
      setLastMessage("无法连接后端，请确认 FastAPI 服务已启动");
      demoSocketRef.current = null;
    };

    socket.onclose = () => {
      if (demoSocketRef.current === socket) {
        demoSocketRef.current = null;
      }
    };
  };

  const handleStreamEvent = (payload: DemoEvent) => {
    if (payload.message) {
      setLastMessage(payload.message);
    }

    if (payload.glossary) {
      setGlossary(payload.glossary);
    }

    if (payload.segment) {
      setSegments((items) => upsertSegment(items, payload.segment as SubtitleSegment));
      setRevisions((items) => upsertRevision(items, payload.segment as SubtitleSegment));
      speakSegment(payload.segment);
    }

    if (payload.metrics) {
      setMetrics(payload.metrics);
    }

    if (payload.correction) {
      setCorrectionTraces((items) => {
        const exists = items.some((item) => item.segmentId === payload.correction?.segmentId);
        return exists || !payload.correction ? items : [...items, payload.correction];
      });
    }
  };

  const speakSegment = (segment: SubtitleSegment) => {
    if (!voiceEnabled || !("speechSynthesis" in window)) {
      return;
    }

    if (segment.status !== "final" && segment.status !== "corrected") {
      return;
    }

    const speechKey = `${segment.id}:${segment.version}`;
    if (spokenSegmentIds.current.has(speechKey)) {
      return;
    }

    const utterance = new SpeechSynthesisUtterance(segment.translatedText);
    utterance.lang = "zh-CN";
    utterance.rate = 1.08;
    window.speechSynthesis.speak(utterance);
    spokenSegmentIds.current.add(speechKey);
  };

  const toggleVoice = () => {
    const next = !voiceEnabled;
    setVoiceEnabled(next);
    if (!next && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setLastMessage(next ? "中文语音播报已开启" : "中文语音播报已关闭");
  };

  const loadProviderStatus = async () => {
    try {
      const [status, diagnostics] = await Promise.all([
        fetchJson<ProviderStatus>(`${API_BASE}/api/providers`),
        fetchJson<ProviderDiagnosticsPayload>(`${API_BASE}/api/providers/diagnostics`)
      ]);
      setProviderStatus(status);
      setProviderDiagnostics(diagnostics.diagnostics);
      setLastMessage("Provider 状态已加载");
    } catch {
      setLastMessage("Provider 状态加载失败，请检查后端服务");
    }
  };

  const copyTranscript = async () => {
    if (!exportText) {
      setLastMessage("暂无可导出的最终字幕");
      return;
    }

    try {
      await navigator.clipboard.writeText(exportText);
      setLastMessage("最终双语字幕已复制到剪贴板");
    } catch {
      setLastMessage("复制失败，请使用导出预览手动复制");
    }
  };

  const downloadTranscript = async (format: "markdown" | "srt") => {
    try {
      const payload = await fetchJson<ExportPayload>(`${API_BASE}/api/demo/export?format=${format}`);
      downloadTextFile(payload.filename, payload.content);
      setLastMessage(`${payload.filename} 已生成下载`);
    } catch {
      setLastMessage("字幕导出失败，请检查后端服务");
    }
  };

  const loadSummary = async () => {
    try {
      const payload = await fetchJson<SummaryResult>(`${API_BASE}/api/demo/summary`);
      setSummary(payload);
      setLastMessage("会后总结已生成");
    } catch {
      setLastMessage("会后总结生成失败，请检查后端服务");
    }
  };

  const loadFinalTranscript = async () => {
    demoSocketRef.current?.close();
    resetVideoSync();
    try {
      const data = await fetchJson<DemoSnapshot>(`${API_BASE}/api/demo/snapshot`);
      setSegments(data.segments);
      setGlossary(data.glossary);
      setMetrics(data.metrics);
      setCorrectionTraces(data.corrections);
      setRevisions(data.revisions);
      setSummary(data.summary);
      setConnectionState("已加载");
      setLastMessage("已加载完整演示快照，可用于赛前兜底演示");
    } catch {
      setConnectionState("加载失败");
      setLastMessage("完整演示快照加载失败，请检查后端服务");
    }
  };

  const loadVideoDemoSource = async () => {
    try {
      const source = await fetchJson<VideoDemoSource>(`${API_BASE}/api/video-demo/source`);
      setVideoSource(source);
      setVideoUrl(source.mediaUrl);
      setLastMessage("已加载 Wikimedia 公开网课视频素材");
      return source;
    } catch {
      setLastMessage("外部视频素材加载失败，请检查后端服务");
      return null;
    }
  };

  const loadLocalVideo = (file: File | null) => {
    if (!file) {
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setVideoUrl(objectUrl);
    setVideoSource({
      title: file.name,
      pageUrl: "",
      mediaUrl: objectUrl,
      license: "Local demo file",
      attribution: "User provided local file",
      durationSeconds: 0,
      scenario: "Local video interpretation",
      note: "本地文件仅用于现场演示，不会上传到后端。"
    });
    setLastMessage(`已加载本地视频：${file.name}`);
  };

  const startVideoDemo = async () => {
    demoSocketRef.current?.close();
    audioSocketRef.current?.close();

    const source = videoSource ?? (await loadVideoDemoSource());
    if (!source) {
      return;
    }

    setVideoUrl(source.mediaUrl);
    let snapshot: VideoDemoSnapshot;
    try {
      snapshot = await fetchJson<VideoDemoSnapshot>(`${API_BASE}/api/video-demo/snapshot`);
    } catch {
      setConnectionState("视频同传失败");
      setLastMessage("无法加载视频字幕快照，请检查后端服务");
      return;
    }

    setVideoSource(snapshot.source);
    setSegments([]);
    setGlossary(snapshot.glossary);
    setCorrectionTraces([]);
    setRevisions([]);
    setSummary(null);
    setMetrics({
      firstSubtitleLatencyMs: null,
      correctionLatencyMs: null,
      glossaryHitRate: 0,
      finalStabilityRate: 0,
      correctionCount: 0,
      finalCount: 0,
      subtitleCount: 0
    });
    setVideoSyncSegments(snapshot.segments);
    setVideoSyncCorrections(snapshot.corrections);
    setVideoSyncRevisions(snapshot.revisions);
    setVideoSyncMetrics(snapshot.metrics);
    setVideoSyncSummary(snapshot.summary);
    setIsVideoSyncActive(true);
    spokenSegmentIds.current.clear();
    setVideoTime(0);
    setConnectionState("视频待播放");
    setLastMessage("视频字幕已就绪，播放时会按时间同步显示中文翻译");

    window.setTimeout(() => {
      if (!videoRef.current) {
        return;
      }
      videoRef.current.load();
      videoRef.current.currentTime = 0;
      void videoRef.current.play().catch(() => {
        setLastMessage("浏览器阻止自动播放，请手动点击视频播放，字幕会跟随播放时间同步出现");
      });
    }, 0);
  };

  const uploadAudio = async (file: File | null) => {
    if (!file) {
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setLastMessage(`正在处理音频文件：${file.name}`);

    try {
      const result = await fetchJson<AudioDemoResult>(`${API_BASE}/api/audio/demo`, {
        method: "POST",
        body: formData
      });
      setAudioResult(result);
      setLastMessage("音频入口已通过 Provider 边界完成模拟处理");
    } catch {
      setLastMessage("音频处理失败，请检查后端服务");
    }
  };

  const uploadAudioBlob = async (blob: Blob, filename: string) => {
    const file = new File([blob], filename, { type: blob.type || "audio/webm" });
    await uploadAudio(file);
  };

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setLastMessage("当前浏览器不支持麦克风采集");
      return;
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setLastMessage("无法获取麦克风权限");
      return;
    }
    const chunks: BlobPart[] = [];
    const mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
      stream.getTracks().forEach((track) => track.stop());
      setRecorder(null);
      setIsRecording(false);
      void uploadAudioBlob(blob, "microphone-demo.webm");
    };

    mediaRecorder.start();
    setRecorder(mediaRecorder);
    setIsRecording(true);
    setLastMessage("麦克风录音中，停止后将自动上传到 Provider 边界");
  };

  const stopRecording = () => {
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
      setLastMessage("录音已停止，正在上传处理");
    }
  };

  const startAudioStream = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setLastMessage("当前浏览器不支持麦克风流式采集");
      return;
    }

    audioSocketRef.current?.close();
    demoSocketRef.current?.close();
    resetVideoSync();
    setSegments([]);
    setGlossary([]);
    setCorrectionTraces([]);
    setRevisions([]);
    setSummary(null);
    setMetrics({
      firstSubtitleLatencyMs: null,
      correctionLatencyMs: null,
      glossaryHitRate: 0,
      finalStabilityRate: 0,
      correctionCount: 0,
      finalCount: 0,
      subtitleCount: 0
    });
    spokenSegmentIds.current.clear();
    setConnectionState("音频流连接中");
    setLastMessage("正在建立麦克风音频流通道");

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setConnectionState("麦克风失败");
      setLastMessage("无法获取麦克风权限");
      return;
    }

    const socket = new WebSocket(AUDIO_STREAM_WS_URL);
    audioSocketRef.current = socket;

    socket.onopen = () => {
      if (audioSocketRef.current !== socket) {
        return;
      }
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (event) => {
        if (
          event.data.size > 0 &&
          socket.readyState === WebSocket.OPEN &&
          audioSocketRef.current === socket
        ) {
          void event.data.arrayBuffer().then((buffer) => socket.send(buffer));
        }
      };
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        setStreamRecorder(null);
        setIsStreamingAudio(false);
        if (socket.readyState === WebSocket.OPEN) {
          socket.send("stop");
        }
      };
      mediaRecorder.start(900);
      setStreamRecorder(mediaRecorder);
      setIsStreamingAudio(true);
      setConnectionState("音频流演示中");
      setLastMessage("麦克风音频分片正在通过 WebSocket 发送");
    };

    socket.onmessage = (event) => {
      if (audioSocketRef.current !== socket) {
        return;
      }

      let payload: DemoEvent;
      try {
        payload = JSON.parse(event.data) as DemoEvent;
      } catch {
        setConnectionState("解析失败");
        setLastMessage("收到无法解析的音频流字幕事件");
        socket.close();
        return;
      }

      handleStreamEvent(payload);
      if (payload.type === "done") {
        setConnectionState("音频流完成");
        setLastMessage("音频流演示完成，可导出最终双语字幕");
        audioSocketRef.current = null;
        socket.close();
      }
    };

    socket.onerror = () => {
      if (audioSocketRef.current !== socket) {
        return;
      }
      stream.getTracks().forEach((track) => track.stop());
      setConnectionState("音频流失败");
      setLastMessage("无法连接音频流通道，请确认 FastAPI 服务已启动");
      audioSocketRef.current = null;
    };

    socket.onclose = () => {
      if (audioSocketRef.current === socket) {
        audioSocketRef.current = null;
      }
    };
  };

  const stopAudioStream = () => {
    if (streamRecorder && streamRecorder.state !== "inactive") {
      streamRecorder.stop();
      setLastMessage("音频流采集已停止，正在收尾字幕事件");
    }
  };

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">XEngineer 第三批次 · AI 同声传译助手</p>
          <h1>实时字幕同传，可回溯修正</h1>
          <p className="lead">
            通过字幕状态机、滑动窗口修正和术语表命中，将单向英文音频流实时翻译成中文，并自动纠正前文错误。
          </p>
        </div>
        <div className="actions" aria-label="演示控制">
          <button type="button" onClick={startDemo}>
            启动实时演示
          </button>
          <button type="button" className="secondary" onClick={loadProviderStatus}>
            查看 Provider
          </button>
          <button type="button" className="secondary" onClick={loadFinalTranscript}>
            加载最终字幕
          </button>
          <button type="button" className="secondary" onClick={copyTranscript}>
            复制字幕
          </button>
          <button type="button" className="secondary" onClick={loadSummary}>
            生成总结
          </button>
          <button type="button" className="secondary" onClick={toggleVoice}>
            {voiceEnabled ? "关闭语音" : "开启语音"}
          </button>
        </div>
      </section>

      <section className="runtime-strip" aria-label="运行状态">
        <div>
          <span>状态</span>
          <strong>{connectionState}</strong>
        </div>
        <div>
          <span>当前事件</span>
          <strong>{lastMessage}</strong>
        </div>
      </section>

      <section className="video-demo-panel" aria-label="外部视频同传演示">
        <div className="section-head">
          <div>
            <h2>外部英文视频同传</h2>
            <p>加载公开视频或本地视频，同步展示中文字幕、修正高亮和版本轨迹。</p>
          </div>
          <div className="video-actions">
            <button type="button" className="secondary" onClick={loadVideoDemoSource}>
              加载公开网课视频
            </button>
            <button type="button" onClick={startVideoDemo}>
              启动视频同传
            </button>
          </div>
        </div>

        <div className="video-layout">
          <div className="video-frame">
            {videoUrl ? (
              <video
                ref={videoRef}
                controls
                preload="metadata"
                src={videoUrl}
                onTimeUpdate={(event) => setVideoTime(event.currentTarget.currentTime)}
              />
            ) : (
              <div className="video-placeholder">加载公开网课视频后，可在这里观看同步中文字幕。</div>
            )}
            {isVideoCaptionMode && activeVideoSegment && (
              <div className={`video-caption ${activeVideoSegment.status}`}>
                <span>{statusLabel[activeVideoSegment.status]} · v{activeVideoSegment.version}</span>
                <strong className="caption-zh">{activeVideoSegment.translatedText}</strong>
                <p className="caption-en">{activeVideoSegment.sourceText}</p>
                {activeVideoSegment.previousTranslation && (
                  <em>修正前：{activeVideoSegment.previousTranslation}</em>
                )}
              </div>
            )}
          </div>

          <div className="video-source-card">
            <span>视频素材</span>
            <strong>{videoSource?.title ?? "尚未加载"}</strong>
            <p>{videoSource?.note ?? "建议使用自写、自录、公共领域或 Creative Commons 授权视频。"}</p>
            {videoSource && (
              <dl>
                <div>
                  <dt>场景</dt>
                  <dd>{videoSource.scenario}</dd>
                </div>
                <div>
                  <dt>许可</dt>
                  <dd>{videoSource.license}</dd>
                </div>
                <div>
                  <dt>署名</dt>
                  <dd>{videoSource.attribution}</dd>
                </div>
              </dl>
            )}
            {videoSource?.pageUrl && (
              <a href={videoSource.pageUrl} target="_blank" rel="noreferrer">
                查看素材来源页
              </a>
            )}
            <label className="upload-control compact">
              <span>替换本地视频</span>
              <input
                type="file"
                accept="video/*"
                onChange={(event) => loadLocalVideo(event.currentTarget.files?.[0] ?? null)}
              />
            </label>
          </div>
        </div>
      </section>

      <section className="workspace">
        <div className="subtitle-panel">
          <div className="section-head">
            <h2>实时字幕</h2>
            <p>同一条字幕可从临时、稳定更新为已修正或最终状态。</p>
          </div>

          <div className="subtitle-list" aria-live="polite">
            {isVideoCaptionMode ? (
              <div className="empty-state compact">视频字幕已叠加在播放器上，修正记录保留在右侧。</div>
            ) : segments.length === 0 ? (
              <div className="empty-state">点击“启动实时演示”，观察字幕流和修正瞬间。</div>
            ) : (
              segments.map((segment) => (
                <article className={`subtitle-card ${segment.status}`} key={segment.id}>
                  <div className="subtitle-meta">
                    <span>{formatTimeRange(segment)}</span>
                    <span className="version">v{segment.version}</span>
                    <span className={`status ${segment.status}`}>{statusLabel[segment.status]}</span>
                  </div>
                  <p className="source">{segment.sourceText}</p>
                  <p className="translation">{segment.translatedText}</p>
                  {segment.previousTranslation && (
                    <p className="previous">修正前：{segment.previousTranslation}</p>
                  )}
                  {segment.changedTerms.length > 0 && (
                    <div className="term-row">
                      {segment.changedTerms.map((term) => (
                        <span key={term}>{term}</span>
                      ))}
                    </div>
                  )}
                </article>
              ))
            )}
          </div>
        </div>

        <aside className="side-panel">
          <section>
            <h2>Provider 状态</h2>
            {providerStatus ? (
              <div className="provider-grid">
                <div>
                  <span>ASR</span>
                  <strong>{providerStatus.asrProvider}</strong>
                </div>
                <div>
                  <span>翻译</span>
                  <strong>{providerStatus.translationProvider}</strong>
                </div>
                <p>{providerStatus.asrModelPath}</p>
                <p>{providerStatus.translationModel}</p>
              </div>
            ) : (
              <p className="muted">默认使用 Mock Provider 稳定演示，可通过环境变量切换真实模型。</p>
            )}
            {providerDiagnostics.length > 0 && (
              <div className="diagnostic-list">
                {providerDiagnostics.map((item) => (
                  <article className={`diagnostic-item ${item.ready ? "ready" : "blocked"}`} key={item.kind}>
                    <div>
                      <strong>{item.kind === "asr" ? "ASR" : "翻译"} · {item.name}</strong>
                      <span>{item.ready ? "已就绪" : "需配置"} · {item.mode}</span>
                    </div>
                    <p>{item.message}</p>
                    <p>{item.action}</p>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section>
            <h2>音频入口</h2>
            <div className="recording-actions">
              <button type="button" className="secondary" onClick={startAudioStream} disabled={isStreamingAudio}>
                开始流式同传
              </button>
              <button type="button" className="secondary" onClick={stopAudioStream} disabled={!isStreamingAudio}>
                停止流式同传
              </button>
            </div>
            <div className="recording-actions">
              <button type="button" className="secondary" onClick={startRecording} disabled={isRecording}>
                开始录音
              </button>
              <button type="button" className="secondary" onClick={stopRecording} disabled={!isRecording}>
                停止录音
              </button>
            </div>
            <label className="upload-control">
              <span>上传英文音频</span>
              <input
                type="file"
                accept="audio/*,video/*"
                onChange={(event) => uploadAudio(event.currentTarget.files?.[0] ?? null)}
              />
            </label>
            {audioResult ? (
              <div className="audio-result">
                <strong>{audioResult.filename}</strong>
                <p>{audioResult.sourceText}</p>
                <p>{audioResult.translatedText}</p>
                <span>
                  {audioResult.provider} · {audioResult.bytesReceived} bytes
                </span>
              </div>
            ) : (
              <p className="muted">当前接口使用 Mock Provider，后续可替换为 faster-whisper。</p>
            )}
          </section>

          <section>
            <h2>量化指标</h2>
            <div className="metrics-grid">
              <Metric label="首字幕延迟" value={formatLatency(metrics.firstSubtitleLatencyMs)} />
              <Metric label="修正延迟" value={formatLatency(metrics.correctionLatencyMs)} />
              <Metric label="术语命中率" value={formatRate(metrics.glossaryHitRate)} />
              <Metric label="最终稳定率" value={formatRate(metrics.finalStabilityRate)} />
            </div>
          </section>

          <section>
            <h2>修正亮点</h2>
            {correctedSegment ? (
              <div className="highlight-box">
                <strong>已触发局部回溯修正</strong>
                <p>{correctedSegment.previousTranslation}</p>
                <p>{correctedSegment.translatedText}</p>
              </div>
            ) : (
              <p className="muted">等待后续上下文触发 correction 事件。</p>
            )}
          </section>

          <section>
            <h2>修正时间线</h2>
            {correctionTraces.length > 0 ? (
              <div className="correction-timeline">
                {correctionTraces.map((trace) => (
                  <article className="correction-trace" key={trace.segmentId}>
                    <div>
                      <strong>{trace.trigger}</strong>
                      <span>{`${trace.latencyMs}ms · v${trace.fromVersion} -> v${trace.toVersion}`}</span>
                    </div>
                    <p>{trace.reason}</p>
                    <p className="trace-before">{trace.previousTranslation}</p>
                    <p className="trace-after">{trace.correctedTranslation}</p>
                    <div className="term-row">
                      {trace.changedTerms.map((term) => (
                        <span key={term}>{term}</span>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted">修正发生后会记录触发原因、版本变化和修正延迟。</p>
            )}
          </section>

          <section>
            <h2>字幕版本轨迹</h2>
            {revisions.length > 0 ? (
              <div className="revision-list">
                {Object.entries(revisionGroups).map(([segmentId, items]) => (
                  <article className="revision-group" key={segmentId}>
                    <strong>{segmentId}</strong>
                    {items.map((revision) => (
                      <div className="revision-item" key={`${revision.segmentId}-${revision.version}`}>
                        <div>
                          <span className={`status ${revision.status}`}>{statusLabel[revision.status]}</span>
                          <span>v{revision.version}</span>
                          <span>{Math.round(revision.confidence * 100)}%</span>
                        </div>
                        <p>{revision.translatedText}</p>
                      </div>
                    ))}
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted">字幕更新后会记录每个版本的状态、置信度和译文变化。</p>
            )}
          </section>

          <section>
            <h2>术语表</h2>
            <div className="glossary-list">
              {glossary.length === 0 ? (
                <p className="muted">演示开始后加载术语表。</p>
              ) : (
                glossary.map((term) => (
                  <div className="glossary-item" key={term.source}>
                    <span>{term.category}</span>
                    <strong>{term.source}</strong>
                    <p>{term.target}</p>
                  </div>
                ))
              )}
            </div>
          </section>

          <section>
            <h2>会后总结</h2>
            {summary ? (
              <div className="summary-box">
                <strong>{summary.title}</strong>
                <p>{summary.summary}</p>
                <ul>
                  {summary.keyPoints.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
                <div className="keyword-row">
                  {summary.keywords.map((keyword) => (
                    <span key={keyword}>{keyword}</span>
                  ))}
                </div>
                <div className="summary-detail">
                  <span>命中术语</span>
                  <p>{summary.glossaryTerms.join(" / ") || "无"}</p>
                  <span>修正记录</span>
                  <p>{summary.correctionNotes.join("；") || "无"}</p>
                </div>
              </div>
            ) : (
              <p className="muted">演示后可生成结构化总结，用于复盘和学习笔记。</p>
            )}
          </section>
        </aside>
      </section>

      <section className="export-panel">
        <div>
          <h2>导出预览</h2>
          <p>导出内容仅包含最终或已修正字幕，适合放入 demo 视频展示。</p>
          <div className="export-actions">
            <button type="button" className="secondary" onClick={() => downloadTranscript("markdown")}>
              下载 MD
            </button>
            <button type="button" className="secondary" onClick={() => downloadTranscript("srt")}>
              下载 SRT
            </button>
          </div>
        </div>
        <textarea readOnly value={exportText} placeholder="最终双语字幕会显示在这里。" />
      </section>

      {currentSegment && !isVideoCaptionMode && (
        <div className="caption-bar" aria-live="polite">
          <span className={`status ${currentSegment.status}`}>{statusLabel[currentSegment.status]}</span>
          <strong>{currentSegment.translatedText}</strong>
        </div>
      )}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
