from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from stt_simple.project.app.stt import transcribe_buffer

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index():
    # Minimal test page to stream microphone chunks to /ws and log transcriptions.
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>STT Demo</title>
        <style>
            body { font-family: sans-serif; max-width: 720px; margin: 40px auto; }
            button { padding: 10px 16px; margin-right: 8px; }
            #log { background: #111; color: #0f0; padding: 12px; min-height: 160px; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>Real-time STT Demo</h1>
        <p>Нажмите Start, дайте доступ к микрофону и дождитесь результата после буфера &gt; 64 KB.</p>
        <p>Если текста нет — говорите 4-6 секунд, следите за Bytes sent &gt; 65000.</p>
        <button id="start">Start</button>
        <button id="stop">Stop</button>
        <div id="status">Status: idle</div>
        <div id="last">Last result: (none)</div>
        <div id="sent">Bytes sent: 0</div>
        <pre id="log"></pre>

        <script>
            const logEl = document.getElementById("log");
            const statusEl = document.getElementById("status");
            const lastEl = document.getElementById("last");
            const sentEl = document.getElementById("sent");
            const startBtn = document.getElementById("start");
            const stopBtn = document.getElementById("stop");

            let ws;
            let mediaStream;
            let sentBytes = 0;
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            let sourceNode = null;
            let processorNode = null;

            function log(line) {
                const ts = new Date().toLocaleTimeString();
                logEl.textContent += `[${ts}] ${line}\\n`;
                logEl.scrollTop = logEl.scrollHeight;
            }

            window.onerror = (msg, src, lineNo, colNo, err) => {
                log(`JS error: ${msg} @ ${lineNo}:${colNo}`);
            };

            function setStatus(text) {
                statusEl.textContent = `Status: ${text}`;
            }

            function ensureSocket() {
                if (ws && ws.readyState === WebSocket.OPEN) return;
                ws = new WebSocket(`ws://${location.host}/ws`);

                ws.onopen = () => setStatus("ws open");
                ws.onclose = (ev) => {
                    setStatus(`ws closed (${ev.code})`);
                    log(`WebSocket closed code=${ev.code}`);
                };
                ws.onerror = (e) => {
                    console.error(e);
                    log("WebSocket error");
                };
                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        lastEl.textContent = `Last result: ${data.text || "(empty)"}`;
                        log(`text: ${data.text} | duration: ${data.duration.toFixed(2)}s`);
                    } catch (err) {
                        log("Received non-JSON message");
                    }
                };
            }

            function downsampleTo16k(audioBuffer) {
                const channelData = audioBuffer.getChannelData(0);
                const sampleRate = audioBuffer.sampleRate;
                if (sampleRate === 16000) return channelData;

                const ratio = sampleRate / 16000;
                const newLength = Math.floor(channelData.length / ratio);
                const result = new Float32Array(newLength);
                for (let i = 0; i < newLength; i++) {
                    result[i] = channelData[Math.floor(i * ratio)];
                }
                return result;
            }

            function floatTo16BitPCM(float32Array) {
                const output = new Int16Array(float32Array.length);
                for (let i = 0; i < float32Array.length; i++) {
                    const s = Math.max(-1, Math.min(1, float32Array[i]));
                    output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
                }
                return output;
            }

            async function start() {
                ensureSocket();
                try {
                    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                } catch (err) {
                    log("Mic permission denied");
                    return;
                }

                try {
                    await audioCtx.resume();
                    log(`AudioContext sampleRate=${audioCtx.sampleRate}`);
                    sourceNode = audioCtx.createMediaStreamSource(mediaStream);
                    processorNode = audioCtx.createScriptProcessor(4096, 1, 1);
                    processorNode.onaudioprocess = (audioProcessingEvent) => {
                        if (!ws || ws.readyState !== WebSocket.OPEN) return;
                        const input = audioProcessingEvent.inputBuffer;
                        const mono16k = downsampleTo16k(input);
                        const pcm16 = floatTo16BitPCM(mono16k);
                        ws.send(pcm16.buffer);
                        sentBytes += pcm16.byteLength;
                        sentEl.textContent = `Bytes sent: ${sentBytes}`;
                    };

                    sourceNode.connect(processorNode);
                    processorNode.connect(audioCtx.destination);
                    setStatus("recording...");
                    log("Recording started");
                } catch (err) {
                    console.error(err);
                    log(`Audio processing setup failed: ${err?.message || err}`);
                }
            }

            function stop() {
                sentBytes = 0;
                sentEl.textContent = "Bytes sent: 0";
                if (processorNode) {
                    processorNode.disconnect();
                    processorNode.onaudioprocess = null;
                    processorNode = null;
                }
                if (sourceNode) {
                    sourceNode.disconnect();
                    sourceNode = null;
                }
                if (mediaStream) {
                    mediaStream.getTracks().forEach((t) => t.stop());
                    mediaStream = null;
                }
                setStatus("stopped");
            }

            startBtn.onclick = start;
            stopBtn.onclick = stop;
        </script>
    </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    audio_chunks: list[bytes] = []
    buffer_size = 0

    while True:
        chunk = await ws.receive_bytes()
        audio_chunks.append(chunk)
        buffer_size += len(chunk)

        if buffer_size > 65536:
            text, duration = transcribe_buffer(audio_chunks)
            await ws.send_json({"text": text, "duration": duration})
            audio_chunks.clear()
            buffer_size = 0
