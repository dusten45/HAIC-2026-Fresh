"""Small grayscale-only keep classifier; learned weights are separate private assets."""
import hashlib
import time

import cv2
import numpy as np

FEATURE_NAMES = ['gray','mean3','mean7','std3','std7','contrast3','contrast7',
                 'sobel_x','sobel_y','gradient','laplacian',
                 *[f'neighbor_{dy}_{dx}' for dy in (-1,0,1) for dx in (-1,0,1) if dy or dx],
                 'original_P_fraction3','original_P_fraction7']


def features(observation):
    assert observation.shape == (4,84,84) and observation.dtype == np.float32
    assert np.isfinite(observation).all() and observation.min() >= 0 and observation.max() <= 1
    image = observation[-1]
    original = ((image > 0.32) & (image < 0.47)).astype(np.uint8)
    mean3,mean7 = cv2.blur(image,(3,3)),cv2.blur(image,(7,7))
    std3 = np.sqrt(np.maximum(0,cv2.blur(image*image,(3,3))-mean3*mean3))
    std7 = np.sqrt(np.maximum(0,cv2.blur(image*image,(7,7))-mean7*mean7))
    gx = cv2.Sobel(image,cv2.CV_32F,1,0,ksize=3)/8
    gy = cv2.Sobel(image,cv2.CV_32F,0,1,ksize=3)/8
    padded = np.pad(image,1,mode='reflect')
    parts = [image,mean3,mean7,std3,std7,image-mean3,image-mean7,
             gx,gy,np.sqrt(gx*gx+gy*gy),cv2.Laplacian(image,cv2.CV_32F,ksize=1)]
    parts += [padded[1+dy:85+dy,1+dx:85+dx]-image
              for dy in (-1,0,1) for dx in (-1,0,1) if dy or dx]
    parts += [cv2.blur(original.astype(np.float32),(k,k)) for k in (3,7)]
    value = np.stack(parts,axis=-1).astype(np.float32)
    assert value.shape == (84,84,len(FEATURE_NAMES)) and np.isfinite(value).all()
    return value,original


class KeepStudent:
    def __init__(self,model_path):
        self.model = cv2.ml.DTrees_load(str(model_path))
        assert self.model.isTrained() and self.model.isClassifier()
        assert self.model.getVarCount() == len(FEATURE_NAMES)
        assert self.model.getMaxDepth() == 5 and self.model.getMinSampleCount() == 64

    def mask(self,observation):
        started = time.perf_counter()
        value,original = features(observation)
        selected = original.astype(bool)
        keep = np.zeros_like(original)
        if selected.any():
            labels = self.model.predict(np.ascontiguousarray(value[selected]))[1].reshape(-1)
            assert np.isin(labels,[0,1]).all()
            keep[selected] = labels.astype(np.uint8)
        mask = original & keep
        assert np.all(mask <= original)
        detail = {'original_P_cells':int(original.sum()),'kept_cells':int(mask.sum()),
                  'deleted_cells':int((original-mask).sum()),'added_cells':0,
                  'original_P_sha256':hashlib.sha256(original.tobytes()).hexdigest(),
                  'student_mask_sha256':hashlib.sha256(mask.tobytes()).hexdigest(),
                  'inference_ms':(time.perf_counter()-started)*1000,
                  'feature_mean_on_P':value[selected].mean(axis=0).astype(float).tolist() if selected.any() else None,
                  'input_shape':[4,84,84],'input_dtype':'float32','input_kind':'official_grayscale_only'}
        return mask,detail
