/* One candidate: scalar binary64 translation of segments602.query/distance.
 * Hypot deliberately calls the original CPython math.hypot, not a substitute.
 * No fmin/fmax: Python ordered min/max preserve first ties and first NaNs.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <float.h>
#include <fenv.h>

#ifdef __FAST_MATH__
#error "fast math forbidden"
#endif
#if FLT_RADIX != 2 || DBL_MANT_DIG != 53 || DBL_MAX_EXP != 1024 || FLT_EVAL_METHOD != 0
#error "scalar IEEE binary64 required"
#endif
_Static_assert(sizeof(double) == 8, "binary64 required");

typedef struct { double x, y; } Point;
typedef struct { double ax, ay, dx, dy, d; } Segment;
static PyObject *original_hypot = NULL;

static int read_values(PyObject *obj, double *out, Py_ssize_t count) {
    PyObject *seq = PySequence_Fast(obj, "numeric sequence required");
    if (!seq) return -1;
    if (PySequence_Fast_GET_SIZE(seq) != count) {
        Py_DECREF(seq); PyErr_SetString(PyExc_ValueError, "invalid operand arity"); return -1;
    }
    for (Py_ssize_t i = 0; i < count; ++i) {
        out[i] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(seq, i));
        if (PyErr_Occurred()) { Py_DECREF(seq); return -1; }
    }
    Py_DECREF(seq); return 0;
}

static int read_points(PyObject *obj, Point **out, Py_ssize_t *count) {
    PyObject *seq = PySequence_Fast(obj, "points required");
    if (!seq) return -1;
    *count = PySequence_Fast_GET_SIZE(seq);
    *out = PyMem_New(Point, *count ? *count : 1);
    if (!*out) { Py_DECREF(seq); PyErr_NoMemory(); return -1; }
    for (Py_ssize_t i = 0; i < *count; ++i) {
        double q[2];
        if (read_values(PySequence_Fast_GET_ITEM(seq, i), q, 2) < 0) {
            PyMem_Free(*out); *out = NULL; Py_DECREF(seq); return -1;
        }
        (*out)[i].x = q[0]; (*out)[i].y = q[1];
    }
    Py_DECREF(seq); return 0;
}

static int read_segments(PyObject *obj, Segment **out, Py_ssize_t *count) {
    PyObject *seq = PySequence_Fast(obj, "segments required");
    if (!seq) return -1;
    *count = PySequence_Fast_GET_SIZE(seq);
    *out = PyMem_New(Segment, *count ? *count : 1);
    if (!*out) { Py_DECREF(seq); PyErr_NoMemory(); return -1; }
    for (Py_ssize_t i = 0; i < *count; ++i) {
        double q[5];
        if (read_values(PySequence_Fast_GET_ITEM(seq, i), q, 5) < 0) {
            PyMem_Free(*out); *out = NULL; Py_DECREF(seq); return -1;
        }
        (*out)[i] = (Segment){q[0], q[1], q[2], q[3], q[4]};
    }
    Py_DECREF(seq); return 0;
}

static int exact_hypot(double x, double y, double *out) {
    PyObject *a = PyFloat_FromDouble(x), *b = PyFloat_FromDouble(y), *result = NULL;
    if (a && b) result = PyObject_CallFunctionObjArgs(original_hypot, a, b, NULL);
    Py_XDECREF(a); Py_XDECREF(b);
    if (!result) return -1;
    *out = PyFloat_AsDouble(result); Py_DECREF(result);
    return PyErr_Occurred() ? -1 : 0;
}

static int point_query(Point p, Segment s, double *out) {
    double t = 0.0;
    if (s.d != 0.0) {
        /* Preserve every Python subtraction/multiply/add/divide boundary. */
        double a = p.x - s.ax;
        double b = a * s.dx;
        double c = p.y - s.ay;
        double d = c * s.dy;
        double e = b + d;
        double f = e / s.d;
        double inner = 1.0;
        if (f < inner) inner = f; /* min(1., f) */
        if (inner > t) t = inner; /* max(0., inner) */
    }
    double a = p.x - s.ax;
    double b = t * s.dx;
    double x = a - b;
    double c = p.y - s.ay;
    double d = t * s.dy;
    double y = c - d;
    return exact_hypot(x, y, out);
}

static double dot(Point p, double ax, double ay) {
    double a = p.x * ax;
    double b = p.y * ay;
    return a + b;
}

