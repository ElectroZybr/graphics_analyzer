import numpy as np
from graphics_analyzer import core


canvas = core.Canvas()


def func(x):
    if x != 0:
        return 4 * ((1 / x) ** 12 - (1 / x) ** 6)
    return 0

def df(x):
    if x != 0:
        return -24 * (2 / x**13 - (1 / x**7))
    return None

def acl(x, dt):
    return -df(x)

def euler(x, v, dt):
    a = acl(x, dt)
    v = v + a * dt
    x = x + v * dt
    return x, v

def verlet(x, v, dt):
    a0 = acl(x, dt)
    x = x + v * dt + 0.5 * a0 * dt**2
    a1 = acl(x, dt)
    v = v + 0.5 * (a0 + a1) * dt
    return x, v


def energy(x, v):
    return func(x) + 0.5 * v**2


fx = canvas.add_func("4*((1/x)**12-(1/x)**6)", "green", 0)
pt = canvas.add_point(0, 0)
v = 0.00001
x = 1.5
dt = 0.05


def step():
    global x, v
    x, v = euler(x, v, dt)
    x, v = verlet(x, v, dt)
    canvas.update_point(pt, x, func(x))


sim_timer = core.pg.QtCore.QTimer()
sim_timer.timeout.connect(step)
sim_timer.start(50)

canvas.exec()
