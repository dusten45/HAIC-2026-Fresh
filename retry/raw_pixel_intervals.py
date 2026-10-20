"""Endpoint enclosures for the audited official uint8 preprocessing pipeline.

Premise: each *post-rasterization* RGB channel lies between the supplied uint8
endpoints. This does not certify uncertain gfxdraw polygon coverage. The scene
is flipped before smoothscale; official HUD/text is drawn AFTER that flip, so
callers must include those pixels in the supplied bounds or mark them unknown.
With flip_y=False input coordinates already describe the final raw surface.

The audited pinned paths are pygame2.6.1 SSE 1000x800->96x96 area shrinking and
OpenCV4.8.1 uint8 INTER_LINEAR96->84 then RGB2GRAY. All channel coefficients are
nonnegative, rounding/saturation is monotone, and accumulators cannot overflow
at these dimensions. Endpoints therefore enclose ALL per-pixel combinations;
random samples below are regression checks, not the monotonicity proof.
"""
import os
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
from functools import lru_cache

import cv2
import numpy as np
import pygame
import pygame.gfxdraw


AUDITED_SOURCES = (
    'https://github.com/pygame/pygame/blob/2.6.1/src_c/transform.c',
    'https://github.com/pygame/pygame/blob/2.6.1/src_c/scale_mmx64.c',
    'https://github.com/opencv/opencv/blob/4.8.1/modules/imgproc/src/resize.cpp',
    'https://github.com/opencv/opencv/blob/4.8.1/modules/imgproc/src/color_rgb.simd.hpp',
    'https://github.com/opencv/opencv/blob/4.8.1/modules/imgproc/src/color_rgb.dispatch.cpp',
    'https://github.com/pygame/pygame/blob/2.6.1/src_c/SDL_gfx/SDL_gfxPrimitives.c',
)


def audit_backend():
    """Reject different/unaudited dispatches rather than adding guessed slack."""
    info = dict(pygame=pygame.version.ver,
        smoothscale_backend=pygame.transform.get_smoothscale_backend(),
        opencv=cv2.__version__,ipp_not_exact=cv2.ipp.useIPP_NotExact(),
        opencl=cv2.ocl.useOpenCL())
    if (info['pygame']!='2.6.1' or info['smoothscale_backend']!='SSE' or
            info['opencv']!='4.8.1' or info['ipp_not_exact'] or info['opencl']):
        raise RuntimeError('Unaudited preprocessing backend: '+str(info))
    return info


def _check_rgb(rgb):
    if not isinstance(rgb,np.ndarray) or rgb.dtype!=np.uint8 or rgb.shape!=(800,1000,3):
        raise ValueError('RGB uint8 array shape800x1000x3 required')


def preprocess_raw_rgb(rgb,*,flip_y=True):
    """Execute the exact pinned operations; no geometry/world is instantiated."""
    audit_backend();_check_rgb(rgb)
    surface = pygame.Surface((1000,800),depth=32)
    pygame.surfarray.blit_array(surface,np.transpose(rgb,(1,0,2)))
    if flip_y:
        surface = pygame.transform.flip(surface,False,True)
    scaled = pygame.transform.smoothscale(surface,(96,96))
    image = np.transpose(np.array(pygame.surfarray.pixels3d(scaled)),(1,0,2))
    image = cv2.resize(image,(84,84))
    return cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)


def forward_enclosure(loRGB,hiRGB,*,flip_y=True):
    """Return exact pipeline endpoint uint8 images, with no +/-gray allowance.

    Componentwise raw lower/upper bounds pass through the SAME monotone integer
    operations as an actual RGB image. Correlations between endpoint channels
    may be discarded, which widens the interval but cannot exclude a rendering.
    """
    _check_rgb(loRGB);_check_rgb(hiRGB)
    if np.any(loRGB>hiRGB):
        raise ValueError('Inverted RGB interval')
    lo = preprocess_raw_rgb(loRGB,flip_y=flip_y)
    hi = preprocess_raw_rgb(hiRGB,flip_y=flip_y)
    if np.any(lo>hi):
        raise RuntimeError('Monotone pipeline invariant violated')
    return lo,hi


def _color_image(value):
    array = np.asarray(value)
    if array.shape==(3,):
        if array.dtype.kind not in 'iu' or np.any(array<0) or np.any(array>255):
            raise ValueError('RGB bounds must be integer channels0..255')
        return np.broadcast_to(array.astype(np.uint8),(800,1000,3))
    _check_rgb(array)
    return array


