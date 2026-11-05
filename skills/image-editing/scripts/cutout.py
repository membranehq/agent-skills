"""Cut the packshot's own shape, from the photograph alone.

The card is a die-cut piece of paper on a pure white backdrop, and it casts a shadow. Every
cut-out model tried on these packshots reads the shadow as part of the card on one design and
tears a hole through the card on the next, so no model is used. The photograph settles it on its
own, because the backdrop is pure neutral white and a shadow on it is that same white under less
light, which leaves the shadow neutral too. The card's paper carries colour. So colour says what
is card, and the steepest change in colour says where its edge runs.

`field` turns the photograph into one number per pixel: how far that pixel is from being the
backdrop. `seed` reads which pixels are card. `cut` moves the seed's outline onto the steepest
change in the field and returns coverage, from 0 to 1, with a true soft edge at the boundary.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from skimage import measure
from pymatting import estimate_alpha_cf

# The shape prior: one boolean mask of the product's outline, shared by every packshot of the same
# product. Set SHAPE_PRIOR to its .npy file to switch the prior on. Without it `cut` runs on colour
# and brightness alone, which is correct for a one-off photograph; see SKILL.md.
SHAPE = np.load(os.environ['SHAPE_PRIOR']) if os.environ.get('SHAPE_PRIOR') else None

R = 12.0          # how far along the normal to look for the edge, in pixels
DS = 0.5          # sampling step along the normal
MINJUMP = 2.5     # a real edge changes the field by at least this much
SS = 4            # supersampling when the corrected outline is drawn back
BAND = 6          # how far either side of the outline the matting solver may decide
EPS = 1e-5        # how hard it holds coverage smooth where card and backdrop barely differ


def _contours(al):
    """the closed outlines of `al` at half coverage, each as an array of (row, column)"""
    out = []
    for c in measure.find_contours(al, 0.5):
        if len(c) < 60: continue
        if np.hypot(*(c[0] - c[-1])) > 2: continue        # an outline cut by the frame, not closed
        out.append(c[:-1])
    return out

def _normals(c):
    """the unit normal at every point of a closed outline"""
    t = np.roll(c, -2, 0) - np.roll(c, 2, 0)
    n = np.stack([t[:, 1], -t[:, 0]], 1)
    return n / np.maximum(np.hypot(n[:, 0], n[:, 1]), 1e-9)[:, None]

def _orient(al, c, nml):
    """turn every normal to point away from the product"""
    H, W = al.shape
    p = c + nml * 3.0
    v = nd.map_coordinates(al, [np.clip(p[:, 0], 0, H-1), np.clip(p[:, 1], 0, W-1)], order=1)
    return np.where(v[:, None] > 0.5, -nml, nml)

def _wrapmed(v, ok, w=25):
    """the median of each point's neighbours along the closed outline, and whether it has any"""
    n = len(v)
    idx = (np.arange(n)[:, None] + np.arange(-w, w+1)[None, :]) % n
    vals = np.where(ok[idx], v[idx], np.nan)
    got = ~np.all(np.isnan(vals), 1)
    med = np.zeros(n)
    if got.any():
        med[got] = np.nanmedian(vals[got], 1)
    return med, got

def _carry(v, keep):
    """fill the stretches with no edge by interpolating along the closed outline"""
    n = len(v)
    if not keep.any(): return v
    if keep.all(): return v
    i = np.where(keep)[0]
    # unroll the circle so the interpolation wraps
    xs = np.concatenate([i - n, i, i + n])
    ys = np.concatenate([v[i], v[i], v[i]])
    return np.interp(np.arange(n), xs, ys)

def _smooth(v, w=9):
    """average each point with its neighbours along the closed outline"""
    k = np.ones(w) / w
    return np.convolve(np.concatenate([v[-w:], v, v[:w]]), k, 'same')[w:-w]

def _profile(L, c, nml):
    """the field sampled along the outward normal at every outline point"""
    H, W = L.shape
    o = np.arange(-R, R + DS/2, DS)
    p = c[:, None, :] + nml[:, None, :] * o[None, :, None]
    return o, nd.map_coordinates(L, [np.clip(p[..., 0], 0, H-1).ravel(), np.clip(p[..., 1], 0, W-1).ravel()],
                                 order=1).reshape(len(c), len(o))

