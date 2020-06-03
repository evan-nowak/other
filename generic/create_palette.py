#!/usr/bin/env python3

"""
#########################
Create Palette
#########################

:Description:
    Create a color palette

:Usage:
    Called from other scripts

"""


def create_palette(cs, N=256):
    import numpy as np

    cs = [i.strip('#') for i in cs]

    L = len(cs) - 1
    M = int(N / L)

    cs = [(int(i[:2], 16), int(i[2:4], 16), int(i[4:], 16)) for i in cs]

    cs_new = []

    for i in range(L):
        temp = []

        for j in [0, 1, 2]:
            c1, c2 = cs[i][j], cs[i + 1][j]

            step = (c2 - c1) / M

            try:
                c = np.arange(c1, c2, step)
                c = np.around(c).astype(int)
            except ZeroDivisionError:
                c = [c1] * M

            temp.append(c[1:-1])

        temp = list(zip(*temp))

        cs_new.append(cs[i])
        cs_new.extend(temp)

    cs_new.append(cs[-1])

    cs_new = [''.join([hex(i).split('x')[1].zfill(2) for i in c]) for c in cs_new]

    cs_new = ['#' + i for i in cs_new]

    return cs_new


if __name__ == '__main__':

    # print(__doc__)

    c = create_palette(['ff0000', 'ffea00'], num=36)
    print(c)
