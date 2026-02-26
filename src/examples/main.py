import threading
import time
import graphics_analyzer.src.core as core
import numpy as np

canvas = core.Canvas()

# fx = canvas.add_func('2/(1+np.e**x)', 'blue') # функция
# fx = canvas.add_func('(1-np.e**(2*(1-x)))**2', 'blue') # функция
# fx = canvas.add_func('-2*2*(1-np.e**(2*(1-x)))*np.e**(2*(1-x))', 'green') # функция

fx = canvas.add_func('4*((1/x)**12-(1/x)**6)', 'blue') # функция
fx = canvas.add_func('24*(2/x**13-(1/x**7))', 'green') # функция

# def user_thread():
#     while True:
#         for i in range(100000000000):
#             canvas.update_func(fx, f'np.sin(x)+np.cos(x)+{i/20}', 'blue')#+{np.sin(i/20)}
#             time.sleep(0.05)


# t = threading.Thread(target=user_thread, daemon=True)
# t.start()

canvas.exec()





