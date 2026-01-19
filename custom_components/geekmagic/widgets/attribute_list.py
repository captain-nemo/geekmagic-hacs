"""Attribute list widget for GeekMagic displays."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..const import COLOR_CYAN, PLACEHOLDER_NAME, PLACEHOLDER_VALUE
from .base import Widget, WidgetConfig
from .components import (
    THEME_TEXT_SECONDARY,
    Color,
    Column,
    Component,
    Row,
    Spacer,
    Text,
)
from .helpers import estimate_max_chars, truncate_text

if TYPE_CHECKING:
    from ..render_context import RenderContext
    from .state import WidgetState


@dataclass
class AttributeListDisplay(Component):
    """Attribute list display component."""

    items: list[tuple[str, str, Color]] = field(default_factory=list)  # (label, value, color)
    title: str | None = None

    def measure(self, ctx: RenderContext, max_width: int, max_height: int) -> tuple[int, int]:
        return (max_width, max_height)

    def render(self, ctx: RenderContext, x: int, y: int, width: int, height: int) -> None:
        """Render attribute list using component primitives."""
        padding = int(width * 0.05)

        # Build list of rows
        rows: list[Component] = []

        # Add title if provided
        if self.title:
            rows.append(
                Text(
                    text=self.title.upper(),
                    font="small",
                    color=THEME_TEXT_SECONDARY,
                    align="start",
                )
            )

        # Estimate max characters for label and value
        max_label_len = estimate_max_chars(width // 2, char_width=7, padding=10)
        max_value_len = estimate_max_chars(width // 2, char_width=7, padding=10)

        # Build each item row
        for label, value, color in self.items:
            display_label = truncate_text(label, max_label_len, style="end")
            display_value = truncate_text(str(value), max_value_len, style="end")

            # Build row: Label ... Value
            row_children = [
                Text(text=display_label, font="small", color=THEME_TEXT_SECONDARY, align="start"),
                Spacer(),
                Text(text=display_value, font="small", color=color, align="end", bold=True),
            ]

            rows.append(
                Row(
                    children=row_children,
                    gap=6,
                    align="center",
                    justify="start",
                )
            )

        # Render all rows in a column
        Column(
            children=rows,
            gap=4 if self.title else 2,
            padding=padding,
            align="stretch",
            justify="start",
        ).render(ctx, x, y, width, height)


class AttributeListWidget(Widget):
    """Widget that displays a list of entity attributes as key-value pairs.

    Configuration example:
        widget:
          type: attribute_list
          entity_id: sensor.bus_arrival
          options:
            title: "Bus Info"
            attributes:
              - key: route_name
                label: "Route"
              - key: destination
                label: "To"
              - key: state
                label: "Arrives"
    """

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the attribute list widget."""
        super().__init__(config)
        self.attributes = config.options.get("attributes", [])
        self.title = config.options.get("title")

    def render(self, ctx: RenderContext, state: WidgetState) -> Component:
        """Render the attribute list widget."""
        entity = state.entity
        color = self.config.color or COLOR_CYAN

        items: list[tuple[str, str, Color]] = []

        for attr_config in self.attributes:
            # Support both dict format and simple string format
            if isinstance(attr_config, dict):
                key = attr_config.get("key", "")
                label = attr_config.get("label", key)
                item_color = attr_config.get("color", color)
                if isinstance(item_color, list):
                    item_color = tuple(item_color)
            else:
                # Simple string format: use attribute name as both key and label
                key = str(attr_config)
                label = key
                item_color = color

            # Get value from entity
            if entity is None:
                value = PLACEHOLDER_VALUE
            elif key == "state":
                # Special case: "state" refers to entity state, not an attribute
                value = entity.state
            else:
                raw_value = entity.get(key)
                value = self._format_value(raw_value)

            items.append((label, value, item_color))

        # If no attributes configured, show friendly name as title
        title = self.title
        if not title and entity:
            title = entity.friendly_name
        elif not title:
            title = self.config.entity_id or PLACEHOLDER_NAME

        return AttributeListDisplay(
            items=items,
            title=title if not self.attributes else self.title,
        )

    def _format_value(self, value: Any) -> str:
        """Format attribute value for display."""
        if value is None:
            return PLACEHOLDER_VALUE
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, float):
            # Format floats with reasonable precision
            return str(int(value)) if value == int(value) else f"{value:.1f}"
        if isinstance(value, list):
            return f"[{len(value)} items]"
        if isinstance(value, dict):
            return f"{{{len(value)} keys}}"
        return str(value)
