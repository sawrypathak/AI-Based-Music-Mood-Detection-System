"""
Mood → Spotify 🎧🌌
Galaxy UI + Text/Voice Mood + History + Hidden Joji Background Music

Install once:
    pip install transformers torch gradio SpeechRecognition
"""

import gradio as gr
from transformers import pipeline
import speech_recognition as sr
from datetime import datetime

# ------------------------------
# 1. Load model (PyTorch only)
# ------------------------------
sentiment_model = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    framework="pt",
)

# ------------------------------
# 2. Spotify playlists
# ------------------------------
PLAYLISTS = {
    "POSITIVE": "https://open.spotify.com/playlist/55HWcJRv1NwmSzUjpclgHc?si=3efc79c5c6264930",
    "NEGATIVE": "https://open.spotify.com/playlist/3blDQRbS56VXZfEDzkpAHZ?si=137b8745022145d1",
    "NEUTRAL":  "https://open.spotify.com/playlist/1vMEUmmMGwiI8gx86pEgPr?si=1af51a7071aa47c6",
}

MOOD_EMOJI = {
    "POSITIVE": "🌈",
    "NEGATIVE": "🌘",
    "NEUTRAL": "🪐",
}

history = []


# ------------------------------
# 3. Helpers
# ------------------------------
def get_mood_label(result):
    score = float(result["score"])
    label = result["label"]
    if score < 0.75:
        return "NEUTRAL", score
    return label, score


def format_history_html():
    if not history:
        return "<div class='history-empty'>No mood history yet… your galaxy log will appear here ✨</div>"

    items = []
    for h in reversed(history[-10:]):
        emoji = MOOD_EMOJI[h["mood"]]
        items.append(
            f"""
            <div class="history-entry">
                <div class="history-main">
                    <span class="history-emoji">{emoji}</span>
                    <span class="history-mood">{h['mood']}</span>
                    <span class="history-text">‘{h['text']}’</span>
                </div>
                <div class="history-meta">
                    {h['time']} · via {h['source']} · confidence {h['score']}
                </div>
            </div>
            """
        )
    return "<div class='history-list'>" + "".join(items) + "</div>"


def analyze(text, source):
    text = text.strip()
    if not text:
        msg = """
        <div class="bubble bubble-neutral">
            ⚠️ Please type or speak something so I can read your vibe 💫
        </div>
        """
        return msg, "", "", format_history_html()

    out = sentiment_model(text)[0]
    mood, score = get_mood_label(out)
    emoji = MOOD_EMOJI[mood]
    url = PLAYLISTS[mood]

    history.append(
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "text": text,
            "mood": mood,
            "score": round(score, 2),
        }
    )

    mood_class = {
        "POSITIVE": "bubble-positive",
        "NEGATIVE": "bubble-negative",
        "NEUTRAL": "bubble-neutral",
    }[mood]

    mood_html = f"""
    <div class="bubble {mood_class}">
        <div class="bubble-title">{emoji} Mood detected: <strong>{mood}</strong></div>
        <div class="bubble-body">✨ Confidence: <code>{score:.2f}</code></div>
    </div>
    """

    explanation_html = f"""
    <div class="bubble bubble-secondary">
        <div class="bubble-label">You said:</div>
        <div class="bubble-quote">“{text}”</div>
        <div class="bubble-sub">
            My galaxy brain thinks this feels <strong>{mood.lower()}</strong>.<br>
            <span class="bubble-raw">
                Raw model: <code>{out['label']}</code> · confidence <code>{out['score']:.2f}</code>
            </span>
        </div>
    </div>
    """

    playlist_html = f"""
    <div class="bubble bubble-link">
        <a href="{url}" target="_blank" rel="noopener noreferrer">
            🎧 Drift into your {mood.lower()} playlist →
        </a>
    </div>
    """

    history_html = format_history_html()
    return mood_html, explanation_html, playlist_html, history_html


def text_to_mood(text):
    return analyze(text, "text")


def voice_to_mood(audio):
    if audio is None:
        msg = """
        <div class="bubble bubble-neutral">
            ⚠️ No audio recorded. Try speaking again a little closer to the mic 🎙️
        </div>
        """
        return msg, "", "", format_history_html()

    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio) as source:
            audio_data = r.record(source)
        text = r.recognize_google(audio_data)
    except Exception:
        msg = """
        <div class="bubble bubble-neutral">
            ⚠️ I couldn't understand your voice. Try again slowly and clearly 🫧
        </div>
        """
        return msg, "", "", format_history_html()

    return analyze(text, "voice")