def _halfcross(o, prof):
    """where the profile falls to half of the plateau inside, to a fraction of a pixel

    Both fields this is used on rise in proportion to how much card a pixel holds: colour does,
    because the white backdrop it mixes with adds none, and darkness below white does, because the
    backdrop contributes a fixed 255. So half of the inside plateau is where the card covers half
    the pixel, which is the edge.
    """
    q = prof.shape[1] // 4
    ins = np.median(prof[:, :q], 1)        # the card, 8 to 12 px inside
    out = np.median(prof[:, -q:], 1)       # the backdrop, or its shadow, 8 to 12 px outside
    half = (ins + out) / 2
    above = prof >= half[:, None]
    i = np.arange(prof.shape[0])
    k = np.clip(prof.shape[1] - 1 - np.argmax(above[:, ::-1], 1), 0, prof.shape[1] - 2)
    a0, a1 = prof[i, k], prof[i, k+1]
    t = np.clip((half - a0) / np.where(np.abs(a1 - a0) < 1e-6, 1e-6, a1 - a0), 0, 1)
    return o[k] + t * DS, ins, out, above.any(1)

def measure_edge(Fc, Fl, c, nml):
    """how far the card's edge lies from each outline point, in pixels

    Colour places the edge wherever the paper has any, which is most of every card: the backdrop is
    pure neutral white and a shadow cast on it stays neutral, so only the card carries colour.
    Where the paper has almost none - one card's pale margin reads under 4 - colour cannot be
    told from the shadow's own 0 to 2, and brightness takes over, but only where the backdrop
    outside that point is clean white. On that card's bottom edge it is 251, so brightness
    works; below one card lies a shadow at 178, darker than the card itself, and brightness
    there would place the edge well outside the card, so that point is left to colour.
    """
    o, pc = _profile(Fc, c, nml)
    offc, insc, outc, gotc = _halfcross(o, pc)
    okc = gotc & (insc - outc >= MINJUMP) & (np.abs(offc) <= R - 2)
    _, pl = _profile(Fl, c, nml)
    offl, insl, outl, gotl = _halfcross(o, pl)
    okl = gotl & (outl <= 255 - 246) & (insl - outl >= 6.0) & (np.abs(offl) <= R - 2)
    off = np.where(okc, offc, offl)
    return off, okc | okl, insc - outc

def corrected_outline_f(Fc, Fl, al, report=False):
    """the outline of `al`, moved onto the card's own edge"""
    polys = []
    stats = []
    for c in _contours(al):
        nml = _orient(al, c, _normals(c))
        off, ok, jump = measure_edge(Fc, Fl, c, nml)
        med, got = _wrapmed(off, ok)
        keep = ok & got & (np.abs(off - med) <= 2.5)
        v = _smooth(_carry(np.where(keep, off, 0.0), keep))
        polys.append((c + nml * v[:, None], nml))
        stats.append((len(c), keep.mean(), float(np.median(off[keep])) if keep.any() else 0.0))
    if report:
        for n, f, m in stats:
            print(f'      outline {n:6d} pts   edge found on {100*f:5.1f}%   median move {m:+5.2f} px')
    return polys

def rasterize(shape, polys, al):
    """draw the corrected outlines back into a coverage map"""
    H, W = shape
    acc = np.zeros((H*SS, W*SS), np.int16)
    for c, nml in polys:
        im = Image.new('L', (W*SS, H*SS), 0)
        ImageDraw.Draw(im).polygon([(x*SS, y*SS) for y, x in c], fill=255)
        f = np.asarray(im) > 0
        # solid or hole is decided by what the seed holds INSIDE the polygon, not beside it: the
        # normal points into the hang hole as readily as it points at the backdrop, so a test taken
        # a few pixels off the outline calls the hang hole solid and fills it in.
        small = f[::SS, ::SS]
        solid = al[small].mean() > 0.5 if small.any() else True
        acc += f.astype(np.int16) * (1 if solid else -1)
    m = (acc > 0).astype(np.float32)
    return np.asarray(Image.fromarray((m*255).astype(np.uint8)).resize((W, H), Image.BOX)).astype(float)/255

