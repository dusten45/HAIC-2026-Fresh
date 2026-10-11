"""One legal, one-hop pixel support cue; no labels or simulator state."""
import cv2
import numpy as np


def supported_road(image):
    base=(image>0.32)&(image<0.47)
    expanded=(image>0.32)&(image<0.52)
    cross=np.array([[0,1,0],[1,0,1],[0,1,0]],np.uint8)
    adjacent=cv2.dilate(base.astype(np.uint8),cross)>0
    # Newly admitted pixels cannot become seeds for another expansion.
    return (base | (expanded & ~base & adjacent)).astype(np.uint8)
