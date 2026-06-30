"""MindMarker speech analysis: transcription, linguistics, acoustics, and risk scoring."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import soundfile as sf

FILLER_WORDS = frozenset({"um", "uh", "ah", "like", "well"})

WHISPER_MODEL_NAME = "tiny"
SPACY_MODEL_NAME = "en_core_web_sm"

# Minimum silence (seconds) between speech segments to count as a pause.
PAUSE_MIN_DURATION_SEC = 0.25
# librosa.effects.split top_db threshold for speech vs silence.
SPLIT_TOP_DB = 25


@dataclass
class LinguisticMetrics:
    type_token_ratio: float
    avg_sentence_length: float
    filler_counts: dict[str, int]
    total_words: int
    unique_words: int
    filler_total: int
    pronoun_noun_ratio: float
    adj_adv_density: float


@dataclass
class AcousticMetrics:
    avg_pause_duration: float
    pause_count: int
    speech_duration_sec: float
    words_per_minute: float
    articulation_rate: float
    pitch_variation: float


@dataclass
class RiskResult:
    score: float
    category: str
    color: str
    factors: list[str]


@dataclass
class AnalysisResult:
    transcript: str
    linguistic: LinguisticMetrics
    acoustic: AcousticMetrics
    risk: RiskResult
    is_demo: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "transcript": self.transcript,
            "linguistic": asdict(self.linguistic),
            "acoustic": asdict(self.acoustic),
            "risk": asdict(self.risk),
            "is_demo": self.is_demo,
        }


def load_whisper_model():
    """Load and cache the local Whisper tiny model."""
    import whisper

    return whisper.load_model(WHISPER_MODEL_NAME)


def load_spacy_model():
    """Load and cache the spaCy English model."""
    import spacy

    try:
        return spacy.load(SPACY_MODEL_NAME)
    except OSError as exc:
        raise RuntimeError(
            f"spaCy model '{SPACY_MODEL_NAME}' is not installed. "
            f"Run: python -m spacy download {SPACY_MODEL_NAME}"
        ) from exc


def transcribe_audio(audio_path: str | Path) -> str:
    """Transcribe an audio file using the local Whisper tiny model."""
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    model = load_whisper_model()
    result = model.transcribe(str(path), fp16=False, language="en")
    text = (result.get("text") or "").strip()
    if not text:
        raise ValueError("Transcription returned empty text. Try a clearer recording.")
    return text


def analyze_linguistics(text: str) -> LinguisticMetrics:
    """Extract linguistic markers from transcript text using spaCy."""
    if not text or not text.strip():
        raise ValueError("Cannot analyze empty transcript.")

    nlp = load_spacy_model()
    doc = nlp(text)

    tokens = [
        token
        for token in doc
        if not token.is_space and not token.is_punct and token.is_alpha
    ]
    words = [token.text.lower() for token in tokens]
    total_words = len(words)

    if total_words == 0:
        raise ValueError("No analyzable words found in transcript.")

    unique_words = len(set(words))
    type_token_ratio = unique_words / total_words

    sentences = list(doc.sents)
    if sentences:
        avg_sentence_length = total_words / len(sentences)
    else:
        avg_sentence_length = float(total_words)

    filler_counts = {word: words.count(word) for word in sorted(FILLER_WORDS)}
    filler_total = sum(filler_counts.values())

    # Count pronouns and nouns
    pronouns_count = sum(1 for token in tokens if token.pos_ == "PRON")
    nouns_count = sum(1 for token in tokens if token.pos_ in {"NOUN", "PROPN"})
    pronoun_noun_ratio = pronouns_count / max(nouns_count, 1)

    # Count adjectives and adverbs
    adj_adv_count = sum(1 for token in tokens if token.pos_ in {"ADJ", "ADV"})
    adj_adv_density = adj_adv_count / total_words

    return LinguisticMetrics(
        type_token_ratio=round(type_token_ratio, 3),
        avg_sentence_length=round(avg_sentence_length, 2),
        filler_counts=filler_counts,
        total_words=total_words,
        unique_words=unique_words,
        filler_total=filler_total,
        pronoun_noun_ratio=round(pronoun_noun_ratio, 2),
        adj_adv_density=round(adj_adv_density, 3),
    )


def analyze_acoustics(
    audio_path: str | Path,
    total_words: int,
    *,
    sr: int | None = None,
) -> AcousticMetrics:
    """Detect pauses with librosa.effects.split and derive speech-rate metrics."""
    path = Path(audio_path)
    y, sample_rate = librosa.load(str(path), sr=sr, mono=True)
    if y.size == 0:
        raise ValueError("Audio file appears to be empty.")

    duration_sec = float(len(y) / sample_rate)
    if duration_sec <= 0:
        raise ValueError("Invalid audio duration.")

    intervals = librosa.effects.split(y, top_db=SPLIT_TOP_DB)
    pause_durations: list[float] = []

    if len(intervals) > 1:
        for idx in range(len(intervals) - 1):
            pause_start = intervals[idx][1]
            pause_end = intervals[idx + 1][0]
            pause_sec = (pause_end - pause_start) / sample_rate
            if pause_sec >= PAUSE_MIN_DURATION_SEC:
                pause_durations.append(pause_sec)

    avg_pause_duration = (
        float(np.mean(pause_durations)) if pause_durations else 0.0
    )
    words_per_minute = (total_words / duration_sec) * 60.0 if duration_sec else 0.0

    # Articulation rate: total words / actual speaking time (excluding silence/pauses)
    total_pause_duration = sum(pause_durations)
    speaking_duration = max(0.5, duration_sec - total_pause_duration)
    articulation_rate = (total_words / speaking_duration) * 60.0

    # Pitch variation estimation (YIN algorithm std dev or fallback to spectral centroid)
    pitch_variation = 0.0
    try:
        # Use yin with frame parameters to make it fast
        pitches = librosa.yin(
            y,
            fmin=60,
            fmax=350,
            sr=sample_rate,
            frame_length=2048,
            hop_length=512
        )
        valid_pitches = pitches[~np.isnan(pitches)]
        if valid_pitches.size > 0:
            pitch_variation = float(np.std(valid_pitches))
    except Exception:
        try:
            cent = librosa.feature.spectral_centroid(y=y, sr=sample_rate)
            pitch_variation = float(np.std(cent)) / 100.0
        except Exception:
            pitch_variation = 0.0

    return AcousticMetrics(
        avg_pause_duration=round(avg_pause_duration, 3),
        pause_count=len(pause_durations),
        speech_duration_sec=round(duration_sec, 2),
        words_per_minute=round(words_per_minute, 1),
        articulation_rate=round(articulation_rate, 1),
        pitch_variation=round(pitch_variation, 2),
    )


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _score_speech_rate(wpm: float) -> tuple[float, str | None]:
    """Lower speech rate increases risk contribution."""
    if wpm < 70:
        return 95.0, "Very slow speech rate"
    if wpm < 90:
        return 78.0, "Slow speech rate"
    if wpm < 110:
        return 52.0, "Below-average speech rate"
    if wpm <= 160:
        return 18.0, None
    if wpm <= 190:
        return 35.0, "Slightly fast speech rate"
    return 48.0, "Unusually fast speech rate"


def _score_fillers(filler_total: int, total_words: int) -> tuple[float, str | None]:
    """Filler words are weighted heavily for responsiveness."""
    filler_rate = filler_total / max(total_words, 1)
    count_component = min(55.0, filler_total * 11.0)
    rate_component = min(45.0, filler_rate * 320.0)
    score = _clamp(count_component + rate_component)

    note = None
    if filler_total >= 4 or filler_rate >= 0.08:
        note = "Elevated filler-word usage"
    elif filler_total >= 2:
        note = "Moderate filler-word usage"
    return score, note


def _score_ttr(ttr: float) -> tuple[float, str | None]:
    if ttr < 0.35:
        return 82.0, "Low vocabulary diversity (TTR)"
    if ttr < 0.45:
        return 58.0, "Reduced vocabulary diversity (TTR)"
    if ttr < 0.55:
        return 32.0, None
    return 12.0, None


def _score_sentence_length(avg_len: float) -> tuple[float, str | None]:
    if avg_len < 4:
        return 72.0, "Very short utterances"
    if avg_len < 7:
        return 48.0, "Short average sentences"
    if avg_len <= 14:
        return 20.0, None
    if avg_len <= 18:
        return 38.0, "Long, potentially fragmented sentences"
    return 55.0, "Unusually long sentences"


def _score_pauses(avg_pause: float, pause_count: int, duration_sec: float) -> tuple[float, str | None]:
    pause_density = pause_count / max(duration_sec, 1.0)
    duration_component = min(50.0, avg_pause * 55.0)
    density_component = min(50.0, pause_density * 18.0)
    score = _clamp(duration_component + density_component)

    note = None
    if avg_pause >= 0.8 or pause_density >= 0.35:
        note = "Frequent or prolonged pauses"
    elif avg_pause >= 0.45 or pause_count >= 3:
        note = "Noticeable pausing pattern"
    return score, note


def _score_pronoun_noun_ratio(ratio: float) -> tuple[float, str | None]:
    if ratio > 0.65:
        return 75.0, "High pronoun-to-noun ratio (potential anomia)"
    if ratio > 0.45:
        return 50.0, "Moderate pronoun-to-noun ratio"
    return 15.0, None


def _score_pitch_variation(std_dev: float) -> tuple[float, str | None]:
    if std_dev > 0.0 and std_dev < 12.0:
        return 65.0, "Monotone/reduced pitch variation"
    return 15.0, None


def calculate_risk_score(
    linguistic: LinguisticMetrics,
    acoustic: AcousticMetrics,
) -> RiskResult:
    """
    Rule-based 0–100 risk score from linguistic and acoustic markers.
    """
    rate_score, rate_note = _score_speech_rate(acoustic.words_per_minute)
    filler_score, filler_note = _score_fillers(
        linguistic.filler_total, linguistic.total_words
    )
    ttr_score, ttr_note = _score_ttr(linguistic.type_token_ratio)
    sentence_score, sentence_note = _score_sentence_length(
        linguistic.avg_sentence_length
    )
    pause_score, pause_note = _score_pauses(
        acoustic.avg_pause_duration,
        acoustic.pause_count,
        acoustic.speech_duration_sec,
    )
    pronoun_score, pronoun_note = _score_pronoun_noun_ratio(linguistic.pronoun_noun_ratio)
    pitch_score, pitch_note = _score_pitch_variation(acoustic.pitch_variation)

    # Compile the weighted score
    raw_score = (
        rate_score * 0.25
        + filler_score * 0.25
        + pause_score * 0.15
        + pronoun_score * 0.15
        + ttr_score * 0.10
        + sentence_score * 0.05
        + pitch_score * 0.05
    )
    score = round(_clamp(raw_score), 1)

    if score < 35:
        category = "Low"
        color = "#22c55e"
    elif score < 65:
        category = "Elevated"
        color = "#f97316"
    else:
        category = "High Risk"
        color = "#ef4444"

    factors = [
        note
        for note in (rate_note, filler_note, pause_note, pronoun_note, ttr_note, sentence_note, pitch_note)
        if note
    ]
    if not factors:
        factors = ["Speech patterns within typical range for this screening model"]

    return RiskResult(score=score, category=category, color=color, factors=factors)


def analyze_audio_file(audio_path: str | Path) -> AnalysisResult:
    """Full pipeline: transcribe, linguistic + acoustic analysis, risk scoring."""
    transcript = transcribe_audio(audio_path)
    linguistic = analyze_linguistics(transcript)
    acoustic = analyze_acoustics(audio_path, linguistic.total_words)
    risk = calculate_risk_score(linguistic, acoustic)
    return AnalysisResult(
        transcript=transcript,
        linguistic=linguistic,
        acoustic=acoustic,
        risk=risk,
    )


def analyze_uploaded_bytes(audio_bytes: bytes, suffix: str = ".wav") -> AnalysisResult:
    """Persist uploaded bytes to a temp file, analyze, and clean up."""
    if not audio_bytes:
        raise ValueError("Uploaded file is empty.")

    suffix = suffix if suffix.startswith(".") else f".{suffix}"
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Validate readable audio early for clearer errors.
        sf.read(tmp_path)
        return analyze_audio_file(tmp_path)
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def get_demo_analysis() -> AnalysisResult:
    """Return stable mock results for live demos without an uploaded file."""
    linguistic = LinguisticMetrics(
        type_token_ratio=0.41,
        avg_sentence_length=6.8,
        filler_counts={"ah": 1, "like": 3, "uh": 2, "um": 4, "well": 1},
        total_words=58,
        unique_words=24,
        filler_total=11,
        pronoun_noun_ratio=0.55,
        adj_adv_density=0.086,
    )
    acoustic = AcousticMetrics(
        avg_pause_duration=0.62,
        pause_count=5,
        speech_duration_sec=30.0,
        words_per_minute=116.0,
        articulation_rate=135.2,
        pitch_variation=10.4,
    )
    risk = calculate_risk_score(linguistic, acoustic)
    transcript = (
        "Um, well, I was thinking about, uh, going to the store yesterday. "
        "Like, I needed milk and, um, some bread. Uh, the weather was nice, "
        "like, really sunny. Well, I saw my neighbor and, um, we talked for "
        "a bit. Uh, then I came home and, like, made lunch."
    )
    return AnalysisResult(
        transcript=transcript,
        linguistic=linguistic,
        acoustic=acoustic,
        risk=risk,
        is_demo=True,
    )
