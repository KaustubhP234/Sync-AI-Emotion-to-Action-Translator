# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt
from datetime import datetime
import io
import os

# -----------------------------
# CONFIG
# -----------------------------
API_ROOT = "http://127.0.0.1:8000/api/emotion"
st.set_page_config(page_title="SoulSync AI", layout="wide")
st.markdown("<h1 style='text-align:center;'>🎧 SoulSync AI – Emotion to Action Translator</h1>", unsafe_allow_html=True)

# Sidebar user ID and mode
user = st.sidebar.text_input("User ID", value="anon")
smart_mode = st.sidebar.checkbox("Smart Environment Mode", value=True)
st.sidebar.markdown("---")
st.sidebar.info("🧠 Emotion-based adaptive visuals, audio & analytics")

# -----------------------------
# SELECT INPUT TYPE
# -----------------------------
option = st.selectbox("Choose Input Type", ["Voice", "Text", "History"])

# helper: Music UI (used after we get a prediction `j`)
def music_ui_block(j):
    if not j:
        st.info("No emotion available for music generation.")
        return

    st.markdown("### 🎶 Emotion → Music")
    music_mode = st.radio("Music Mode", ["Curated (Spotify preview)", "AI Generated (MusicGen)"], index=0)
    duration = st.slider("Duration (seconds, generated only)", 5, 20, 8, step=1)
    if st.button("Play Soundtrack for this emotion"):
        mode = "curated" if music_mode.startswith("Curated") else "generated"
        try:
            resp = requests.post(
                f"{API_ROOT}/generate_music",
                data={"emotion": j.get("emotion"), "mode": mode, "duration": duration},
                timeout=60,
            )
            # If backend returned JSON with URL or error
            ct = resp.headers.get("content-type", "")
            if "application/json" in ct:
                j2 = resp.json()
                if j2.get("type") == "url":
                    st.info("Playing Spotify preview (30s).")
                    st.audio(j2.get("url"))
                else:
                    # server returned JSON but not URL -> show message or error
                    if j2.get("message"):
                        st.error(j2.get("message"))
                    else:
                        st.error("No music available.")
            else:
                # assume audio bytes returned (WAV)
                st.audio(resp.content, format="audio/wav")
        except Exception as e:
            st.error(f"Music generation failed: {e}")

# -----------------------------
# VOICE INPUT
# -----------------------------
if option == "Voice":
    uploaded_file = st.file_uploader("🎙 Upload Voice File (.wav)", type=["wav"])
    if uploaded_file:
        if st.button("Analyze Audio"):
            try:
                with st.spinner("Analyzing emotion..."):
                    res = requests.post(
                        f"{API_ROOT}/analyze_audio",
                        files={"file": uploaded_file},
                        data={"user_id": user},
                        timeout=60,
                    )
                try:
                    j = res.json()
                except Exception:
                    st.error("❌ Server returned non-JSON response.")
                    j = {}

                if not j:
                    st.info("No response from server.")
                else:
                    st.success("✅ Emotion Detected!")
                    st.markdown(f"**Emotion:** `{j.get('emotion')}`")
                    st.markdown(f"**Confidence:** `{j.get('confidence')}`")
                    st.markdown(f"**Action:** {j.get('action')}")

                    # Smart Environment Visuals + Audio
                    scene = j.get("scene")
                    sound = j.get("sound")

                    if smart_mode:
                        st.markdown("### 🌈 Adaptive Environment")
                        # Button to generate AI scene
                        if st.button("🎨 Generate AI Scene"):
                            try:
                                r = requests.get(
                                    f"{API_ROOT}/generate_scene",
                                    params={"emotion": j.get("emotion")},
                                    timeout=30,
                                )
                                if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                                    st.image(r.content, use_column_width=True)
                                else:
                                    try:
                                        rr = r.json()
                                        st.info(rr.get("message") or "AI scene generation unavailable.")
                                    except Exception:
                                        st.info("AI scene generation unavailable.")
                                    if scene:
                                        st.image(f"frontend/static/scenes/{scene}", use_column_width=True)
                            except Exception as e:
                                st.error(f"Scene generation failed: {e}")
                                if scene:
                                    st.image(f"frontend/static/scenes/{scene}", use_column_width=True)
                        else:
                            # Show static scene if available
                            if scene:
                                try:
                                    if isinstance(scene, str) and scene.startswith("http"):
                                        st.image(scene, use_column_width=True)
                                    else:
                                        st.image(f"frontend/static/scenes/{scene}", use_column_width=True)
                                except Exception:
                                    st.info("⚠️ Scene asset not found. Place files in frontend/static/scenes/")

                        # Play sound if available
                        if sound:
                            try:
                                if isinstance(sound, str) and sound.startswith("http"):
                                    st.audio(sound, format="audio/mp3")
                                else:
                                    try:
                                        with open(f"frontend/static/scenes/{sound}", "rb") as f:
                                            st.audio(f.read(), format="audio/mp3")
                                    except FileNotFoundError:
                                        st.info("🎵 Sound file not found in frontend/static/scenes/")
                            except Exception:
                                st.info("🎵 Sound playback not available.")

                    # Drift alert
                    if j.get("drift_alert"):
                        da = j["drift_alert"]
                        if da.get("alert"):
                            st.warning(da.get("message"))
                        else:
                            st.info(da.get("message"))

                    # Music UI block
                    music_ui_block(j)

            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")

