import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

class Slice3dviewer:
    def __init__(self, data, data_ax, title = '',z = 0):
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
        
        self.im = data_ax.imshow(data[tuple(self.sliceind)])
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
        
    def update(self,_):
        self.sliceind[self.z] = self.slider.val
        self.im.set_data(self.data[tuple(self.sliceind)])
        #self.ax.set_ylabel('slice %s' % self.ind)
        self.im.axes.figure.canvas.draw_idle()

'''
if __name__ == '__main__':
    fig, ax = plt.subplots()
    with h5py.File('20210723-Microchip-Tlapse/20210723.175348.933.HanYang_uchip_WBC-007/20210723.175348.933.HanYang_uchip_WBC-007.TCF') as f:
        data = f['Data/3D/000000'][:]
    tracker = Slice3dviewer(data, ax)
    plt.show()
'''