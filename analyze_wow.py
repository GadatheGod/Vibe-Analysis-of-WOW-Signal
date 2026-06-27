import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.stats import linregress

# ============================================================
# 1. LOAD & PARSE DATA
# ============================================================
print("=" * 60)
print("WOW! SIGNAL ANALYSIS")
print("=" * 60)

df = pd.read_csv('oseti_19770815_220410.csv', header=None)

# Separate signal data from metadata
# First 50 columns are channels, last 6 are metadata
channel_data = df.iloc[:, :50].copy()
metadata = df.iloc[:, 50:].copy()

# Convert to numeric (empty strings become NaN)
channel_data = channel_data.apply(pd.to_numeric, errors='coerce')
channel_data = channel_data.fillna(0)

# Remove header row (row 0 contains channel numbers 1-50)
channel_data = channel_data.iloc[1:].reset_index(drop=True)
metadata = metadata.iloc[1:].reset_index(drop=True)

# Time column is the last column
times = metadata.iloc[:, -1].astype(str).str.strip()

# Filter out rows where time is not valid
valid_mask = times.str.contains(r'\d{2}\s\d{2}\s\d{2}', regex=True)
times = times[valid_mask].reset_index(drop=True)
channel_data = channel_data[valid_mask].reset_index(drop=True)
metadata = metadata[valid_mask].reset_index(drop=True)

print(f"\nData loaded: {channel_data.shape[0]} time steps x {channel_data.shape[1]} channels")
print(f"Time range: {times.iloc[0]} to {times.iloc[-1]}")

# ============================================================
# 2. FIND THE WOW! SIGNAL PEAK
# ============================================================
print("\n" + "=" * 60)
print("SIGNAL PEAK DETECTION")
print("=" * 60)

# Find the row with maximum signal
max_val = channel_data.values.max()
max_row_flat = np.argmax(channel_data.values)
max_row, max_col = np.unravel_index(max_row_flat, channel_data.shape)
max_time = times.iloc[max_row]

print(f"\nPeak signal: {max_val:.1f}")
print(f"Peak channel: {max_col + 1}")
print(f"Peak time: {max_time}")
print(f"Peak coordinates: RA={metadata.iloc[max_row, 0].strip()}, Dec={metadata.iloc[max_row, 1].strip()}")

# Find all rows with significant signal (>3 sigma above background)
background = channel_data.values[~np.isclose(channel_data.values, 0)].mean()
background_std = channel_data.values[~np.isclose(channel_data.values, 0)].std()
threshold = 3 * background_std

wow_rows = []
for i in range(len(channel_data)):
    row_max = channel_data.iloc[i].max()
    if row_max > threshold:
        wow_rows.append(i)

print(f"\nBackground noise level: {background:.2f}")
print(f"Threshold (3-sigma): {threshold:.2f}")
print(f"Wow! signal detected in {len(wow_rows)} consecutive time steps")
print(f"Signal duration: {len(wow_rows) * 1.2} seconds (each step = 1.2s)")

# ============================================================
# 3. SIGNAL PROFILE ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("SIGNAL PROFILE (Channel 3)")
print("=" * 60)

# Focus on the peak channel (where the signal was detected)
peak_channel_idx = max_col
signal_profile = channel_data.iloc[:, peak_channel_idx].values

# Find the wow signal window
wow_start = min(wow_rows)
wow_end = max(wow_rows) + 1

print(f"\n--- Signal Profile (Channel {peak_channel_idx + 1}) ---")
for i in range(wow_start, wow_end):
    time_str = times.iloc[i]
    val = signal_profile[i]
    bar = '#' * int(val)
    print(f"  {time_str} | SNR: {val:5.1f} | {bar}")