def field(a):
    """colour or darkness, in units of colour: how far each pixel is from being the backdrop

    The packshot's backdrop is pure neutral white, and a drop shadow is that same white under less
    light, so the shadow is neutral too: measured on five packshots, every pixel of backdrop and
    shadow carries between 0.0 and 2.6 levels of colour, while the card's paper carries 4 to 22.
    Colour, not brightness, is what separates the card from the backdrop and from its own shadow.
    That is why a brightness threshold could never find the card's left and bottom edges, where the
    card meets its own shadow and the two are equally dark.

    The one part of a card that carries no colour is a black band, and it is far darker than a
    shadow ever goes - the shadows bottom out at 171, the black bands sit at 3 to 98 - so darkness
    settles that case. Darkness enters in the same units as colour so that one field carries both.
    """
    L = a.mean(2); ch = (a.max(2) - a.min(2)).astype(float)
    return nd.gaussian_filter(np.maximum(ch, np.clip(150.0 - L, 0, None) / 4.0), 0.8)


# ---------------------------------------------------------------------------
# The cut itself: the seed says which pixels, the gradient says exactly where.
#
# A cut-out model turned out to be the weak part, not the edge finder - it reads one design's
# packshot well and tears holes across the right half of the next, and no amount of snapping
# repairs a hole. The field above needs no model. But it needs no fixed threshold either, because
# how much colour counts as card is each card's own business: the palest is nearly white and
# carries 4 to 6 levels, while another carries 17 to 22 in the middle and 5 at its pale margin.
# Any one number that keeps the pale card whole lets the darker card's shadow in, and any number
# that keeps that shadow out eats a pale corner and the gaps between a third card's beads.
#
# So the threshold decides only which pixels belong to the card, never where its edge runs:
#   - a generous threshold grows the regions that a strict one has already proved are card,
#     which keeps pale paper attached to the card it belongs to without letting a shadow in,
#     because a shadow touches no strict-card pixel;
#   - every hole is filled except the hang hole, which is found by where it sits rather than by
#     how big it is, so a blown-out highlight on a metal bead cannot pass for one;
#   - then the outline is moved onto the steepest change in the field, which is the edge whatever
#     the paper's colour - a card carrying 5 levels and a card carrying 22 both drop to 0 at the
#     backdrop, and the steepest point of that drop is the same place in both.
#
# The soft edge falls out of the same measurement rather than a blur. A boundary pixel part card
# and part backdrop carries the card's colour in proportion to how much card it holds, because the
# backdrop it mixes with adds the same amount to red, green and blue and so adds no colour at all.
# Divide the colour a boundary pixel has by the colour of the paper beside it, and the answer is
# the fraction of that pixel the card covers.

MINPART = 400        # a speck smaller than this is JPEG noise, not product
MINHOLE = 600        # a hole smaller than this is card texture
WEAK = 2.8           # above the 2.6 that the strongest measured shadow carries

def _largest(M):
    lab, n = nd.label(M)
    if n < 2: return M
    sz = nd.sum(np.ones(M.shape, np.float32), lab, range(1, n+1))
    return lab == 1 + int(np.argmax(sz))

def _holes(M):
    h = nd.binary_fill_holes(M) & ~M
    lab, n = nd.label(h)
    return lab, n

DIE_PAD = 10         # how far inside the fitted die-cut the paper is certainly paper
OVERHANG = 30        # how far past the die-cut a band end may reach, as the base photo's card does