# -----------------------------
# TEXT INPUT
# -----------------------------
elif option == "Text":
    text_input = st.text_area("💬 Enter Text")
    if st.button("Analyze Text"):
        try:
            with st.spinner("Analyzing text emotion..."):
                res = requests.post(
                    f"{API_ROOT}/analyze_text",
                    data={"text": text_input, "user_id": user},
                    timeout=30,
                )
            j = res.json()
            st.success("✅ Emotion Detected!")
            st.json(j)

            # Show scene and sound
            if smart_mode and j.get("scene"):
                st.markdown("### 🌈 Adaptive Environment")
                try:
                    if isinstance(j['scene'], str) and j['scene'].startswith("http"):
                        st.image(j['scene'], use_column_width=True)
                    else:
                        st.image(f"frontend/static/scenes/{j['scene']}", use_column_width=True)
                except Exception:
                    st.info("🎵 Scene asset or sound unavailable.")
                try:
                    if j.get("sound"):
                        with open(f"frontend/static/scenes/{j['sound']}", "rb") as f:
                            st.audio(f.read(), format="audio/mp3")
                except Exception:
                    pass

            # Music UI block
            music_ui_block(j)

        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------
# HISTORY VIEW
# -----------------------------
elif option == "History":
    st.subheader("📊 Emotion History & Analytics")
    col1, col2 = st.columns([1, 1])
    with col1:
        limit = st.number_input("Number of recent entries", min_value=5, max_value=200, value=50, step=5)
    with col2:
        refresh = st.button("🔄 Refresh")

    try:
        r = requests.get(f"{API_ROOT}/history", params={"limit": limit}, timeout=15)
        hist_data = r.json().get("history", [])
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        hist_data = []

    if not hist_data:
        st.info("No history yet. Analyze some audio or text to populate data.")
    else:
        df = pd.DataFrame(hist_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        st.markdown("### 🕒 Recent Entries")
        st.dataframe(df[['timestamp', 'input_type', 'filename', 'emotion', 'confidence', 'action']])

        # Emotion timeline
        st.markdown("### 📈 Emotion Timeline")
        chart_df = df.copy()
        chart_df['index'] = range(len(chart_df))
        chart = alt.Chart(chart_df).mark_circle(size=70).encode(
            x=alt.X('timestamp:T', title='Time'),
            y=alt.Y('emotion:N', title='Emotion'),
            color='emotion:N',
            tooltip=['timestamp:T', 'emotion:N', 'confidence', 'action']
        ).interactive().properties(height=300)
        st.altair_chart(chart, use_container_width=True)

        # Pie chart distribution
        st.markdown("### 🧩 Emotion Distribution")
        dist = df['emotion'].value_counts().reset_index()
        dist.columns = ['emotion', 'count']
        pie = alt.Chart(dist).mark_arc().encode(
            theta=alt.Theta(field="count", type="quantitative"),
            color=alt.Color(field="emotion", type="nominal"),
            tooltip=['emotion', 'count']
        )
        st.altair_chart(pie, use_container_width=True)

        # Summary stats
        st.markdown("### 📊 Summary Stats")
        most_freq = df['emotion'].mode()[0]
        avg_conf = round(df['confidence'].astype(float).mean(), 2)
        st.write(f"**Most frequent emotion:** {most_freq}")
        st.write(f"**Average confidence:** {avg_conf}%")

        # Stability snapshot
        try:
            s = requests.get(f"{API_ROOT}/stability", params={"limit": limit}, timeout=10)
            stab = s.json().get("stability", {})
            st.markdown("### 📊 Stability Snapshot")
            st.json(stab)
        except Exception as e:
            st.info("Stability endpoint unavailable yet.")

        # Download option
        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download History CSV", csv, file_name="emotion_history.csv", mime="text/csv")
