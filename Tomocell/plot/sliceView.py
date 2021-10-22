import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.widgets import Slider
from matplotlib.patches import Arrow, Circle, Ellipse, Rectangle

class sliceView:
    def __init__(self, data, data_ax, title = '',z = 0,cmap = cm.gray):
        self.ax = data_ax
        data_ax.set_title(title)
        # set size of axes
        plt.subplots_adjust(bottom = 0.25)
        slider_ax = plt.axes([0.25, 0.1, 0.55, 0.03])
        # initial plot
        self.data =data
        self.slices = data.shape[z]
        self.z = z
        init_val = self.slices//2

        self.sliceind = [slice(None),slice(None)]
        self.sliceind.insert(z, init_val)
        
        self.im = data_ax.imshow(data[tuple(self.sliceind)], cmap = cmap)
        # set slider
        self.slider = Slider(
            ax = slider_ax,
            label = 'z axis',
            valmin=0,
            valmax=self.slices-1,
            valstep=1,
            valinit=init_val,
            orientation='horizontal'
        )
        self.slider.on_changed(self.update)

        # generate annot list
        # active_annot : activated annotatiosn. Inactive when x.remove()
        # self.annot: list of functions to activate annotations
        self.active_patches=[]
        self.patches=[list() for _ in range(self.slices)]

    def add_shape(self, shape, z):
        p = self.ax.add_patch(shape)
        self.patches[z].append(p)
        self.active_patches.append(p)
    
    def add_point(self,point,z,radius =3,color='purple'):
        circle = Circle(point,radius=radius, color=color,visible=False)
        self.add_shape(circle, z)

    def add_arrow(self,start,end,z,width=4,color='red'):
        arrow = Arrow(start[0],start[1],end[0],end[1],width=width,color=color,visible=False)
        self.add_shape(arrow, z)
    
    def add_ellipse(self,xy,width,height,angle,z,color='green'):
        ellipse = Ellipse(xy, width, height, angle, color=color,visible=False,fill=False)
        self.add_shape(ellipse, z)
    
    def add_rect(self,xy,width,height,angle,z,color='blue'):
        rect = Rectangle(xy, width, height, angle, color=color,visible=False,fill=False)
        self.add_shape(rect, z)
        
    def update(self,_):
        sliceval = self.slider.val
        self.sliceind[self.z] = sliceval
        self.im.set_data(self.data[tuple(self.sliceind)])
        #self.ax.set_ylabel('slice %s' % self.ind)
        for p in self.active_patches:
            p.set_visible(False)
        for p in self.patches[sliceval]:
            p.set_visible(True)
        
        self.im.axes.figure.canvas.draw_idle()