def _put(t, shape, y0, x0):
    out = np.zeros(shape, bool)
    sy0, sx0 = max(0, -y0), max(0, -x0)
    ey, ex = min(t.shape[0], shape[0] - y0), min(t.shape[1], shape[1] - x0)
    if ey <= sy0 or ex <= sx0: return out
    out[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = t[sy0:ey, sx0:ex]
    return out

def _tpl(TPL, h):
    w = round(TPL.shape[1] * h / TPL.shape[0])
    return np.asarray(Image.fromarray(TPL.astype(np.uint8) * 255).resize((w, h), Image.BILINEAR)) > 127

def fit_shape(M, TPL, q=4):
    """Place the die-cut where it overlaps the card body best. The body is the filled silhouette
    with the thin overhanging band ends opened away, so the bands cannot pull the fit sideways."""
    b = nd.binary_opening(nd.binary_fill_holes(M), iterations=10)
    lab, n = nd.label(b)
    if n: b = lab == (np.argmax(nd.sum(np.ones_like(b, float), lab, range(1, n + 1))) + 1)
    small = b[::q, ::q]; ys, xs = np.nonzero(small)
    H0 = (ys.max() - ys.min() + 1) * q
    cy, cx = (ys.min() + ys.max()) / 2 * q, (xs.min() + xs.max()) / 2 * q
    best = None
    for s in np.arange(.94, 1.09, .005):
        t = _tpl(TPL, round(H0 * s)); ts = t[::q, ::q]
        for dy in range(-40, 41, 4):
            for dx in range(-40, 41, 4):
                m = _put(ts, small.shape, round((cy - t.shape[0] / 2 + dy) / q),
                         round((cx - t.shape[1] / 2 + dx) / q))
                v = (m & small).sum() / (m | small).sum()
                if best is None or v > best[0]: best = (v, s, dy, dx)
    v, s, dy, dx = best
    t = _tpl(TPL, round(H0 * s))
    T = _put(t, M.shape, round(cy - t.shape[0] / 2 + dy), round(cx - t.shape[1] / 2 + dx))
    return T, dict(scale=float(s), iou=float(v), dy=dy, dx=dx)

def inside_shape(a, M):
    """the part of the frame that is certainly inside the card, from the fitted die-cut

    Colour alone cannot hold three of the fifteen cards together. three of them are printed on a pale grey stock, and over part of each one the paper carries under one level of colour -
    one design's right third measures 0.9 against a backdrop of 0.0 - so the seed drops it. The lost
    patch touches the card's border rather than being enclosed by it, so filling holes cannot bring
    it back, and the cut came out with a 210,000 px bite taken out of the card. Brightness cannot rescue it on its own either, because the patch reads 215 and the
    shadow beside the card reads 171 to 231.

    Where the patch sits does settle it. Every packshot of one product shares its outline, so fitting that
    die-cut says where the card is, and any pixel well inside the fitted shape that is not the
    backdrop is paper, whatever colour it carries. Outside the shape colour still rules, which is
    what keeps the drop shadow out and lets the overhanging band ends in.

    The die-cut is fitted to the colour seed `M`, not to the L<250 silhouette the old cut used. The
    silhouette carries the drop shadow, so it pulls the fit toward the shadow and the fitted shape
    then reaches past the card: measured on one design, fitting to the silhouette put 10,168 px of
    shadow at 176 levels of brightness inside the shape, while fitting to the colour seed leaves
    394 px, all of it within 8 px of the seed. The seed's own bite biases the fit far less than the
    shadow does, because the fit maximises overlap rather than matching a bounding box.

    What the shape restores on a healthy card is its hang hole, and `seed` punches that out again
    afterwards, so the prior costs those cards nothing.

    Inside the shape every pixel counts, with no brightness test. One card's top right
    corner is blown out to 252 and another's to 254, as bright as the backdrop, so a test on
    brightness cut a notch out of each corner. The only thing inside the card that is not paper is the hang hole, and `seed`
    punches that out by where it sits.

    The same fitted shape also carries the hang hole, and that is the one place it beats colour.
    Colour finds the whole punched opening, outer rim and all, because the opening is where the
    white backdrop shows. But the punch leaves a bevelled wall of paper a millimetre deep around
    it, and that wall is card: it is what makes the hole read as a hole. Cutting at the outer rim
    throws the wall away and leaves a flat disc, and on one card, whose punch is torn and 204 px
    across against a die of 122, it opened the card's top edge and the base photo's own hole came
    through as a grey ghost ring. The die-cut's hole is the void alone, so it keeps the wall.
    """
    T, info = fit_shape(M, SHAPE)
    return nd.binary_erosion(T, iterations=DIE_PAD), nd.binary_fill_holes(T) & ~T, info


OPEN = 25            # a lobe narrower than twice this is a band end, not card

def reach_of(M):
    """how far a band end may reach: the card's own convex outline, grown by OVERHANG

    The packshots photograph the bracelets tied loosely, so their ends trail past the card - 63,
    53 and 55 px on three designs - while the base photo's own card trails 25. Everything past that
    in the base photo is the model's hand, so a cut that keeps the full trail pastes bracelet over
    her fingers.

    The bound cannot be the fitted die-cut grown by 30. The die-cut's sides are indented at the
    waist, and no two cards are torn alike there, so on one design the card stands 69 px proud of the
    template's left indent and the clip took an 845 px tall strip out of the card itself.

    The card's own convex outline has no indent, so it cannot cut into the card anywhere. Along the
    straight edges it runs where the card runs, which is where a trailing band end has to be
    stopped. The outline is taken from the card with its band ends opened away: twenty-five
    iterations removes a lobe up to 50 px across, which covers every band end measured, and the
    card itself is nowhere near that thin.
    """
    from skimage.morphology import convex_hull_image
    b = nd.binary_opening(nd.binary_fill_holes(M), iterations=OPEN)
    lab, n = nd.label(b)
    if n:
        b = lab == 1 + int(np.argmax(nd.sum(np.ones(b.shape, np.float32), lab, range(1, n + 1))))
    return nd.binary_dilation(convex_hull_image(b), iterations=OVERHANG)

DARK = 240           # a pixel this dark, inside the card's own outline, is paper

def hull_repair(M, L):
    """the paper the colour test dropped: dark pixels inside the card's own convex outline

    One design is printed on a pale grey stock, and over its right third the paper carries 0.9 levels of
    colour against a backdrop of 0.0, so the colour seed drops a strip of card up to 524 px wide.
    The strip touches the card's border instead of being enclosed by it, so filling holes cannot
    bring it back, and every attempt to repair it downstream failed: the fitted die-cut is itself
    placed against the bitten seed, so it lands 59 px inside the paper, and the edge measurement
    reaches 12 px, far short of the 50 px it would have to cross.

    Brightness decides it, once the search is bounded. The strip reads 218 against a backdrop of
    248, so `L < 240` separates them - but the drop shadow beside the card reads 171 to 231 and
    would be admitted too. The card's own convex outline is the bound that excludes the shadow,
    because a shadow falls outside the card while a bite falls inside. The outline comes from the
    bitten seed, and a convex hull closes a bite in a straight edge: measured on that design, the
    hull of the bitten seed reaches the card's right edge on every row but the worst few.

    The hull is only the bound, never the answer. It bridges the indents at the card's waist, where
    one card's hull stands 83 px proud of the paper, so the brightness test inside it is what decides:
    the backdrop showing through a waist indent reads 248 and stays out.

    Admitted pixels must also join the seed, so a dark object lying inside the hull but apart from
    the card cannot be taken for paper.
    """
    from skimage.morphology import convex_hull_image
    b = nd.binary_opening(nd.binary_fill_holes(M), iterations=10)
    lab, n = nd.label(b)
    if n:
        b = lab == 1 + int(np.argmax(nd.sum(np.ones(b.shape, np.float32), lab, range(1, n + 1))))
    cand = convex_hull_image(b) & (L < DARK)
    lab, n = nd.label(cand | M)
    if not n:
        return M
    return np.isin(lab, np.unique(lab[M & (lab > 0)])) & (lab > 0)


def seed(F, c0, inner=None, holeT=None, L=None):
    """which pixels are card: strict pixels, grown through generous ones, holes filled"""
    strong = F >= c0 / 2
    lab, n = nd.label(F >= min(WEAK, c0 / 2))
    if n:
        hit = np.unique(lab[strong & (lab > 0)])
        M = np.isin(lab, hit) & (lab > 0)
    else:
        M = strong
    lab, n = nd.label(M)
    if n:
        sz = nd.sum(np.ones(M.shape, np.float32), lab, range(1, n+1))
        M = np.isin(lab, [i+1 for i in range(n) if sz[i] >= MINPART]) & (lab > 0)
    if L is not None:
        M = hull_repair(M, L)
    if inner is not None:
        M = M | inner
    # Close the seed before anything reads its outline. Where the paper carries almost no colour
    # the threshold flickers from column to column and leaves the border a comb of one and two
    # pixel notches, and on one card a few pale spots on the top edge open into the
    # backdrop, so filling holes never reaches them. Closing removes both and leaves a smooth
    # boundary for the edge measurement to move.
    M = nd.binary_closing(M, structure=np.ones((3, 3), bool), iterations=8)
    filled = nd.binary_fill_holes(M)
    ys, xs = np.where(filled)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    hole = hang_hole(F, c0, filled)
    if holeT is not None:
        # the die punch, confirmed by the photograph: the void the fitted die-cut says is there,
        # kept only where the photograph agrees it is open. If the fit is off far enough to lose
        # half of it, the photograph decides on its own.
        h2 = holeT & hole
        if h2.sum() >= 0.5 * holeT.sum():
            hole = h2
    return filled & ~hole

def hang_hole(F, c0, card):
    """the hole punched at the top of the card, as against every other pale place on it

    It cannot be found by its colour. On one card the backdrop seen through the hole reads 3
    to 5 levels of colour, not 0, because the warm paper bounces light into it, which is enough to
    pass for pale paper; and a blown-out highlight on a metal bead reads 254 against paper at 229,
    which is as white as the backdrop and 6,178 px across, so neither colour nor size tells the two
    apart. Two things do, together: the hole is a patch the paper's colour does not reach that the
    backdrop cannot reach either, because the card encloses it, and it is punched at the top of the
    card near the middle, where the highlight is not.
    """
    cold = F < c0 / 2
    lab, n = nd.label(cold)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    lab, n = nd.label(cold & ~np.isin(lab, border[border > 0]))
    ys, xs = np.where(card)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    best, bestsz = np.zeros(F.shape, bool), 0
    for i in range(1, n + 1):
        m = lab == i
        sz = int(m.sum())
        if sz < MINHOLE or sz <= bestsz: continue
        cy, cx = nd.center_of_mass(m)
        if cy < y0 + 0.20 * (y1 - y0) and abs(cx - (x0 + x1) / 2) < 0.25 * (x1 - x0):
            best, bestsz = m, sz
    if not bestsz:
        return best
    # The rim of the hole carries colour of its own. The punch leaves a wall of paper a millimetre
    # deep, and on one card that wall stands in shade while the backdrop behind it picks up
    # warm light off the paper, so a ring inside the hole reads 5 to 12 where the open backdrop
    # reads 2 and the paper 18. Half the paper's colour is the wrong fence for that ring, and the
    # hole comes out 124 px wide where the same punch gives 176 on every other design. So grow the
    # hole the way the card itself is grown, and let the hole's own interior say how far: three
    # times what it reads, never past three quarters of the paper, and never more than forty pixels
    # out, which keeps the growth clear of the card's own soft top edge. A hole that reads the open
    # backdrop, as four of the five do, asks for no growth at all.
    thr = min(3 * float(np.percentile(F[best], 90)), 0.75 * c0)
    if thr <= c0 / 2:
        return best
    cold = F < thr
    lab, n = nd.label(cold)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    near = cold & ~np.isin(lab, border[border > 0]) & nd.binary_dilation(best, iterations=40)
    lab, n = nd.label(near)
    hit = np.unique(lab[best & (lab > 0)])
    grown = nd.binary_fill_holes(np.isin(lab, hit[hit > 0]) & (lab > 0))
    return grown if grown.sum() > bestsz else best

def paper(F, M):
    """how much colour the card's paper carries, read well inside its edge

    Read too close to the edge and the answer is the edge itself. The a card packshot's top edge is
    not a step but a ramp fifty pixels deep - the photograph is soft there - so a ring six pixels
    inside the outline sits in the middle of that ramp and reports 6 where the paper reads 20. The
    ring is taken from 25 to 60 px in, which is past any edge on these packshots, and falls back to
    a narrower one on a card too small to give it.
    """
    for a, b in ((25, 60), (8, 25), (2, 8)):
        rim = nd.binary_erosion(M, iterations=a) & ~nd.binary_erosion(M, iterations=b)
        if rim.sum() >= 2000:
            return max(float(np.median(F[rim])), 2 * WEAK)
    return 12.0

def matte(a, m, report=False):
    """coverage, solved from the photograph's own colours in a band around the outline

    A threshold cannot end here. The packshots are JPEGs, and at a near-white edge the eight pixel
    blocks of the compression differ by a level or two; on one card, whose paper carries
    only 5 levels of colour against the backdrop's 0, one level of block noise is a third of the
    way from backdrop to card, so a threshold turns the compression into a comb of notches along
    every straight edge. Matting answers it the way a photo editor does: the outline above is
    trusted only to say where the edge runs, to within a few pixels, and inside that band the
    coverage is solved for, under the rule that neighbouring pixels of one colour share one
    coverage. The rule is what smooths the edge, because it reads along the edge as well as across
    it, and block noise does not survive it.
    """
    tri = np.full(m.shape, 0.5)
    inside = nd.binary_erosion(m, iterations=BAND)
    outside = ~nd.binary_dilation(m, iterations=BAND)
    tri[inside] = 1.0
    tri[outside] = 0.0
    ys, xs = np.where(~outside)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    A = np.zeros(m.shape)
    A[y0:y1, x0:x1] = estimate_alpha_cf(a[y0:y1, x0:x1] / 255.0, tri[y0:y1, x0:x1],
                                        laplacian_kwargs={'epsilon': EPS})
    A[inside] = 1.0
    A[outside] = 0.0
    if report:
        print(f'    soft edge {int(((A > 0.02) & (A < 0.98)).sum()):7d} px')
    return A

def cut(a, report=False, passes=2, die=None):
    """the packshot's own shape, measured

    `a` is the photograph as a float array of shape (H, W, 3), values 0 to 255. The return is one
    coverage value per pixel, 0 to 1. `die` forces the shape prior on or off; by default it is on
    whenever SHAPE_PRIOR names a file.
    """
    F = field(a)
    Fl = nd.gaussian_filter(255.0 - a.mean(2), 0.8)
    c0 = paper(F, seed(F, 12.0))     # read the paper from colour alone, before the die-cut helps
    La = a.mean(2)
    M = seed(F, c0, L=La)
    reach = None
    if SHAPE is not None if die is None else die:
        inner, holeT, info = inside_shape(a, M)
        M = seed(F, c0, inner, holeT, L=La)
        reach = reach_of(M)
        if report:
            print(f"    die-cut scale {info['scale']:.3f}  iou {info['iou']:.3f}"
                  f"  adds {int((inner & ~M).sum()):7d} px  trims {int((M & ~reach).sum()):7d} px")
        M = M & reach
    if report:
        print(f'    paper {c0:5.1f}   seed {M.sum():8d} px')
    al = M.astype(float)
    for _ in range(passes):
        al = rasterize(a.shape[:2], corrected_outline_f(F, Fl, al, report), al)
        if reach is not None:
            al = al * reach           # the edge measurement must not walk a band end back out
    return matte(a, (al > 0.5) & (reach if reach is not None else True), report)


if __name__ == '__main__':
    # cutout.py <photo> <out.png> [--report]
    src, dst = sys.argv[1], sys.argv[2]
    a = np.asarray(Image.open(src).convert('RGB')).astype(float)
    al = np.clip(cut(a, report='--report' in sys.argv), 0, 1)
    out = np.dstack([a, al * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(dst)
    print(f'{dst}  {int((al > .5).sum()):,} px of product,'
          f' {int(((al > 0) & (al < 1)).sum()):,} px of soft edge')