# Measure rise and fall times
peak_idx = wow_rows[len(wow_rows)//2]
rise_time = (peak_idx - wow_start) * 1.2
fall_time = (wow_end - peak_idx) * 1.2

print(f"\nRise time: {rise_time:.1f} seconds")
print(f"Fall time: {fall_time:.1f} seconds")
print(f"Total duration: {(wow_end - wow_start) * 1.2:.1f} seconds")
print(f"Peak SNR: {max_val:.1f} ({max_val/background:.1f}× background)")

# ============================================================
# 4. BANDWIDTH ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("BANDWIDTH ANALYSIS")
print("=" * 60)

# Find which channels were active during the peak
peak_row = wow_rows[len(wow_rows)//2]
peak_values = channel_data.iloc[peak_row].values

active_channels = []
for i in range(50):
    if peak_values[i] > threshold:
        active_channels.append(i + 1)

print(f"\nActive channels during peak: {active_channels}")
print(f"Number of active channels: {len(active_channels)}")
print(f"Bandwidth: {len(active_channels)} channels × 10.08 kHz/channel = {len(active_channels) * 10.08:.1f} kHz")

# Frequency range
central_freq = 1420.4056  # MHz
channel_spacing = 0.01008  # MHz (10.08 kHz)
freq_start = central_freq - (25 * channel_spacing)
freq_end = freq_start + (50 * channel_spacing)

print(f"\nFrequency range: {freq_start:.4f} - {freq_end:.4f} MHz")
print(f"Central frequency: {central_freq:.4f} MHz (hydrogen line)")

# ============================================================
# 5. DOPPLER SHIFT ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("DOPPLER SHIFT ANALYSIS")
print("=" * 60)

observed_freq = 1420.726  # MHz (from 2025 reanalysis)
rest_freq = 1420.4056  # MHz (hydrogen line)
c = 299792458  # speed of light m/s

delta_f = observed_freq - rest_freq
radial_velocity = (delta_f / rest_freq) * c

print(f"\nRest frequency (hydrogen line): {rest_freq:.4f} MHz")
print(f"Observed frequency: {observed_freq:.4f} MHz")
print(f"Frequency offset: {delta_f:.3f} MHz ({delta_f * 1000:.1f} kHz)")
print(f"\nRadial velocity: {radial_velocity:.1f} m/s ({radial_velocity/1000:.3f} km/s)")

if radial_velocity > 0:
    print("Direction: Source moving TOWARD Earth")
else:
    print("Direction: Source moving AWAY from Earth")

# ============================================================
# 6. HEATMAP VISUALIZATION
# ============================================================
print("\n" + "=" * 60)
print("GENERATING VISUALIZATIONS...")
print("=" * 60)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('WOW! SIGNAL (1977) — Complete Analysis', fontsize=16, fontweight='bold')

# --- Plot 1: Full Heatmap ---
ax1 = axes[0, 0]
# Use imshow for simpler heatmap (no meshgrid needed)

im1 = ax1.pcolormesh(channel_data.values, shading='gouraud', cmap='hot')
ax1.set_xlabel('Time Step (1.2s each, ~83 steps)')
ax1.set_ylabel('Channel Number (50 total)')
ax1.set_yticks(range(0, 50, 5))
ax1.set_yticklabels(range(50, 0, -5))
ax1.set_title('Full Data: 50 Channels × 83 Time Steps\n(Heatmap of Signal Strength)')
plt.colorbar(im1, ax=ax1, label='Signal Strength (SNR)')

# Highlight wow signal region
wow_row_start = min(wow_rows)
wow_row_end = max(wow_rows) + 1
ax1.axhline(y=peak_channel_idx, color='cyan', linestyle='--', linewidth=2, label=f'Peak Channel ({peak_channel_idx+1})')
ax1.axhspan(wow_row_start - 0.5, wow_row_end - 0.5, alpha=0.2, color='yellow', label='Wow! Signal Window')
ax1.legend(loc='upper right', fontsize=8)

# --- Plot 2: Signal Profile ---
ax2 = axes[0, 1]
wow_times = times.iloc[wow_rows]
wow_vals = signal_profile[wow_rows]
wow_steps = np.arange(len(wow_rows)) * 1.2

ax2.plot(wow_steps, wow_vals, 'r-', linewidth=2, marker='o', markersize=6)
ax2.axhline(y=threshold, color='orange', linestyle='--', label=f'Threshold (3σ = {threshold:.1f})')
ax2.axhline(y=background, color='gray', linestyle=':', label=f'Background ({background:.1f})')
ax2.set_xlabel('Time (seconds from signal start)')
ax2.set_ylabel('Signal Strength (SNR)')
ax2.set_title(f'Signal Profile — Channel {peak_channel_idx + 1}\nPeak: {max_val:.1f} at {max_time}')
ax2.legend()
ax2.grid(True, alpha=0.3)

# --- Plot 3: Channel Activity During Peak ---
ax3 = axes[1, 0]
peak_values_plot = channel_data.iloc[peak_row].values
channel_nums_plot = np.arange(50) + 1

bars = ax3.bar(channel_nums_plot, peak_values_plot, color='steelblue', alpha=0.8, edgecolor='black')
bars[peak_channel_idx].set_color('red')
bars[peak_channel_idx].set_alpha(1.0)

ax3.set_xlabel('Channel Number')
ax3.set_ylabel('Signal Strength (SNR)')
ax3.set_title(f'All 50 Channels at Peak ({max_time})\nChannel {peak_channel_idx + 1} = {max_val:.1f}')
ax3.set_xticks(range(1, 51, 5))
ax3.axhline(y=threshold, color='orange', linestyle='--', label=f'Threshold ({threshold:.1f})')
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')

# --- Plot 4: Background vs Signal ---
ax4 = axes[1, 1]
non_zero = channel_data.values[~np.isclose(channel_data.values, 0)]
signal_only = channel_data.values[channel_data.values > threshold]

ax4.hist(non_zero, bins=50, alpha=0.5, color='gray', label='Background Noise (all readings)')
if len(signal_only) > 0:
    ax4.hist(signal_only, bins=30, alpha=0.7, color='red', label='Wow! Signal (above threshold)')

ax4.set_xlabel('Signal Strength (SNR)')
ax4.set_ylabel('Frequency')
ax4.set_title('Signal Distribution\nBackground vs Wow! Event')
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('wow_signal_analysis.png', dpi=150, bbox_inches='tight')
print("[OK] Saved: wow_signal_analysis.png")

# ============================================================
# 7. SUMMARY TABLE
# ============================================================
print("\n" + "=" * 60)
print("ANALYSIS SUMMARY")
print("=" * 60)

summary = f"""
==============================================================
          WOW! SIGNAL - ANALYSIS SUMMARY
==============================================================
Date:          August 15, 1977
Time:          22:09:25 EST
Duration:      ~72 seconds

Signal Peak:   {max_val:.1f} SNR ({max_val/background:.1f}x background)
Channel:       {peak_channel_idx + 1} / 50
Frequency:     {observed_freq:.4f} MHz

Doppler Shift: {delta_f:.3f} MHz ({delta_f * 1000:.1f} kHz)
Radial Vel:    {radial_velocity:.1f} m/s ({radial_velocity/1000:.3f} km/s)

Rise Time:     {rise_time:.1f} seconds
Fall Time:     {fall_time:.1f} seconds

Bandwidth:     {len(active_channels)} channels ({len(active_channels) * 10.08:.1f} kHz)
Direction:     Sagittarius (RA 19h 05m, Dec -27)

Source:        ? (Never detected again)
Confidence:    ***** (Best SETI candidate ever)
==============================================================
"""
print(summary)

print("\nAnalysis complete! Check wow_signal_analysis.png for visualizations.")
