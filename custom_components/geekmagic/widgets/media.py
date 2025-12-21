"""Media player widget for GeekMagic displays."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..const import COLOR_CYAN
from .base import Widget, WidgetConfig
from .components import (
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
    Bar,
    Color,
    Column,
    Component,
    Icon,
    Row,
    Spacer,
    Text,
)

if TYPE_CHECKING:
    from ..render_context import RenderContext
    from .state import WidgetState


def _format_time(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    seconds = int(seconds)
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


@dataclass
class NowPlaying(Component):
    """Now playing display component."""

    title: str
    artist: str = ""
    album: str = ""
    position: float = 0
    duration: float = 0
    color: Color = COLOR_CYAN
    show_artist: bool = True
    show_album: bool = False
    show_progress: bool = True

    def measure(self, ctx: RenderContext, max_width: int, max_height: int) -> tuple[int, int]:
        return (max_width, max_height)

    def render(self, ctx: RenderContext, x: int, y: int, width: int, height: int) -> None:
        """Render now playing info."""
        padding = int(width * 0.05)

        # Truncate text
        max_chars = (width - padding * 2) // 8
        title = self.title[: max_chars - 2] + ".." if len(self.title) > max_chars else self.title
        artist = (
            self.artist[: max_chars - 2] + ".." if len(self.artist) > max_chars else self.artist
        )
        album = self.album[: max_chars - 2] + ".." if len(self.album) > max_chars else self.album

        # Build component tree
        children = [
            Text("NOW PLAYING", font="small", color=THEME_TEXT_SECONDARY),
            Spacer(min_size=int(height * 0.03)),
            Text(title, font="regular", color=THEME_TEXT_PRIMARY),
        ]

        if self.show_artist and artist:
            children.append(Spacer(min_size=int(height * 0.02)))
            children.append(Text(artist, font="small", color=THEME_TEXT_SECONDARY))

        if self.show_album and self.album:
            children.append(Spacer(min_size=int(height * 0.02)))
            children.append(Text(album, font="small", color=THEME_TEXT_SECONDARY))

        # Add spacer before progress section
        children.append(Spacer())

        # Progress bar and time labels
        if self.show_progress and self.duration > 0:
            progress = min(100, (self.position / self.duration) * 100)
            pos_str = _format_time(self.position)
            dur_str = _format_time(self.duration)

            children.extend(
                [
                    Bar(
                        percent=progress,
                        color=self.color,
                        height=max(4, int(height * 0.05)),
                    ),
                    Spacer(min_size=int(height * 0.02)),
                    Row(
                        children=[
                            Text(pos_str, font="small", color=THEME_TEXT_SECONDARY, align="start"),
                            Spacer(),
                            Text(dur_str, font="small", color=THEME_TEXT_SECONDARY, align="end"),
                        ]
                    ),
                ]
            )

        # Render the column
        Column(children=children, padding=padding, align="center").render(ctx, x, y, width, height)


@dataclass
class MediaIdle(Component):
    """Idle/paused state display."""

    def measure(self, ctx: RenderContext, max_width: int, max_height: int) -> tuple[int, int]:
        return (max_width, max_height)

    def render(self, ctx: RenderContext, x: int, y: int, width: int, height: int) -> None:
        """Render paused state."""
        # Calculate icon size
        icon_size = max(24, int(height * 0.25))

        # Build component tree
        Column(
            children=[
                Icon("pause", size=icon_size, color=THEME_TEXT_SECONDARY),
                Spacer(min_size=int(height * 0.08)),
                Text("PAUSED", font="small", color=THEME_TEXT_SECONDARY),
            ],
            align="center",
            justify="center",
        ).render(ctx, x, y, width, height)


class MediaWidget(Widget):
    """Widget that displays media player information."""

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the media widget."""
        super().__init__(config)
        self.show_artist = config.options.get("show_artist", True)
        self.show_album = config.options.get("show_album", False)
        self.show_progress = config.options.get("show_progress", True)

    def render(self, ctx: RenderContext, state: WidgetState) -> Component:
        """Render the media player widget.

        Args:
            ctx: RenderContext for drawing
            state: Widget state with entity data
        """
        entity = state.entity

        if entity is None or entity.state in ("off", "unavailable", "unknown", "idle"):
            return MediaIdle()

        return NowPlaying(
            title=entity.get("media_title", "Unknown"),
            artist=entity.get("media_artist", ""),
            album=entity.get("media_album_name", ""),
            position=entity.get("media_position", 0),
            duration=entity.get("media_duration", 0),
            color=self.config.color or COLOR_CYAN,
            show_artist=self.show_artist,
            show_album=self.show_album,
            show_progress=self.show_progress,
        )
