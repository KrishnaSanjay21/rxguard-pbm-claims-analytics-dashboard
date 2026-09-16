import plotly.graph_objects as go

from rxguard.config import COLORS


def finish(fig: go.Figure, *, x_title: str | None = None, y_title: str | None = None, percent_y: bool = False) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font={"family": "Arial", "color": COLORS["navy"]},
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        hoverlabel={"bgcolor": "white", "font_size": 12},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    fig.update_xaxes(title=x_title, gridcolor="#EDF2F7")
    fig.update_yaxes(title=y_title, gridcolor="#EDF2F7", tickformat=".0%" if percent_y else None)
    return fig
