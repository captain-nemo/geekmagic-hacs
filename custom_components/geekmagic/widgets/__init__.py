"""Widget components for GeekMagic displays."""

from .base import Widget, WidgetConfig
from .chart import ChartWidget
from .clock import ClockWidget
from .entity import EntityWidget
from .gauge import GaugeWidget
from .media import MediaWidget
from .progress import MultiProgressWidget, ProgressWidget
from .status import StatusListWidget, StatusWidget
from .text import TextWidget
from .weather import WeatherWidget

__all__ = [
    "ChartWidget",
    "ClockWidget",
    "EntityWidget",
    "GaugeWidget",
    "MediaWidget",
    "MultiProgressWidget",
    "ProgressWidget",
    "StatusListWidget",
    "StatusWidget",
    "TextWidget",
    "WeatherWidget",
    "Widget",
    "WidgetConfig",
]
