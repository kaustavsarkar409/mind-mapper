# 🩺 MindMarker: Clinical Speech Biomarker System

MindMarker is a clinical-grade, research-inspired digital speech biomarker screening application. It analyzes a spontaneous ~30-second audio sample in real-time, extracting acoustic and linguistic markers to visualize a patient's cognitive wellness profile and calculate a cognitive risk index.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Framework](https://img.shields.io/badge/framework-Streamlit-FF4B4B.svg)

---

## 🌟 Key Features

* **Glassmorphic Clinical UI**: Calm, trust-inspiring dark-themed design built with modern aesthetics, custom responsive typography, and glowing CSS background animations.
* **Dual-View Dashboard Toggle**:
  * **Patient Dashboard**: Clean, supportive layout focusing on cognitive wellness scores, reassurance, and recommended cognitive wellness exercises.
  * **Clinician Dashboard**: High-density diagnostic layout showing granular biomarker data plotted against reference ranges with color-coded alerts (Healthy vs. Elevated).
* **Acoustic Biomarkers**: Measures speech rate (Words Per Minute), pause frequency, average pause duration, and total voice segment durations.
* **Linguistic Biomarkers**: Computes Type-Token Ratio (TTR) for vocabulary diversity, average sentence length, and flags/highlights filler words (*um, uh, like*) in the interactive transcript.

---

## 🚀 Local Quickstart

### Prerequisites
* Python 3.9+
* FFmpeg (required by `librosa` and `whisper` for audio decoding)

### Setup & Run
1. **Clone the repository**:
   ```bash
   git clone https://github.com/kaustavsarkar409/mind-mapper.git
   cd mind-mapper
   ```

2. **Create a virtual environment & install dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Download spaCy language model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Launch the application**:
   ```bash
   streamlit run app.py
   ```

---

## ☁️ Public Hosting / Deployment

Here are the easiest methods to publish this application online for others to access:

### Option 1: Streamlit Community Cloud (Free & Recommended)
Streamlit hosts public repositories for free with direct GitHub integration.
1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) using your GitHub account (`kaustavsarkar409`).
2. Click **New app** in the top right.
3. Choose the repository `kaustavsarkar409/mind-mapper`.
4. Set the **Branch** to `main`.
5. Set the **Main file path** to `app.py`.
6. Click **Deploy!** Your app will be live on a public URL (e.g., `https://mind-mapper.streamlit.app/`) in minutes.

### Option 2: Docker / Containerized Hosting (VPS, Render, Railway, AWS)
You can deploy MindMarker as a Docker container. 

1. **Build the image**:
   ```bash
   docker build -t mind-marker .
   ```
2. **Run the container**:
   ```bash
   docker run -p 8501:8501 mind-marker
   ```

---

## ⚠️ Clinical Disclaimer
MindMarker provides a research-inspired digital speech biomarker screening signal only. It does not constitute a medical diagnosis, clinical evaluation, or FDA-approved diagnostic statement. Consult a certified healthcare professional for a comprehensive cognitive assessment.
