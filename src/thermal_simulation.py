"""Thermal heatmap analysis and HVAC cooling convergence simulation."""

import os
import numpy as np
import matplotlib.pyplot as plt
from bitmap_utils import read_bmp

DATA_PATH = os.path.join("data", "thermal_room_1.bmp")
RESULTS_DIR = "results"


def rgb_to_temperature_grid(
    pixels: list[list[tuple[int, int, int]]],
    min_temp: float = 18.0,
    max_temp: float = 35.0,
) -> np.ndarray:
    """Convert a 2D RGB pixel grid into an estimated room temperature matrix (°C)."""
    rgb_arr = np.array(pixels, dtype=np.float64)
    intensity = (0.6 * rgb_arr[:, :, 0] + 0.3 * rgb_arr[:, :, 1] + 0.1 * (255.0 - rgb_arr[:, :, 2])) / 255.0
    return min_temp + intensity * (max_temp - min_temp)


def simulate_cooling(
    temp_grid: np.ndarray,
    target_temp: float = 21.0,
    total_minutes: int = 30,
    step_minutes: int = 5,
) -> tuple[list[int], list[float], list[float], list[float], dict[int, np.ndarray]]:
    """Simulate progressive thermal convergence toward a target HVAC setpoint."""
    time_steps = list(range(0, total_minutes + 1, step_minutes))
    min_temps, max_temps, mean_temps = [], [], []
    snapshots: dict[int, np.ndarray] = {}

    for t in time_steps:
        alpha = t / total_minutes
        current_grid = temp_grid + alpha * (target_temp - temp_grid)
        min_temps.append(float(np.min(current_grid)))
        max_temps.append(float(np.max(current_grid)))
        mean_temps.append(float(np.mean(current_grid)))
        if t in {0, 10, 20, 30}:
            snapshots[t] = current_grid

    return time_steps, min_temps, max_temps, mean_temps, snapshots


def run_simulation(bmp_path: str = DATA_PATH, target_temp: float = 21.0, duration_min: int = 30) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    bmp = read_bmp(bmp_path)
    print(f"Loaded BMP ({bmp.width}x{bmp.height}, {bmp.bits_per_pixel}-bit)")

    temp_grid = rgb_to_temperature_grid(bmp.pixels)
    times, min_t, max_t, mean_t, snapshots = simulate_cooling(
        temp_grid, target_temp=target_temp, total_minutes=duration_min
    )

    # 1. Save 4-panel thermal progression across time intervals (0, 10, 20, 30 min)
    fig, axes = plt.subplots(1, 4, figsize=(15, 4), constrained_layout=True)
    vmin, vmax = float(np.min(temp_grid)), float(np.max(temp_grid))

    for ax, (t, grid) in zip(axes, sorted(snapshots.items())):
        im = ax.imshow(grid, cmap="inferno", vmin=vmin, vmax=vmax)
        ax.set_title(f"t = {t} min\n(Mean: {np.mean(grid):.1f}°C)")
        ax.axis("off")

    fig.colorbar(im, ax=axes, shrink=0.85, label="Estimated Temperature (°C)")
    fig.suptitle("Spatial Thermal Cooling Progression Over 30 Minutes", fontsize=13)
    plt.savefig(os.path.join(RESULTS_DIR, "thermal_progression.png"), dpi=150)
    plt.close()

    # 2. Save temperature convergence curve over time
    plt.figure(figsize=(7, 4.5))
    plt.plot(times, max_t, marker="o", color="crimson", label="Max Room Temp (°C)")
    plt.plot(times, mean_t, marker="s", color="darkorange", label="Mean Room Temp (°C)")
    plt.plot(times, min_t, marker="^", color="royalblue", label="Min Room Temp (°C)")
    plt.axhline(target_temp, linestyle="--", color="gray", label=f"Target Setpoint ({target_temp}°C)")
    plt.xlabel("Elapsed Time (minutes)")
    plt.ylabel("Temperature (°C)")
    plt.title("IoT Thermal Regulation Convergence Over Time")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "cooling_convergence.png"), dpi=150)
    plt.close()

    print(f"Saved plots to {RESULTS_DIR}/ (Initial Mean: {mean_t[0]:.2f}°C -> Final Mean: {mean_t[-1]:.2f}°C)")


if __name__ == "__main__":
    run_simulation()
