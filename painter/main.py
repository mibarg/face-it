#import matplotlib
#matplotlib.use('Agg')
from matplotlib import animation, rc
import matplotlib.pyplot as plt
plt.ioff()

from os.path import join
import sys
import argparse
from subprocess import Popen, PIPE

import logging

import cv2
import numpy as np

OBSERVED_VALUE = 0
IMAGE_SHAPE = (512, 512)


def argument_parser():
    parser = argparse.ArgumentParser(description='Painter')
    parser.add_argument('--thresh', dest='dist_treshold', default=40, type=int)
    parser.add_argument('--frame_limit', dest='frame_limit', default=8000, type=int)
    parser.add_argument('--frame_msec', dest='msecs_per_frame', default=6, type=int)
    parser.add_argument('--fps', dest='frames_per_sec', default=None, type=int)

    parser.add_argument('--out', dest='output_path', default='painter/videos/or_vid.mp4', type=str)
    parser.add_argument('--image', dest='image_path', default='painter/examples/or.jpg', type=str)
    parser.add_argument('--add_root', action='store_true', dest='add_root', default=False)

    parser.add_argument('--root', dest='project_root', default='/home/dsteam/repos/face-it/', type=str)
    parser.add_argument('--prepro', dest='image_prepro', default='painter/image_preprocessor.py', type=str)
    parser.add_argument('--tmp', dest='tmp_path', default='painter/examples/tmp.jpg', type=str)
    parser.add_argument('--xml', dest='xml_path', type=str, default='painter/data/haarcascade_frontalface_alt.xml')

    return parser.parse_args()


def main():
    args = argument_parser()

    # Dependecies imports
    sys.path.extend([args.project_root, ])
    from painter.saliency.vid_painter import Painter

    # join paths
    path_image_prepro = join(args.project_root, args.image_prepro)
    path_image = join(args.project_root,args.image_path) if args.add_root else args.image_path
    path_out = join(args.project_root, args.output_path) if args.add_root else args.output_path
    path_tmp = join(args.project_root, args.tmp_path)
    path_xml = join(args.project_root, args.xml_path)

    # read image
    cmnd = "source activate image_pp; %s --image='%s' --grey='%s' --xml='%s'; source deactivate" \
           % (path_image_prepro, path_image, path_tmp, path_xml)

    process = Popen(cmnd, shell=True, stdout=PIPE)
    process.wait()
    image_segment = cv2.imread(path_tmp)

    # create an MRF and Saliancy agent
    painter = Painter(image_segment, dist_scale_thresh=args.dist_treshold, image_shape=IMAGE_SHAPE, observed_value=OBSERVED_VALUE)
    frame_gen = painter.frame_gen()

    # prepare figure
    fig = plt.figure()
    plt.axis('off')

    # init video variables
    blank_img = np.multiply(np.ones(IMAGE_SHAPE), 255).astype(np.int)
    blank_img[0] = 0
    im = plt.figimage(blank_img, 'gray', animated=True)
    plt.close(fig)
    cur_frame, frame_cntr = None, 0

    # define frame producing function
    def updatefig(*args):
        global frame_cntr
        frame_cntr += 1
        if frame_cntr % 1000 == 0:
            logging.info('**********Recoded frame number %d**********' % frame_cntr)
        try:
            cur_frame = frame_gen.next()
        except StopIteration:
            pass
        im.set_array(cur_frame)
        return im,

    # animate and record
    ani = animation.FuncAnimation(fig, updatefig, frames=args.frame_limit, interval=args.msecs_per_frame, blit=True)
    rc('animation', html='html5')
    writer = animation.FFMpegWriter(fps=args.fps)
    ani.save(path_out, writer=writer)

if __name__ == '__main__':
    main()