static void range(Point *p, Py_ssize_t n, double ax, double ay, double *lo, double *hi) {
    *lo = *hi = dot(p[0], ax, ay);
    for (Py_ssize_t i = 1; i < n; ++i) {
        double q = dot(p[i], ax, ay);
        if (q < *lo) *lo = q;
        if (q > *hi) *hi = q;
    }
}

static int polygon_query(Point *a, Py_ssize_t na, Segment *ae, Py_ssize_t nae,
                         Point *b, Py_ssize_t nb, Segment *be, Py_ssize_t nbe,
                         double *out) {
    int separated = 0;
    for (int group = 0; group < 2; ++group) {
        Point *p = group ? b : a;
        Py_ssize_t n = group ? nb : na;
        for (Py_ssize_t j = 0; j < n; ++j) {
            if (!na || !nb) {
                PyErr_SetString(PyExc_ValueError, "min() arg is an empty sequence"); return -1;
            }
            Point v = p[j], w = p[(j + 1) % n];
            double ax = v.y - w.y;
            double ay = w.x - v.x;
            double alo, ahi, blo, bhi;
            range(a, na, ax, ay, &alo, &ahi);
            range(b, nb, ax, ay, &blo, &bhi);
            if (alo > bhi || blo > ahi) separated = 1;
        }
    }
    if (!separated) { *out = 0.0; return 0; }
    int first = 1;
    double minimum = 0.0;
    for (int group = 0; group < 2; ++group) {
        Point *p = group ? b : a;
        Segment *edges = group ? ae : be;
        Py_ssize_t n = group ? nb : na;
        Py_ssize_t ne = group ? nae : nbe;
        for (Py_ssize_t j = 0; j < n; ++j) {
            for (Py_ssize_t k = 0; k < ne; ++k) {
                double q;
                if (point_query(p[j], edges[k], &q) < 0) return -1;
                if (first || q < minimum) minimum = q;
                first = 0;
            }
        }
    }
    if (first) { PyErr_SetString(PyExc_ValueError, "min() arg is an empty sequence"); return -1; }
    *out = minimum; return 0;
}

static PyObject *query(PyObject *self, PyObject *args) {
    PyObject *p, *s;
    double pv[2], sv[5], result;
    if (!PyArg_ParseTuple(args, "OO", &p, &s)) return NULL;
    if (read_values(p, pv, 2) < 0 || read_values(s, sv, 5) < 0) return NULL;
    if (point_query((Point){pv[0], pv[1]}, (Segment){sv[0], sv[1], sv[2], sv[3], sv[4]}, &result) < 0) return NULL;
    return PyFloat_FromDouble(result);
}

static PyObject *distance(PyObject *self, PyObject *args) {
    PyObject *ao, *aeo, *bo, *beo;
    Point *a = NULL, *b = NULL;
    Segment *ae = NULL, *be = NULL;
    Py_ssize_t na, nb, nae, nbe;
    double result;
    PyObject *answer = NULL;
    if (!PyArg_ParseTuple(args, "OOOO", &ao, &aeo, &bo, &beo)) return NULL;
    if (read_points(ao, &a, &na) < 0 || read_segments(aeo, &ae, &nae) < 0 ||
        read_points(bo, &b, &nb) < 0 || read_segments(beo, &be, &nbe) < 0) goto done;
    if (polygon_query(a, na, ae, nae, b, nb, be, nbe, &result) < 0) goto done;
    answer = PyFloat_FromDouble(result);
done:
    PyMem_Free(a); PyMem_Free(b); PyMem_Free(ae); PyMem_Free(be);
    return answer;
}

static PyObject *environment(PyObject *self, PyObject *ignored) {
    return Py_BuildValue("{s:i,s:i,s:i,s:i,s:O}", "FLT_EVAL_METHOD", FLT_EVAL_METHOD,
                         "DBL_MANT_DIG", DBL_MANT_DIG, "rounding_mode", fegetround(),
                         "FE_TONEAREST", FE_TONEAREST, "original_math_hypot", original_hypot);
}

static PyMethodDef methods[] = {
    {"query", query, METH_VARARGS, "Exact prepared point-segment query."},
    {"distance", distance, METH_VARARGS, "Ordered scalar SAT and distance min."},
    {"environment", environment, METH_NOARGS, "Floating point runtime evidence."},
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef module = {PyModuleDef_HEAD_INIT, "_scalar603", NULL, -1, methods};
PyMODINIT_FUNC PyInit__scalar603(void) {
    PyObject *math = PyImport_ImportModule("math");
    if (!math) return NULL;
    original_hypot = PyObject_GetAttrString(math, "hypot");
    Py_DECREF(math);
    if (!original_hypot) return NULL;
    return PyModule_Create(&module);
}
