# How the cut works, and why

`scripts/cutout.py` is the cut. This file says why it works the way it does, so the experiments
that produced it are not repeated.

## The problem

A packshot is one product photographed on a white backdrop. The product has to come off that
backdrop with an alpha channel. Two things make it hard.

1. **The product casts a shadow onto the backdrop.** The shadow is dark, so a test on brightness
   takes the shadow for product and a grey smear rides along onto whatever the cut is pasted on.
2. **A pale product barely differs from the backdrop.** Measured on fifteen designs of one card,
   the paper carried 5 to 32 levels of colour against the backdrop, and over part of three of them
   less than 1. No single fixed threshold both admits the product and excludes the shadow.

## What does not work

**Segmentation models.** `birefnet-general`, `birefnet-dis`, `isnet-general-use`, `bria-rmbg`,
`massive` and `hrsod` were each run on five packshots. Measured against the real edge they missed
by 1 to 199 px, and `birefnet-general` put 762,061 shadow pixels inside the mask on one image.
They are also the wrong class of model: segmentation answers "which object", which is already
known here, while an edge needs _matting_ — the coverage of each pixel, between 0 and 1.

**A measured distance ramp.** Measuring the edge's 10–90 width per pixel and laying a ramp of that
width along the outline was tried and rejected. On low-contrast paper the width measurement is
inflated by noise: the median read 6.1 to 7.9 px where a sharp edge should read about 2. The ramp
washed out the torn paper fibre and bled backdrop colour into the product.

## What works

**Colour separates all three.** The backdrop is neutral white. The shadow is that same white under
less light, so the shadow stays neutral: measured chroma at most 0.60, 0.18, 2.60 and 4.18 on four
designs. Only the product carries colour. One test on chroma therefore tells the product from the
backdrop _and_ from its own shadow.

Coverage is linear in chroma, because a neutral backdrop adds the same amount to red, green and
blue and so adds no colour. That gives `alpha = chroma / c0`, with `c0` the product's own measured
colour, read per photograph by `paper()`. The fence is `c0 / 2`, with hysteresis at `WEAK = 2.8` so
a pale patch stays attached without letting the shadow in.

**The outline is measured, the edge is solved.** `cut()` runs in two stages.

1. `field`, `seed`, `paper` and `corrected_outline_f` find _where the edge runs_, to within a few
   pixels. They walk the normal at every contour point and take the half-crossing of the inside
   plateau. Two cues are used, each only where it is valid: chroma wherever its jump is at least
   `MINJUMP = 2.5`, and brightness only where the outside is clean white (L ≥ 246) and its jump is
   at least 6.
2. `matte` turns that outline into a trimap — definite product, definite backdrop, and a `BAND = 6`
   px strip of unknown between them — and hands it to closed-form matting
   (`pymatting.estimate_alpha_cf`, `EPS = 1e-5`). The solver decides coverage inside the strip
   under the rule that neighbouring pixels of one colour share one coverage.

The division of labour is the point. **The measurement places the edge**, which the models get
wrong because of the shadow. **The solver shapes it**, which a threshold gets wrong.

## Why a threshold gives rough edges

Comb-like notches appear along every straight edge of a thresholded cut. Two causes, and the second
is the larger.

1. `np.maximum(A, al)` lets per-pixel noise in the chroma field create alpha _outside_ the smooth
   polygon: 773 speckle pixels on one design, 0 after matting.
2. **Packshots are JPEGs.** At a near-white edge the 8×8 blocks of the compression differ by one or
   two levels. Where the product carries only 5 levels of colour against the backdrop's 0, one
   level of block noise is a third of the way across. A per-pixel threshold turns the compression
   grid into a comb. Contrast-stretching the raw photograph to the range 240–256 shows the blocks.

Matting removes the comb because its smoothness prior reads _along_ the edge as well as across it,
and block noise does not survive that.

## The shape prior

Where many packshots share one product outline, that outline holds the product together where
colour cannot. `inside_shape` fits it to the colour seed and `seed` takes the union; outside the
fitted shape colour still rules, which keeps the shadow out and lets a trailing end in.

Four details decide whether the prior helps or hurts.

- **Fit to the colour seed, never to an `L < 250` silhouette.** The silhouette carries the shadow,
  so it pulls the fit toward the shadow and the fitted shape then reaches past the product.
  Measured: fitting to the silhouette put 10,168 px of shadow at 176 levels inside the shape;
  fitting to the colour seed left 394 px, all within 8 px of the seed.
- **Erode by 10 px and apply no brightness test inside.** Two of the cards had a corner blown out
  to 252 and 254, as bright as the backdrop, so a brightness test inside the shape cut a notch out
  of each corner.
- **Repair the seed before you fit.** A fit placed against a bitten mask is bitten too: on one
  design the bite dragged the fit 59 px inside the paper, and no downstream repair recovered it.
- **Punch a hole at the prior's hole, not at the colour opening.** Colour finds the whole opening
  including the bevelled wall of material around it, and that wall is product. Cutting at the outer
  rim leaves a flat disc; on one card it opened the top edge and the photograph underneath showed
  through as a grey ghost ring. Keep the photograph as a check: use the prior's hole only where the
  photograph agrees the hole is open.

## When colour fails: the hull-bounded brightness test

On a pale grey stock the colour test drops whole strips of product. Measured on one design, the
paper over its right third carried 0.9 levels against a backdrop of 0.0, and the seed lost a strip
up to 524 px wide. The strip touches the product's border rather than being enclosed by it, so
filling holes cannot bring it back.

`hull_repair` fixes it at the seed, with two tests together.

1. **Brightness.** The strip reads 218 against a backdrop of 248, so `L < 240` separates them.
2. **The product's own convex outline.** The strip is a bite in a straight edge, and a convex hull
   closes such a bite. The shadow, which also reads under 240, falls outside the product and so
   outside the hull.

The hull is the bound and never the answer, because it bridges genuine concavities: on one card the
hull stood 83 px proud of the paper at the waist. Inside those bridges the brightness test decides,
and backdrop showing through a concavity reads 248 and stays out. An admitted pixel must also join
the seed, so a dark object lying inside the hull but apart from the product cannot be taken for it.

Measured over nine designs, as how far the cut fell short of the product's edge: the worst went
from 33 px median and 103 px at worst to 12 and 41, four others improved, and none regressed.

## Clipping a trailing end

A cord or strap photographed loose trails past the product: 63, 55 and 53 px on three designs.
Where the cut is pasted onto a photograph that allows only 25, the rest lands on whatever is
behind. `reach_of` bounds the cut to the product's own convex outline grown by `OVERHANG = 30` px.

**The bound must be the product's outline, never the fitted shape prior.** A prior's sides can sit
inside the real product where the product is torn or tied differently: on one design the card stood
69 px proud of the prior's indent and a bound built from the prior took an 845 px tall strip out of
the product itself.

The bound is applied to the seed, after each outline pass, and to the matted alpha, so the edge
measurement cannot walk a trailing end back out.

## Known defect

One card's punched hole keeps about 10 px of its shaded inner wall on one side: it comes out 157 px
wide where the same punch gives 176 to 184 elsewhere. The wall stands in shade while the backdrop
behind it picks up warm light off the paper, so a ring inside the hole reads 5 to 12 where the open
backdrop reads 2. `hang_hole` grows the hole by three times what its own interior reads, capped at
three quarters of the product's colour, which recovers most but not all of it.