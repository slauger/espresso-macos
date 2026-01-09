"""
Audio fingerprinting for identifying specific notification sounds
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime


class AudioFingerprint:
    """Create and compare audio fingerprints"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize audio fingerprinting

        Args:
            config_dir: Directory to store fingerprint database (default: ~/.espresso)
        """
        if config_dir is None:
            config_dir = Path.home() / ".espresso"

        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.fingerprint_file = config_dir / "audio_fingerprints.json"

        # Load existing fingerprints
        self.fingerprints = self.load_fingerprints()

    def load_fingerprints(self) -> Dict:
        """Load fingerprints from disk"""
        if self.fingerprint_file.exists():
            try:
                with open(self.fingerprint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load fingerprints: {e}")

        return {}

    def save_fingerprints(self):
        """Save fingerprints to disk"""
        try:
            with open(self.fingerprint_file, 'w') as f:
                json.dump(self.fingerprints, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save fingerprints: {e}")

    def create_fingerprint(self, audio_samples: np.ndarray, sample_rate: int) -> Dict:
        """
        Create audio fingerprint from samples

        Args:
            audio_samples: Audio data buffer (ring buffer of last N seconds)
            sample_rate: Sample rate

        Returns:
            Dictionary with fingerprint characteristics
        """
        # Calculate basic characteristics
        duration = len(audio_samples) / sample_rate

        # RMS levels over time (split into 10ms chunks)
        chunk_size = int(0.01 * sample_rate)  # 10ms chunks
        rms_profile = []

        for i in range(0, len(audio_samples), chunk_size):
            chunk = audio_samples[i:i+chunk_size]
            if len(chunk) > 0:
                rms = float(np.sqrt(np.mean(chunk**2)))
                rms_profile.append(rms)

        # Peak characteristics
        peak_level = float(np.max(np.abs(audio_samples)))
        mean_level = float(np.mean(np.abs(audio_samples)))

        # Find where audio starts and ends (above threshold)
        threshold = mean_level * 2
        above_threshold = np.abs(audio_samples) > threshold

        if np.any(above_threshold):
            start_idx = np.argmax(above_threshold)
            end_idx = len(audio_samples) - np.argmax(above_threshold[::-1])
            active_duration = (end_idx - start_idx) / sample_rate
        else:
            active_duration = 0.0

        # FFT for frequency analysis (simplified - just get dominant frequencies)
        fft = np.fft.rfft(audio_samples)
        freqs = np.fft.rfftfreq(len(audio_samples), 1/sample_rate)
        magnitudes = np.abs(fft)

        # Get top 5 frequencies
        top_freq_indices = np.argsort(magnitudes)[-5:]
        top_frequencies = [float(freqs[i]) for i in top_freq_indices]

        # Energy distribution (low, mid, high)
        low_band = magnitudes[freqs < 500]
        mid_band = magnitudes[(freqs >= 500) & (freqs < 2000)]
        high_band = magnitudes[freqs >= 2000]

        total_energy = np.sum(magnitudes)
        if total_energy > 0:
            low_energy = float(np.sum(low_band) / total_energy)
            mid_energy = float(np.sum(mid_band) / total_energy)
            high_energy = float(np.sum(high_band) / total_energy)
        else:
            low_energy = mid_energy = high_energy = 0.0

        return {
            "duration": float(duration),
            "active_duration": float(active_duration),
            "peak_level": peak_level,
            "mean_level": mean_level,
            "rms_profile": rms_profile[:50],  # Limit to first 500ms
            "top_frequencies": top_frequencies,
            "energy_distribution": {
                "low": low_energy,
                "mid": mid_energy,
                "high": high_energy
            }
        }

    def compare_fingerprints(self, fp1: Dict, fp2: Dict) -> float:
        """
        Compare two fingerprints and return similarity score (0-1)

        Args:
            fp1: First fingerprint
            fp2: Second fingerprint

        Returns:
            Similarity score (0 = completely different, 1 = identical)
        """
        scores = []

        # Compare active duration (must be similar)
        dur1 = fp1.get("active_duration", 0)
        dur2 = fp2.get("active_duration", 0)

        if dur1 > 0 and dur2 > 0:
            dur_diff = abs(dur1 - dur2) / max(dur1, dur2)
            dur_score = max(0, 1 - dur_diff * 2)  # More strict on duration
            scores.append(dur_score)

        # Compare peak levels
        peak1 = fp1.get("peak_level", 0)
        peak2 = fp2.get("peak_level", 0)

        if peak1 > 0 and peak2 > 0:
            peak_diff = abs(peak1 - peak2) / max(peak1, peak2)
            peak_score = max(0, 1 - peak_diff)
            scores.append(peak_score)

        # Compare RMS profiles (shape of the sound)
        rms1 = np.array(fp1.get("rms_profile", []))
        rms2 = np.array(fp2.get("rms_profile", []))

        if len(rms1) > 0 and len(rms2) > 0:
            # Normalize and compare
            min_len = min(len(rms1), len(rms2))
            rms1 = rms1[:min_len]
            rms2 = rms2[:min_len]

            # Normalize
            if np.max(rms1) > 0:
                rms1 = rms1 / np.max(rms1)
            if np.max(rms2) > 0:
                rms2 = rms2 / np.max(rms2)

            # Calculate correlation
            correlation = np.corrcoef(rms1, rms2)[0, 1]
            if not np.isnan(correlation):
                scores.append(float(correlation))

        # Compare energy distribution
        energy1 = fp1.get("energy_distribution", {})
        energy2 = fp2.get("energy_distribution", {})

        if energy1 and energy2:
            energy_diff = (
                abs(energy1.get("low", 0) - energy2.get("low", 0)) +
                abs(energy1.get("mid", 0) - energy2.get("mid", 0)) +
                abs(energy1.get("high", 0) - energy2.get("high", 0))
            ) / 3
            energy_score = max(0, 1 - energy_diff)
            scores.append(energy_score)

        # Return average score
        if scores:
            return float(np.mean(scores))
        return 0.0

    def identify_sound(self, audio_samples: np.ndarray, sample_rate: int,
                       min_confidence: float = 0.7) -> Tuple[Optional[str], float]:
        """
        Try to identify a sound by comparing with known fingerprints

        Args:
            audio_samples: Audio data
            sample_rate: Sample rate
            min_confidence: Minimum confidence to return a match

        Returns:
            Tuple of (sound_name, confidence) or (None, 0.0) if no match
        """
        # Create fingerprint for this sound
        fp = self.create_fingerprint(audio_samples, sample_rate)

        # Compare with all known fingerprints
        best_match = None
        best_score = 0.0

        for name, stored_fp in self.fingerprints.items():
            score = self.compare_fingerprints(fp, stored_fp)
            if score > best_score:
                best_score = score
                best_match = name

        if best_score >= min_confidence:
            return best_match, best_score

        return None, best_score

    def learn_sound(self, name: str, audio_samples: np.ndarray, sample_rate: int):
        """
        Learn a new sound and store its fingerprint

        Args:
            name: Name for this sound (e.g., "teams_notification")
            audio_samples: Audio data
            sample_rate: Sample rate
        """
        fp = self.create_fingerprint(audio_samples, sample_rate)

        # Add metadata
        fp["learned_at"] = datetime.now().isoformat()
        fp["sample_rate"] = sample_rate

        self.fingerprints[name] = fp
        self.save_fingerprints()

        print(f"✅ Learned sound: {name}")
        print(f"   Duration: {fp['active_duration']:.3f}s")
        print(f"   Peak level: {fp['peak_level']:.3f}")
