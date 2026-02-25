import re
import pyqtgraph as pg
import numpy as np
from pyqtgraph import GraphicsLayoutWidget

class Canvas:
    funcs = []
    curves = []
    lines = []
    error_lines = []
    counter = 0

    pen_pool = {
        'Lblue': pg.mkPen(color=(50, 200, 200), width=4),
        'blue': pg.mkPen(color=(50, 130, 200), width=4),
        'red': pg.mkPen(color=(220, 60, 60), width=4),
        'green': pg.mkPen(color=(75, 220, 90), width=4),
        'gray': pg.mkPen(color=(150, 150, 150), width=3, style=pg.QtCore.Qt.PenStyle.DashLine)
    }

    def __init__(self) -> None:
        self.app = pg.mkQApp()
        self.w: GraphicsLayoutWidget = GraphicsLayoutWidget()
        self.w.resize(1400, 900)
        self.w.setBackground((30, 30, 30))
        self.w.setVerticalScrollBarPolicy(pg.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.w.setHorizontalScrollBarPolicy(pg.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.plot: pg.PlotItem = self.w.addPlot()
        self.w.nextCol()
        self.error_plot: pg.PlotItem = self.w.addPlot()
        self.plot.getViewBox().setAspectLocked(True)

        pg.setConfigOptions(antialias=True,)

        self.default_pen = self.pen_pool['Lblue']

        # ось X = 0
        x0 = pg.InfiniteLine(
            pos=0,
            angle=0,           # горизонтальная
            pen=pg.mkPen((150, 150, 150), width=2)
        )

        # ось Y = 0
        y0 = pg.InfiniteLine(
            pos=0,
            angle=90,          # вертикальная
            pen=pg.mkPen((150, 150, 150), width=2)
        )

        text = pg.TextItem(
            text='x = 2',
            color='w',
            anchor=(0.5, 0.5),
            html='<span style="color:white; font-size:25pt;">x = 2</span>'
            
        )

        # text.setFlag(text.ItemIgnoresTransformations)
        # self.plot.addItem(text)
        # text.setPos(2, 0)


        self.plot.addItem(x0)
        self.plot.addItem(y0)
        self.plot.setTitle("Function")
        self.error_plot.setTitle("Error")
        self.plot.showGrid(x=True, y=True, alpha=0.6)
        self.error_plot.showGrid(x=True, y=True, alpha=0.6)
        self.plot.getAxis('left').setStyle(autoExpandTextSpace=False, autoReduceTextSpace=False)
        self.error_plot.getAxis('left').setStyle(autoExpandTextSpace=False, autoReduceTextSpace=False)
        self.plot.getAxis('bottom').setStyle(autoExpandTextSpace=False, autoReduceTextSpace=False)
        self.error_plot.getAxis('bottom').setStyle(autoExpandTextSpace=False, autoReduceTextSpace=False)
        self.plot.getAxis('left').setWidth(70)
        self.error_plot.getAxis('left').setWidth(70)
        self.plot.getAxis('bottom').setHeight(45)
        self.error_plot.getAxis('bottom').setHeight(45)
        self.plot.getViewBox().setMouseEnabled(x=True, y=True)
        self.error_plot.getViewBox().setMouseEnabled(x=True, y=True)
        vb = self.plot.getViewBox()
        vb.enableAutoRange(enable=False)  # тоже отключает авто-scale

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # каждые 50 мс (~20 FPS)

        self.w.show()

    def update(self):
        x_range, _ = self.plot.viewRange() # type: ignore
        scale = (x_range[1] - x_range[0])*0.5
        x = np.linspace(x_range[0]-scale, x_range[1]+scale, 1000)

        for i, f in enumerate(self.funcs):
            y = f.fx(x)
            if f.render_from is not None:
                mask = x >= f.render_from
                self.curves[i].setData(x[mask], y[mask])
            else:
                self.curves[i].setData(x, y)


    def add_func(self, func: str, color: str | None = None, fr: float | None = None):
        self.funcs.append(Expr(func, fr))
        
        if color:
            pen = self.pen_pool.get(color)
        else:
            key = list(self.pen_pool.keys())[len(self.curves)%len(self.pen_pool)]
            pen = self.pen_pool[key]

        if not pen:
            print(f'\033[31mСтиль \'{color}\' не найден\033[0m')
            pen = self.default_pen

        self.curves.append(self.plot.plot([], [], pen=pen))
        return self.funcs[-1]
    
    def update_func(self, func, new_func, color: str | None = None):
        for i, f in enumerate(self.funcs):
            if f is func:
                self.funcs[i].update_expr(new_func)        

    def add_unit_circle(self):
        a = np.linspace(0, 2*np.pi, 100)
        self.plot.plot(np.sin(a), np.cos(a), pen=self.default_pen)
    
    def add_point(self, x, y, color='w', size=0.05):
        self.lines.append(self.plot.plot([x], [y], pen=None, symbol='o', symbolSize=size, symbolBrush=color, symbolPen=None, pxMode=False))
        return self.lines[-1]

    def add_error_plot(self, color: str | None = "red"):
        pen = self.pen_pool.get(color) if color else self.default_pen
        if not pen:
            pen = self.default_pen
        self.error_lines.append(self.error_plot.plot([], [], pen=pen))
        return self.error_lines[-1]

    def update_error_plot(self, line, x, y):
        for i, item in enumerate(self.error_lines):
            if item is line:
                self.error_lines[i].setData(x, y)
                return
    
    def update_point(self, pt, x, y):
        for i, f in enumerate(self.lines):
            if f is pt:
                self.lines[i].setData([x], [y])

    def update_animation(self):
        a = (self.counter/5) * (2*np.pi/360)

        s, c = np.sin(a), np.cos(a)
        self.lines[0].setData([c], [s])
        self.lines[1].setData([c, c], [0, s])
        self.lines[2].setData([0, c], [s, s])
        self.lines[3].setData([0, c], [0, s])

    def draw_func(self, func):
        pass

    def exec(self):
        pg.exec()


def parser(expr: str):
    # expr = expr.replace('^', '**')
    # expr = re.sub(r'(\d+|[a-zA-Z])\s*([a-zA-Z])', r'\1 * \2', expr)
    # expr = re.sub(r'\|([^|]+)\|', r'abs(\1)', expr)
    print(expr)
    return lambda x: eval(expr, {'x': x, 'np': np})

class Expr:
    def __init__(self, expr, render_from = None):
        self.fx = lambda x: eval(expr, {'x': x, 'np': np})
        self.render_from = render_from
    
    def update_expr(self, expr):
        self.fx = lambda x: eval(expr, {'x': x, 'np': np})

class Equation:
    def __init__(self, left_expr, right_expr, render_from = None) -> None:
        self.left_expr = left_expr
        self.right_expr = right_expr
        self.render_from = render_from
    
    
