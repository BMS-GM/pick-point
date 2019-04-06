#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Create depth map
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import numpy as np
import cv2 as cv


class DepthMap:


    def write_ply(fn, verts, colors):
        ply_header = '''ply
            format ascii 1.0
            element vertex %(vert_num)d
            property float x
            property float y
            property float z
            property uchar red
            property uchar green
            property uchar blue
            end_header
            '''
        verts = verts.reshape(-1, 3)
        colors = colors.reshape(-1, 3)
        verts = np.hstack([verts, colors])
        with open(fn, 'wb') as f:
            f.write((ply_header % dict(vert_num=len(verts))).encode('utf-8'))
            np.savetxt(f, verts, fmt='%f %f %f %d %d %d ')

    if __name__ == '__main__':
        print(__doc__)
        print('loading images...')

        imgR = cv.imread('C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_0_frame_1.png')
        imgL = cv.imread('C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_1_frame_1.png')

        # disparity range is tuned for 'aloe' image pair
        window_size = 3
        min_disp = 16
        num_disp = 112 - min_disp
        stereo = cv.StereoSGBM_create(minDisparity=min_disp,
                                      numDisparities=num_disp,
                                      blockSize=4,
                                      P1=8 * 3 * window_size ** 2,
                                      P2=32 * 3 * window_size ** 2,
                                      disp12MaxDiff=1,
                                      uniquenessRatio=10,
                                      speckleWindowSize=100,
                                      speckleRange=32
                                      )

        print('computing disparity...')
        disp = stereo.compute(imgL, imgR).astype(np.float32) / 16.0

        print('generating 3d point cloud...', )
        h, w = imgL.shape[:2]
        f = 0.8 * w  # guess for focal length
        Q = np.float32([[1, 0, 0, -0.5 * w],
                        [0, -1, 0, 0.5 * h],  # turn points 180 deg around x-axis,
                        [0, 0, 0, -f],  # so that y-axis looks up
                        [0, 0, 1, 0]])
        points = cv.reprojectImageTo3D(disp, Q)
        colors = cv.cvtColor(imgL, cv.COLOR_BGR2RGB)
        mask = disp > disp.min()
        out_points = points[mask]
        out_colors = colors[mask]
        out_fn = 'out.ply'
        write_ply('out.ply', out_points, out_colors)
        print('%s saved' % 'out.ply')
        depthMap = (disp - min_disp) / num_disp
        print(depthMap.shape)

        depthMap[:, 0::100] = 255
        imgL[:, 0::100] = 255
        imgR[:, 0::100] = 255

        depthMap[0::100, :] = 255
        imgL[0::100, :] = 255
        imgR[0::100, :] = 255

        imgL = cv.resize(imgL, (0, 0), fx=0.5, fy=0.5)
        imgR = cv.resize(imgR, (0, 0), fx=0.5, fy=0.5)
        cv.imshow('left', imgL)
        cv.imshow('right', imgR)
        print(depthMap.dtype)
        cv.imshow('depth map', np.array(depthMap, dtype = np.uint8 ) )
        cv.waitKey()

        print('Done')
        cv.destroyAllWindows()



