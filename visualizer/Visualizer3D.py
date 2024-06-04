import pyqtgraph.opengl as gl
import numpy as np

class Visualizer3D(gl.GLViewWidget):
    
    def __init__(self):
        super(Visualizer3D, self).__init__()     

        N = 11
        M = 11

        x = np.linspace(0, 10, N)
        y = np.linspace(0, 10, M)
        z = np.random.random((N, M))
       
        self.plot_item = gl.GLSurfacePlotItem(x, y, z, drawEdges = True)
        self.addItem(self.plot_item)


    def update_random(self):
        N = 11
        M = 11

        x = np.linspace(0, 10, N)
        y = np.linspace(0, 10, M)
        z = np.random.random((N, M))        
        self.plot_item.setData(x, y, z)