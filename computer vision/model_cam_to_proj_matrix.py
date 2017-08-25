import numpy as np
import math


def rodrigues(r):
    '''Rodrigues formula
    Input: 1x3 array of rotations about x, y, and z
    Output: 3x3 rotation matrix'''
    def S(n):
        Sn = np.array([
            [0, -n[2], n[1]],
            [n[2], 0, -n[0]],
            [-n[1], n[0], 0]])
        return Sn
    theta = np.linalg.norm(r)
    if theta > 1e-30:
        n = r/theta
        Sn = S(n)
        R = np.eye(3) + np.sin(theta)*Sn + (1-np.cos(theta))*np.dot(Sn, Sn)
    else:
        Sr = S(r)
        theta2 = theta**2
        R = np.eye(3) + (1 - theta2 / 6.)*Sr + (.5 - theta2 / 24.) * np.dot(Sr, Sr)
    return np.mat(R)

'''
Zoom = 2.2137359  # Focal
AspectRatio = 1920.0 / 1080.0
Skew = 0
Pan = -20.644655
Tilt = 102.63156
Roll = -5.0312373
Tx = 39.021924
Ty = -2.0245495
Tz = 110.96914

'''
Zoom = 0.853
AspectRatio = 1920.0 / 1080.0
Skew = 0.1
Pan = 35.34
Tilt = 117.04
Roll = 10.06
Tx = 5
Ty = -3
Tz = 20


K = np.array([
    [Zoom, Skew, 0.5],
    [0.0, Zoom * AspectRatio, 0.5],
    [0.0, 0.0, 1.0]])


# Rotation matrix
Rpan = rodrigues(np.array([0.0, 0.0, Pan*math.pi/180.0]))
Rtilt = rodrigues(np.array([Tilt*math.pi/180.0, 0.0, 0.0]))
Rroll = rodrigues(np.array([0.0, 0.0, Roll*math.pi/180.0]))
Mrot = Rroll * Rtilt * Rpan

# Translation vector
t = np.array([Tx, Ty, Tz])

KR = K * Mrot
Kt = np.dot(K, t)


# Projection Martix
Rproj = np.zeros((3, 4))
Rproj[:, 0] = KR[:, 0].T
Rproj[:, 1] = KR[:, 1].T
Rproj[:, 2] = KR[:, 2].T
Rproj[:, 3] = Kt
print("Rproj: {}".format(Rproj))