@lru_cache(maxsize=16)
def _polygon_masks(vertices):
    """Certain fill and all potentially color-changing AA+fill pixels.

    Source DEFAULT_ALPHA_PIXEL_ROUTINE uses d+floor((s-d)*alpha/256),
    with opaque overwrite at255. On a32bpp RGB surface channel mask arithmetic
    is equivalent modulo256. For any effective alpha1..255 black-on-white
    changes at least one level, even when white-on-black rounds alpha1 to0.
    AA coverage/scan conversion depends on vertices, not RGB. Repeated blends
    toward a single extreme cannot cancel its detected change.
    """
    def draw(background,foreground,aa):
        surface = pygame.Surface((1000,800),depth=32)
        surface.fill((background,)*3)
        if aa:pygame.gfxdraw.aapolygon(surface,vertices,(foreground,)*3)
        pygame.gfxdraw.filled_polygon(surface,vertices,(foreground,)*3)
        return np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))[:,:,0]
    fill = draw(0,255,False)==255
    white = draw(0,255,True)
    black = draw(255,0,True)
    affect = (white!=0)|(black!=255)
    fill.flags.writeable=False;affect.flags.writeable=False
    return fill,affect


def _ordered_color_images(lower,upper):
    lo,hi=_color_image(lower),_color_image(upper)
    # Constant RGB bounds are by far the common case. Validate their three
    # channels without scanning a2.4million-element broadcast image.
    a,b=np.asarray(lower),np.asarray(upper)
    inverted = np.any(a>b) if a.shape==(3,) and b.shape==(3,) else np.any(lo>hi)
    if inverted:
        raise ValueError('Inverted RGB bounds')
    return lo,hi


def raster_layer_enclosure(layers,background_bounds,*,interest_box=None):
    """Enclose ordered fixed integer polygons before the official vertical flip.

    layers: dictionaries with vertices, rgb_lo, rgb_hi, optional(False default).
    Background/material bounds may be RGB triples or full uint8 RGB images;
    arbitrary pointwise shade variation within those intervals is permitted.
    Required filled pixels overwrite; AA pixels take the old/material hull.
    Optional layers include both absence and presence, even in their fill.
    No uncertain geometry is silently reduced to one polygon. Callers must
    enumerate geometry hypotheses or supply raw bounds covering all geometry.
    interest_box=(x0,y0,x1,y1) is an optional PREflip raw-coordinate rectangle.
    Full-canvas masks preserve raster phase. Outside the rectangle bounds become
    [0,255], so even a too-tight rectangle only widens the forward enclosure.
    """
    audit_backend()
    if len(background_bounds)!=2:raise ValueError('Background lower/upper required')
    background_lo,background_hi=_ordered_color_images(*background_bounds)
    if interest_box is None:
        x0,y0,x1,y1=0,0,1000,800
    else:
        if (len(interest_box)!=4 or any(not isinstance(v,(int,np.integer)) for v in interest_box)):
            raise ValueError('Integer raw interest_box x0,y0,x1,y1 required')
        x0,y0,x1,y1=map(int,interest_box)
        if not 0<=x0<x1<=1000 or not 0<=y0<y1<=800:
            raise ValueError('Interest rectangle outside raw canvas or empty')
    area=np.s_[y0:y1,x0:x1]
    lower=np.zeros((800,1000,3),np.uint8);upper=np.full_like(lower,255)
    lower[area]=background_lo[area];upper[area]=background_hi[area]
    lower_roi,upper_roi=lower[area],upper[area]
    for layer in layers:
        vertices=tuple(tuple(point) for point in layer['vertices'])
        if len(vertices)<3 or any(len(point)!=2 or any(
                not isinstance(v,(int,np.integer)) or not -32768<=v<=32767 for v in point) for point in vertices):
            raise ValueError('At least3 signed16 integer vertex pairs required')
        vertices=tuple(tuple(int(v) for v in point) for point in vertices)
        lo,hi=_ordered_color_images(layer['rgb_lo'],layer['rgb_hi'])
        optional=layer.get('optional',False)
        if not isinstance(optional,bool):raise ValueError('optional must be Boolean')
        fill,affect=_polygon_masks(vertices)
        fill,affect=fill[area],affect[area];lo,hi=lo[area],hi[area]
        lower_roi[affect]=np.minimum(lower_roi[affect],lo[affect])
        upper_roi[affect]=np.maximum(upper_roi[affect],hi[affect])
        if not optional:
            lower_roi[fill]=lo[fill];upper_roi[fill]=hi[fill]
    return lower,upper