# ------------------------------
# 4. Build UI
# ------------------------------
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    # Global CSS + header + graphics + signature + hidden bg audio hook
    gr.HTML(
        """
        <style>
        body {
            margin: 0;
            background:
                radial-gradient(circle at 10% 20%, #1a1630 0, #050411 45%, #02010a 80%);
            color: #f5f5ff;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .app-header {
            text-align: center;
            padding-top: 8px;
            padding-bottom: 4px;
        }
        .app-header h1 {
            font-size: 36px;
            font-weight: 800;
            letter-spacing: 1px;
            margin: 0;
            background: linear-gradient(120deg, #ff9dff, #8bd7ff, #a1ffce);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .app-header p {
            margin: 4px 0 8px 0;
            color: #d2d5ff;
            font-size: 13px;
        }

        .dark-card {
            background: rgba(15, 15, 30, 0.95);
            border-radius: 18px;
            padding: 14px;
            border: 1px solid rgba(120, 120, 170, 0.6);
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.8);
        }

        .neon-btn {
            border-radius: 999px;
            padding: 11px 18px;
            width: 100%;
            border: none;
            background: linear-gradient(90deg, #ff8af2, #7df2ff);
            color: #050411;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 0 12px rgba(255, 138, 242, 0.4);
            transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
        }
        .neon-btn:hover {
            transform: translateY(-1px) scale(1.02);
            filter: brightness(1.05);
            box-shadow: 0 0 18px rgba(255, 138, 242, 0.7),
                        0 0 18px rgba(125, 242, 255, 0.65);
        }

        .output-card, .history-card {
            background: rgba(8, 8, 20, 0.95);
            border-radius: 18px;
            padding: 14px 16px;
            border: 1px solid rgba(130, 130, 190, 0.6);
            color: #f3f4ff;
            font-size: 14px;
        }
        .history-card {
            margin-top: 8px;
            max-height: 240px;
            overflow-y: auto;
            border-style: dashed;
            font-size: 13px;
        }

        /* Galaxy graphics */
        .graphic-box {
            display: flex;
            align-items: center;
            gap: 14px;
            margin: 6px auto 12px auto;
            max-width: 360px;
        }
        .planet-wrapper {
            position: relative;
            width: 80px;
            height: 80px;
        }
        .planet {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #ffffff 0, #ffe0ff 8%, #9b5fff 40%, #241148 75%);
            box-shadow:
                0 0 20px rgba(155, 95, 255, 0.8),
                0 0 45px rgba(72, 222, 255, 0.4);
        }
        .ring {
            position: absolute;
            top: 34px;
            left: -8px;
            width: 96px;
            height: 24px;
            border-radius: 50%;
            border: 2px solid rgba(164, 255, 250, 0.8);
            border-left-color: transparent;
            border-right-color: transparent;
            transform: rotate(-15deg);
            filter: drop-shadow(0 0 8px rgba(164,255,250,0.7));
        }
        .moon {
            position: absolute;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #c8f7ff;
            top: 50%;
            left: 50%;
            transform-origin: -28px -20px;
            animation: orbit 6s linear infinite;
            box-shadow: 0 0 8px rgba(200,247,255,0.9);
        }
        @keyframes orbit {
            from { transform: rotate(0deg); }
            to   { transform: rotate(360deg); }
        }
        .stars {
            position: absolute;
            inset: -8px;
        }
        .star {
            position: absolute;
            width: 3px;
            height: 3px;
            border-radius: 50%;
            background: #ffffff;
            box-shadow: 0 0 8px rgba(255,255,255,0.8);
            animation: twinkle 1.8s infinite ease-in-out alternate;
        }
        .star:nth-child(1) { top: 8%; left: 15%; animation-delay: 0.1s; }
        .star:nth-child(2) { top: 20%; right: 10%; animation-delay: 0.5s; }
        .star:nth-child(3) { bottom: 15%; left: 20%; animation-delay: 0.9s; }
        .star:nth-child(4) { bottom: 4%; right: 22%; animation-delay: 1.3s; }
        @keyframes twinkle {
            from { opacity: 0.3; transform: scale(0.8); }
            to   { opacity: 1; transform: scale(1.1); }
        }
        .equalizer {
            display: flex;
            align-items: flex-end;
            gap: 4px;
            height: 55px;
        }
        .bar {
            width: 5px;
            border-radius: 999px;
            background: linear-gradient(180deg, #ffb3ff, #7df2ff);
            box-shadow: 0 0 12px rgba(255,179,255,0.8);
            animation: bounce 1.1s infinite ease-in-out;
            transform-origin: bottom;
        }
        .bar:nth-child(1) { height: 24px; animation-delay: 0s; }
        .bar:nth-child(2) { height: 40px; animation-delay: 0.12s; }
        .bar:nth-child(3) { height: 32px; animation-delay: 0.24s; }
        .bar:nth-child(4) { height: 46px; animation-delay: 0.36s; }
        .bar:nth-child(5) { height: 30px; animation-delay: 0.48s; }
        @keyframes bounce {
            0%   { transform: scaleY(0.6); opacity: 0.7; }
            50%  { transform: scaleY(1.1); opacity: 1; }
            100% { transform: scaleY(0.7); opacity: 0.8; }
        }
        .graphic-caption {
            font-size: 13px;
            color: #e4e5ff;
            opacity: 0.95;
            margin-top: 4px;
        }

        /* Shooting stars */
        .shooting-star {
            position: fixed;
            width: 2px;
            height: 70px;
            background: linear-gradient(to bottom, rgba(255,255,255,0.9), transparent);
            opacity: 0.0;
            pointer-events: none;
            transform: rotate(135deg);
            animation: shoot 6s linear infinite;
        }
        .shooting-star.star1 { top: 8%; left: 80%; animation-delay: 0s; }
        .shooting-star.star2 { top: 25%; left: 10%; animation-delay: 2s; }
        .shooting-star.star3 { top: 60%; left: 60%; animation-delay: 4s; }
        @keyframes shoot {
            0%   { opacity: 0; transform: translate3d(0,0,0) rotate(135deg); }
            10%  { opacity: 0.9; }
            40%  { opacity: 0; transform: translate3d(-120px,120px,0) rotate(135deg); }
            100% { opacity: 0; }
        }

        /* Chat bubbles */
        .bubble {
            border-radius: 14px;
            padding: 10px 12px;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .bubble-positive {
            background: linear-gradient(135deg, rgba(120,255,200,0.1), rgba(80,200,255,0.15));
            border: 1px solid rgba(130,255,220,0.6);
        }
        .bubble-negative {
            background: linear-gradient(135deg, rgba(130,160,255,0.08), rgba(180,110,255,0.16));
            border: 1px solid rgba(190,140,255,0.7);
        }
        .bubble-neutral {
            background: linear-gradient(135deg, rgba(200,200,255,0.08), rgba(170,170,220,0.16));
            border: 1px solid rgba(180,180,230,0.7);
        }
        .bubble-secondary {
            background: rgba(15, 15, 30, 0.9);
            border: 1px solid rgba(130, 130, 190, 0.7);
        }
        .bubble-link {
            text-align: center;
            background: rgba(10, 18, 35, 0.95);
            border: 1px solid rgba(170, 200, 255, 0.7);
        }
        .bubble-link a {
            color: #e7f0ff;
            text-decoration: none;
            font-weight: 600;
        }
        .bubble-link a:hover { text-decoration: underline; }
        .bubble-title { font-weight: 600; margin-bottom: 4px; }
        .bubble-quote { font-style: italic; margin: 4px 0; }
        .bubble-sub { font-size: 13px; opacity: 0.95; }

        .history-empty { opacity: 0.8; font-size: 13px; }
        .history-entry {
            margin-bottom: 6px;
            padding-bottom: 4px;
            border-bottom: 1px dashed rgba(110,110,170,0.45);
        }
        .history-main {
            display: flex;
            flex-wrap: wrap;
            align-items: baseline;
            gap: 6px;
        }
        .history-emoji { font-size: 15px; }
        .history-mood { font-weight: 600; font-size: 13px; }
        .history-text { font-size: 13px; opacity: 0.9; }
        .history-meta { font-size: 11px; color: #a4a5d8; }

        /* Hidden audio player container */
        #bg-music-player { 
            opacity: 0; 
            height: 0; 
            max-height: 0; 
            overflow: hidden;
        }

        /* Little play/pause chip under header */
        .music-chip {
            text-align: center;
            margin-bottom: 6px;
        }
        .music-chip button {
            border-radius: 999px;
            border: 1px solid rgba(150, 150, 220, 0.6);
            background: rgba(15, 15, 30, 0.7);
            color: #e5e6ff;
            font-size: 12px;
            padding: 6px 16px;
            cursor: pointer;
            backdrop-filter: blur(4px);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .music-chip button:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 10px rgba(170,170,255,0.6);
        }

        /* Signature */
        @keyframes softglow {
            0%   { text-shadow: 0 0 4px rgba(185, 160, 255, 0.25); opacity: 0.7; }
            50%  { text-shadow: 0 0 8px rgba(185, 160, 255, 0.45); opacity: 1; }
            100% { text-shadow: 0 0 4px rgba(185, 160, 255, 0.25); opacity: 0.7; }
        }
        .signature {
            position: fixed;
            bottom: 12px;
            right: 16px;
            font-size: 13px;
            color: rgba(220, 220, 255, 0.58);
            background: rgba(20, 20, 35, 0.35);
            padding: 6px 14px;
            border-radius: 10px;
            border: 1px solid rgba(140, 140, 200, 0.25);
            backdrop-filter: blur(6px);
            box-shadow: 0 0 14px rgba(0, 0, 0, 0.4);
            animation: softglow 3.5s infinite ease-in-out;
        }
        </style>

        <!-- Shooting stars -->
        <div class="shooting-star star1"></div>
        <div class="shooting-star star2"></div>
        <div class="shooting-star star3"></div>

        <div class="app-header">
            <h1>Mood → Spotify</h1>
            <p>galaxy-themed AI that turns your feelings into playlists ✨</p>
        </div>

        <div class="graphic-box">
            <div class="planet-wrapper">
                <div class="planet"></div>
                <div class="ring"></div>
                <div class="moon"></div>
                <div class="stars">
                    <div class="star"></div>
                    <div class="star"></div>
                    <div class="star"></div>
                    <div class="star"></div>
                </div>
            </div>
            <div>
                <div class="equalizer">
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                </div>
                <div class="graphic-caption">
                    your feelings → my brain → your playlist ✨
                </div>
            </div>
        </div>

        <div class="music-chip">
            <button onclick="
                const audio = document.querySelector('#bg-music-player audio');
                if (!audio) return;
                if (audio.paused) {
                    audio.play();
                    this.textContent = 'Pause background music ♫';
                } else {
                    audio.pause();
                    this.textContent = 'Play background music ♫';
                }
            ">
                Play background music ♫
            </button>
        </div>

        <div class="signature">Made by Sawry 🪐</div>
        """
    )

    # Hidden audio player (served by Gradio, controlled by JS)
    bg_music = gr.Audio(
        value="Joji_-_Will_He_Nightcore_(mp3.pm).mp3",
        autoplay=False,
        loop=True,
        interactive=False,
        visible=True,          # visible True, but hidden by CSS
        label=None,
        elem_id="bg-music-player",
    )

    with gr.Row():
        # LEFT: input
        with gr.Column(scale=4):
            with gr.Group(elem_classes="dark-card"):
                with gr.Tab("⌨️ Type"):
                    text_inp = gr.Textbox(
                        label="How are you feeling?",
                        lines=3,
                        placeholder="i feel okayish but kinda tired but lowkey proud...",
                    )
                    text_btn = gr.Button("Analyze Mood", elem_classes="neon-btn")

                with gr.Tab("🎤 Voice"):
                    audio_inp = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="Record your voice",
                    )
                    audio_btn = gr.Button(
                        "Analyze Voice Mood", elem_classes="neon-btn"
                    )

        # RIGHT: output
        with gr.Column(scale=6):
            mood_out = gr.HTML(elem_classes="output-card")
            explanation_out = gr.HTML(elem_classes="output-card")
            playlist_out = gr.HTML(elem_classes="output-card")
            history_out = gr.HTML(elem_classes="history-card")

    text_btn.click(
        text_to_mood,
        inputs=text_inp,
        outputs=[mood_out, explanation_out, playlist_out, history_out],
    )
    audio_btn.click(
        voice_to_mood,
        inputs=audio_inp,
        outputs=[mood_out, explanation_out, playlist_out, history_out],
    )

demo.launch()
