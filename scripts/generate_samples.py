#!/usr/bin/env python3
"""Generate sample renders showcasing GeekMagic display layouts and widgets.

Usage:
    uv run python scripts/generate_samples.py

Outputs PNG images to the samples/ directory.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add the custom_components to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.geekmagic.const import (
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_YELLOW,
)
from custom_components.geekmagic.layouts.grid import Grid2x2, Grid2x3
from custom_components.geekmagic.layouts.hero import HeroLayout
from custom_components.geekmagic.layouts.split import SplitLayout
from custom_components.geekmagic.renderer import Renderer
from custom_components.geekmagic.widgets.base import WidgetConfig
from custom_components.geekmagic.widgets.chart import ChartWidget
from custom_components.geekmagic.widgets.clock import ClockWidget
from custom_components.geekmagic.widgets.entity import EntityWidget
from custom_components.geekmagic.widgets.media import MediaWidget
from custom_components.geekmagic.widgets.text import TextWidget


@dataclass
class MockState:
    """Mock Home Assistant entity state."""

    state: str
    attributes: dict[str, Any]
    entity_id: str = ""


@dataclass
class MockStates:
    """Mock Home Assistant states registry."""

    _states: dict[str, MockState]

    def get(self, entity_id: str) -> MockState | None:
        return self._states.get(entity_id)


@dataclass
class MockConfig:
    """Mock Home Assistant config."""

    time_zone_obj: Any = None


@dataclass
class MockHass:
    """Mock Home Assistant instance."""

    states: MockStates
    config: MockConfig


def create_mock_hass() -> MockHass:
    """Create a mock Home Assistant with sample entity states."""
    states = {
        "sensor.temperature": MockState(
            state="21.5",
            attributes={"unit_of_measurement": "°C", "friendly_name": "Temperature"},
            entity_id="sensor.temperature",
        ),
        "sensor.humidity": MockState(
            state="65",
            attributes={"unit_of_measurement": "%", "friendly_name": "Humidity"},
            entity_id="sensor.humidity",
        ),
        "sensor.cpu_usage": MockState(
            state="42",
            attributes={"unit_of_measurement": "%", "friendly_name": "CPU Usage"},
            entity_id="sensor.cpu_usage",
        ),
        "sensor.memory": MockState(
            state="8.2",
            attributes={"unit_of_measurement": "GB", "friendly_name": "Memory"},
            entity_id="sensor.memory",
        ),
        "sensor.power": MockState(
            state="156",
            attributes={"unit_of_measurement": "W", "friendly_name": "Power"},
            entity_id="sensor.power",
        ),
        "sensor.solar": MockState(
            state="2.4",
            attributes={"unit_of_measurement": "kW", "friendly_name": "Solar"},
            entity_id="sensor.solar",
        ),
        "media_player.spotify": MockState(
            state="playing",
            attributes={
                "friendly_name": "Spotify",
                "media_title": "Bohemian Rhapsody",
                "media_artist": "Queen",
                "media_album_name": "A Night at the Opera",
                "media_position": 125,
                "media_duration": 354,
            },
            entity_id="media_player.spotify",
        ),
    }
    return MockHass(states=MockStates(_states=states), config=MockConfig())


def save_image(renderer: Renderer, img, name: str, output_dir: Path) -> None:
    """Save image as PNG."""
    output_path = output_dir / f"{name}.png"
    png_data = renderer.to_png(img)
    output_path.write_bytes(png_data)
    print(f"  ✓ {output_path}")


def generate_clock_sample(renderer: Renderer, output_dir: Path) -> None:
    """Generate clock widget sample."""
    img, draw = renderer.create_canvas()

    widget = ClockWidget(WidgetConfig(widget_type="clock", slot=0, options={"show_date": True}))
    widget.render(renderer, draw, (0, 0, 240, 240), hass=None)

    save_image(renderer, img, "01_clock", output_dir)


def generate_grid_2x2_sample(renderer: Renderer, hass: MockHass, output_dir: Path) -> None:
    """Generate 2x2 grid with mixed widgets."""
    layout = Grid2x2()

    # Add widgets
    layout.set_widget(
        0,
        ClockWidget(WidgetConfig(widget_type="clock", slot=0, options={"show_date": False})),
    )
    layout.set_widget(
        1,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=1,
                entity_id="sensor.temperature",
                color=COLOR_CYAN,
            )
        ),
    )
    layout.set_widget(
        2,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=2,
                entity_id="sensor.humidity",
                color=COLOR_GREEN,
            )
        ),
    )
    layout.set_widget(
        3,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=3,
                entity_id="sensor.power",
                color=COLOR_YELLOW,
            )
        ),
    )

    img, draw = renderer.create_canvas()
    layout.render(renderer, draw, hass)  # type: ignore[arg-type]

    save_image(renderer, img, "02_grid_2x2", output_dir)


def generate_grid_2x3_sample(renderer: Renderer, hass: MockHass, output_dir: Path) -> None:
    """Generate 2x3 grid with entity widgets."""
    layout = Grid2x3()

    entities = [
        ("sensor.temperature", COLOR_CYAN),
        ("sensor.humidity", COLOR_GREEN),
        ("sensor.cpu_usage", COLOR_YELLOW),
        ("sensor.memory", COLOR_CYAN),
        ("sensor.power", COLOR_RED),
        ("sensor.solar", COLOR_GREEN),
    ]

    for i, (entity_id, color) in enumerate(entities):
        layout.set_widget(
            i,
            EntityWidget(
                WidgetConfig(
                    widget_type="entity",
                    slot=i,
                    entity_id=entity_id,
                    color=color,
                )
            ),
        )

    img, draw = renderer.create_canvas()
    layout.render(renderer, draw, hass)  # type: ignore[arg-type]

    save_image(renderer, img, "03_grid_2x3", output_dir)


def generate_hero_sample(renderer: Renderer, hass: MockHass, output_dir: Path) -> None:
    """Generate hero layout with clock and entity widgets."""
    layout = HeroLayout()

    # Hero slot: Clock
    layout.set_widget(
        0,
        ClockWidget(WidgetConfig(widget_type="clock", slot=0, options={"show_date": True})),
    )

    # Footer slots: Entities
    layout.set_widget(
        1,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=1,
                entity_id="sensor.temperature",
                color=COLOR_CYAN,
            )
        ),
    )
    layout.set_widget(
        2,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=2,
                entity_id="sensor.humidity",
                color=COLOR_GREEN,
            )
        ),
    )
    layout.set_widget(
        3,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=3,
                entity_id="sensor.power",
                color=COLOR_YELLOW,
            )
        ),
    )

    img, draw = renderer.create_canvas()
    layout.render(renderer, draw, hass)  # type: ignore[arg-type]

    save_image(renderer, img, "04_hero_layout", output_dir)


def generate_split_sample(renderer: Renderer, hass: MockHass, output_dir: Path) -> None:
    """Generate split layout."""
    layout = SplitLayout(horizontal=False, ratio=0.5)

    layout.set_widget(
        0,
        ClockWidget(WidgetConfig(widget_type="clock", slot=0, options={"show_date": True})),
    )
    layout.set_widget(
        1,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=1,
                entity_id="sensor.temperature",
                color=COLOR_CYAN,
            )
        ),
    )

    img, draw = renderer.create_canvas()
    layout.render(renderer, draw, hass)  # type: ignore[arg-type]

    save_image(renderer, img, "05_split_layout", output_dir)


def generate_media_sample(renderer: Renderer, hass: MockHass, output_dir: Path) -> None:
    """Generate media player widget sample."""
    img, draw = renderer.create_canvas()

    widget = MediaWidget(
        WidgetConfig(
            widget_type="media",
            slot=0,
            entity_id="media_player.spotify",
            options={"show_artist": True, "show_progress": True},
        )
    )
    widget.render(renderer, draw, (0, 0, 240, 240), hass)  # type: ignore[arg-type]

    save_image(renderer, img, "06_media_player", output_dir)


def generate_chart_sample(renderer: Renderer, hass: MockHass, output_dir: Path) -> None:
    """Generate chart widget with sample data."""
    img, draw = renderer.create_canvas()

    widget = ChartWidget(
        WidgetConfig(
            widget_type="chart",
            slot=0,
            entity_id="sensor.temperature",
            label="Temperature",
            color=COLOR_CYAN,
            options={"show_value": True, "show_range": True},
        )
    )

    # Set sample history data (simulated temperature over 24h)
    sample_data = [
        18.5,
        18.2,
        17.8,
        17.5,
        17.2,
        17.0,
        17.5,
        18.0,
        19.0,
        20.0,
        21.0,
        21.5,
        22.0,
        22.5,
        22.8,
        22.5,
        22.0,
        21.5,
        21.0,
        20.5,
        20.0,
        19.5,
        19.0,
        18.5,
    ]
    widget.set_history(sample_data)

    widget.render(renderer, draw, (0, 0, 240, 240), hass)  # type: ignore[arg-type]

    save_image(renderer, img, "07_chart", output_dir)


def generate_text_sample(renderer: Renderer, output_dir: Path) -> None:
    """Generate text widget sample."""
    layout = Grid2x2()

    layout.set_widget(
        0,
        TextWidget(
            WidgetConfig(
                widget_type="text",
                slot=0,
                label="Status",
                options={"text": "Online", "size": "large"},
                color=COLOR_GREEN,
            )
        ),
    )
    layout.set_widget(
        1,
        TextWidget(
            WidgetConfig(
                widget_type="text",
                slot=1,
                label="Mode",
                options={"text": "Auto", "size": "large"},
                color=COLOR_CYAN,
            )
        ),
    )
    layout.set_widget(
        2,
        TextWidget(
            WidgetConfig(
                widget_type="text",
                slot=2,
                label="Alert",
                options={"text": "None", "size": "large"},
                color=COLOR_YELLOW,
            )
        ),
    )
    layout.set_widget(
        3,
        TextWidget(
            WidgetConfig(
                widget_type="text",
                slot=3,
                label="Network",
                options={"text": "OK", "size": "large"},
                color=COLOR_GREEN,
            )
        ),
    )

    img, draw = renderer.create_canvas()
    layout.render(renderer, draw, None)

    save_image(renderer, img, "08_text_widgets", output_dir)


def generate_dashboard_sample(renderer: Renderer, hass: MockHass, output_dir: Path) -> None:
    """Generate a complete dashboard sample."""
    layout = HeroLayout(hero_ratio=0.6)

    # Hero: Media player
    layout.set_widget(
        0,
        MediaWidget(
            WidgetConfig(
                widget_type="media",
                slot=0,
                entity_id="media_player.spotify",
                options={"show_artist": True, "show_progress": True},
            )
        ),
    )

    # Footer: Status indicators
    layout.set_widget(
        1,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=1,
                entity_id="sensor.temperature",
                color=COLOR_CYAN,
            )
        ),
    )
    layout.set_widget(
        2,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=2,
                entity_id="sensor.humidity",
                color=COLOR_GREEN,
            )
        ),
    )
    layout.set_widget(
        3,
        EntityWidget(
            WidgetConfig(
                widget_type="entity",
                slot=3,
                entity_id="sensor.power",
                color=COLOR_YELLOW,
            )
        ),
    )

    img, draw = renderer.create_canvas()
    layout.render(renderer, draw, hass)  # type: ignore[arg-type]

    save_image(renderer, img, "09_dashboard", output_dir)


def main() -> None:
    """Generate all sample renders."""
    output_dir = Path(__file__).parent.parent / "samples"
    output_dir.mkdir(exist_ok=True)

    print("Generating sample renders...")
    print(f"Output directory: {output_dir}\n")

    renderer = Renderer()
    hass = create_mock_hass()

    # Generate samples
    generate_clock_sample(renderer, output_dir)
    generate_grid_2x2_sample(renderer, hass, output_dir)
    generate_grid_2x3_sample(renderer, hass, output_dir)
    generate_hero_sample(renderer, hass, output_dir)
    generate_split_sample(renderer, hass, output_dir)
    generate_media_sample(renderer, hass, output_dir)
    generate_chart_sample(renderer, hass, output_dir)
    generate_text_sample(renderer, output_dir)
    generate_dashboard_sample(renderer, hass, output_dir)

    print(f"\n✓ Generated 9 sample images in {output_dir}/")


if __name__ == "__main__":
    main()
