import numpy as np 

class Palette:
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


def test():
    collors = [
        (0x00, 0x00, 0x00),
        (0xFF, 0x00, 0x00),
        (0x00, 0xFF, 0x00),
        (0x00, 0x00, 0xFF),
        (0xFF, 0xFF, 0xFF)
    ]
    steps = [0,10,20,30,40]
    p = Palette(steps, collors)
    t = np.arange(0,41)
    val = p.interp(t)
    print(val)

if __name__ == "__main__":
    test()
