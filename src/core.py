import re
import html
import pyqtgraph as pg
import numpy as np
from pyqtgraph import GraphicsLayoutWidget


class Canvas:
    pen_pool = {
        "Lblue": pg.mkPen(color=(50, 200, 200), width=4),
        "blue": pg.mkPen(color=(50, 130, 200), width=4),
        "red": pg.mkPen(color=(220, 60, 60), width=4),
        "green": pg.mkPen(color=(75, 220, 90), width=4),
        "gray": pg.mkPen(
            color=(150, 150, 150),
            width=3,
            style=pg.QtCore.Qt.PenStyle.DashLine,
        ),
    }

    def __init__(self, width: int = 800, height: int = 600) -> None:
        self.app = pg.mkQApp()
        self.w: GraphicsLayoutWidget = GraphicsLayoutWidget()
        self.w.resize(width, height)
        self._base_width = width
        self._base_height = height
        self._panel_pad = 70
        self._label_h = 24
        # Square area allocated per plot panel.
        self._panel_side = max(260, min(width, height - self._panel_pad - self._label_h))
        self.w.setBackground((30, 30, 30))
        self.w.setVerticalScrollBarPolicy(pg.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.w.setHorizontalScrollBarPolicy(pg.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        pg.setConfigOptions(antialias=True)

        self.default_pen = self.pen_pool["Lblue"]
        self.counter = 0
        self.fps = 0
        self.last_fps = 0

        self._panels: list[dict] = []
        self.funcs: list[dict] = []
        self.lines: list = []
        self.error_lines: list = []
        self.series: list = []

        self.plot = self.add_plot(title="Function", lock_aspect=True)
        self.error_plot = None

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

        self._fps_timer = pg.QtCore.QTimer()
        self._fps_timer.timeout.connect(self._refresh_fps)
        self._fps_timer.start(1000)

        self.w.show()

    def _update_window_size(self):
        # Keep each panel visually equal and close to 1:1.
        count = max(1, len(self._panels))
        target_h = self._panel_side + self._panel_pad + self._label_h
        target_w = count * self._panel_side + self._panel_pad

        # Do not shrink below constructor defaults.
        target_w = max(target_w, self._base_width)
        target_h = max(target_h, self._base_height)
        self.w.resize(target_w, target_h)

    def _panel_for_plot(self, plot: pg.PlotItem):
        for panel in self._panels:
            if panel["plot"] is plot:
                return panel
        return None

    def _resolve_plot(self, plot: pg.PlotItem | None = None, index: int | None = None):
        if plot is not None:
            return plot
        if index is not None:
            return self._panels[index]["plot"]
        return self.plot

    def add_plot(
        self,
        title: str = "Plot",
        label_text: str | None = None,
        lock_aspect: bool = False,
        show_grid: bool = True,
    ):
        col = len(self._panels)
        panel_layout = self.w.addLayout(row=0, col=col)

        header = label_text if label_text is not None else ""
        panel_label = panel_layout.addLabel(
            f'<span style="color:#e6e6e6; font-size:12pt;">{header}</span>'
        )
        panel_label.setMinimumHeight(24)
        panel_label.setMaximumHeight(24)
        panel_layout.nextRow()

        plot = panel_layout.addPlot()
        plot.setTitle(title)
        if show_grid:
            self.show_grid(True, plot)

        self.show_axis_line(True, plot)

        plot.getAxis("left").setStyle(autoExpandTextSpace=False, autoReduceTextSpace=False)
        plot.getAxis("bottom").setStyle(autoExpandTextSpace=False, autoReduceTextSpace=False)
        plot.getAxis("left").setWidth(70)
        plot.getAxis("bottom").setHeight(45)
        plot.getViewBox().setMouseEnabled(x=True, y=True)
        plot.getViewBox().enableAutoRange(enable=False)
        if lock_aspect:
            plot.getViewBox().setAspectLocked(True)

        info = {}
        if len(self._panels) == 0:
            info["FPS"] = "0"

        panel = {
            "layout": panel_layout,
            "label": panel_label,
            "plot": plot,
            "max_label_len": 0,
            "info": info,
            "last_text": None,
        }
        self._panels.append(panel)
        self._update_window_size()
        self._render_panel_info(panel)
        return plot
    
    def show_axis_line(self, show: bool = True, plot: pg.PlotItem | None = None):
        '''Показать/скрыть оси X=0 и Y=0 на указанном графике (или на главном, если не указано)'''
        target = self._resolve_plot(plot)
        if show:
            self.x0 = pg.InfiniteLine(
                pos=0,
                angle=0,           # горизонтальная
                pen=pg.mkPen((150, 150, 150), width=2)
            )
            self.y0 = pg.InfiniteLine(
                pos=0,
                angle=90,          # вертикальная
                pen=pg.mkPen((150, 150, 150), width=2)
            )
            target.addItem(self.x0, ignoreBounds=True)
            target.addItem(self.y0, ignoreBounds=True)
        else:
            target.removeItem(self.x0)
            target.removeItem(self.y0)
    
    def show_grid(self, show: bool = True, plot: pg.PlotItem | None = None):
        '''Показать/скрыть сетку на указанном графике (или на главном, если не указано)'''
        target = self._resolve_plot(plot)
        if show:
            target.showGrid(x=True, y=True, alpha=0.6)
        else:
            target.showGrid(x=False, y=False)

    def show_coord_panel(
        self,
        show: bool = True,
        plot: pg.PlotItem | None = None,
    ):
        """Show/hide coordinate axis panels on the right and bottom."""
        target = self._resolve_plot(plot)

        target.showAxis("left", show=show)
        target.showAxis("bottom", show=show)

    def get_plot(self, index: int = 0):
        return self._panels[index]["plot"]

    def _render_panel_info(self, panel: dict):
        text = " ".join([f"{k} {v}" for k, v in panel["info"].items()])
        if panel["last_text"] == text:
            return
        panel["last_text"] = text
        panel["max_label_len"] = max(panel["max_label_len"], len(text))
        padded = text.ljust(panel["max_label_len"])
        safe = html.escape(padded).replace(" ", "&nbsp;")
        panel["label"].setText(
            f'<span style="color:#e6e6e6; font-size:12pt; font-family:Consolas, monospace;">{safe}</span>'
        )

    def set_plot_label(self, text: str, plot: pg.PlotItem | None = None):
        target = self._resolve_plot(plot)
        panel = self._panel_for_plot(target)
        if panel is not None:
            panel["info"]["INFO"] = text
            self._render_panel_info(panel)

    def update(self):
        for item in self.funcs:
            f = item["expr"]
            plot = item["plot"]
            curve = item["curve"]
            last_range = item["last_range"]
            last_version = item["last_version"]

            x_range, _ = plot.viewRange()  # type: ignore
            curr_range = (x_range[0], x_range[1])
            same_range = (
                last_range is not None
                and np.isclose(curr_range[0], last_range[0], rtol=1e-6, atol=1e-6)
                and np.isclose(curr_range[1], last_range[1], rtol=1e-6, atol=1e-6)
            )
            if same_range and last_version == f.version:
                continue

            scale = (x_range[1] - x_range[0]) * 0.5
            view_px = max(200, int(plot.getViewBox().width()))
            samples = min(1200, max(300, view_px))
            x = np.linspace(x_range[0] - scale, x_range[1] + scale, samples)
            y = f.fx(x)

            if f.render_from is not None:
                mask = x >= f.render_from
                curve.setData(x[mask], y[mask])
            else:
                curve.setData(x, y)
            item["last_range"] = curr_range
            item["last_version"] = f.version

        self.fps += 1

    def add_func(
        self,
        func: str,
        color: str | None = None,
        fr: float | None = None,
        plot: pg.PlotItem | None = None,
    ):
        target = self._resolve_plot(plot)
        expr = Expr(func, fr)

        if color:
            pen = self.pen_pool.get(color)
        else:
            key = list(self.pen_pool.keys())[len(self.funcs) % len(self.pen_pool)]
            pen = self.pen_pool[key]

        if not pen:
            print(f"\033[31mStyle '{color}' not found\033[0m")
            pen = self.default_pen

        curve = target.plot([], [], pen=pen)
        curve.setClipToView(True)
        curve.setDownsampling(auto=True, method="peak")
        self.funcs.append(
            {
                "expr": expr,
                "curve": curve,
                "plot": target,
                "last_range": None,
                "last_version": -1,
            }
        )
        self.series.append(curve)
        return expr

    def update_func(self, func, new_func, color: str | None = None):
        for item in self.funcs:
            if item["expr"] is func:
                item["expr"].update_expr(new_func)

    def add_series(self, color: str | None = None, plot: pg.PlotItem | None = None):
        target = self._resolve_plot(plot)
        pen = self.pen_pool.get(color) if color else self.default_pen
        if not pen:
            pen = self.default_pen
        line = target.plot([], [], pen=pen)
        line.setClipToView(True)
        line.setDownsampling(auto=True, method="peak")
        self.series.append(line)
        return line

    def update_plot(self, item, x, y):
        if np.isscalar(x):
            x = [x]
        if np.isscalar(y):
            y = [y]
        item.setData(x, y)

    def add_unit_circle(self, plot: pg.PlotItem | None = None):
        target = self._resolve_plot(plot)
        a = np.linspace(0, 2 * np.pi, 100)
        target.plot(np.sin(a), np.cos(a), pen=self.default_pen)

    def add_point(self, x, y, color="w", size=0.05, plot: pg.PlotItem | None = None):
        target = self._resolve_plot(plot)
        point = pg.ScatterPlotItem([x], [y], pen=None, brush=color, size=size, pxMode=False)
        target.addItem(point)
        point.setZValue(100000)
        self.lines.append(point)
        self.series.append(point)
        return point

    def update_point(self, pt, x, y):
        self.update_plot(pt, x, y)

    def update_animation(self):
        a = (self.counter / 5) * (2 * np.pi / 360)
        s, c = np.sin(a), np.cos(a)
        self.lines[0].setData([c], [s])
        self.lines[1].setData([c, c], [0, s])
        self.lines[2].setData([0, c], [s, s])
        self.lines[3].setData([0, c], [0, s])

    def log_fps(self, flag=True):
        self.log_timer = pg.QtCore.QTimer()
        self.log_timer.timeout.connect(self._print_fps)
        self.log_timer.start(1000)
        self.fps = 0

    def _refresh_fps(self):
        fps_value = self.fps
        self.last_fps = fps_value
        self.fps = 0
        if self._panels:
            first = self._panels[0]
            first["info"]["FPS"] = str(fps_value)
            self._render_panel_info(first)

    def set_camera_x(self, x_st=-1, x_end=1, plot: pg.PlotItem | None = None, index: int | None = None):
        vb = self._resolve_plot(plot, index).getViewBox()
        vb.setXRange(x_st, x_end, padding=0)

    def set_camera_y(self, y_st=-1, y_end=1, plot: pg.PlotItem | None = None, index: int | None = None):
        vb = self._resolve_plot(plot, index).getViewBox()
        vb.setYRange(y_st, y_end, padding=0)

    def set_autorange(self, enabled=True, plot: pg.PlotItem | None = None, index: int | None = None):
        target = self._resolve_plot(plot, index)
        vb = target.getViewBox()
        vb.enableAutoRange(x=enabled, y=enabled)
    
    # def update_autoscale(self, x_pad=0.05, y_pad=0.5, plot: pg.PlotItem | None = None, index: int | None = None):
    #     target = self._resolve_plot(plot, index)
    #     (x0, x1), (y0, y1) = target.viewRange()
    #     plot.setXRange(x0 - (x1 - x0)*0.05, x1 + (x1 - x0)*0.05, padding=0)
    #     plot.setYRange(y0 - (y1 - y0)*0.50, y1 + (y1 - y0)*0.50, padding=0)

    def set_info(self, key: str, value=None, plot: pg.PlotItem | None = None):
        if isinstance(value, pg.PlotItem) and plot is None:
            plot = value
            value = None

        target = self._resolve_plot(plot)
        panel = self._panel_for_plot(target)
        if panel is None:
            return
        if value is None:
            panel["info"][""] = str(key)
        else:
            panel["info"][str(key)] = str(value)
        self._render_panel_info(panel)

    def exec(self):
        pg.exec()


def parser(expr: str):
    print(expr)
    return lambda x: eval(expr, {"x": x, "np": np})


class Expr:
    def __init__(self, expr, render_from=None):
        self.fx = lambda x: eval(expr, {"x": x, "np": np})
        self.render_from = render_from
        self.version = 0

    def update_expr(self, expr):
        self.fx = lambda x: eval(expr, {"x": x, "np": np})
        self.version += 1
