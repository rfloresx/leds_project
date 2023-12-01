import numpy as np 

class Palete:
    def __init__(self, xp, fp):
        self.xp = xp
        self.fp = np.array(fp,dtype =np.int16)
        self.rp = self.fp[:,0]
        self.gp = self.fp[:,1]
        self.bp = self.fp[:,2]

    def interp(self, data):
        val_r = np.interp(data, self.xp, self.rp)
        val_g = np.interp(data, self.xp, self.gp)
        val_b = np.interp(data, self.xp, self.bp)
        return np.column_stack((val_r, val_g, val_b)).astype(np.int16)

# colors = [
#     (0x00,0x00,0x00),
#     (0xff,0x00,0x00),
#     (0x00,0xff,0x00),
#     (0x00,0x00,0xff)
# ]
# p = Palete([0,1,2,3], colors)
# d = np.array([0, .5, 1, 1.5, 2, 2.5, 3, 3.5, 4])
# v = p.interp(d)
# print(v)
# val = np.interp([1,.5,2.5], val[0],val[1])
    


