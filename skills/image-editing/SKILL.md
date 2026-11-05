---
name: image-editing
description: Edit a client's product photographs for a marketplace listing — cut a product off its packshot backdrop with a true soft edge, place it on a model or lifestyle photo, build an image set, and judge the result before anything is published. Use when a client task asks for main images, image stacks, a product swapped into a photo, a background removed, or a packshot cleaned up, e.g. "build the image set for these SKUs", "put the new colourway on the model", "the edges look rough".
metadata:
  summary: 'Cut a product off its photo backdrop, place it in a lifestyle photo, and check the edges before it goes live.'
---

# Editing a client's product images

A main image is the client's shop window, so the bar is different from ordinary image work: the
product must be whole, its edge must be clean at full zoom, and nothing may be invented. This skill
is how to meet that bar and how to prove you met it.

It comes from rebuilding 57 main images for a jewellery company on Amazon in October 2026. The
method and every trap in it are measured, not assumed.

## What the operator must decide, not you

- **Which image goes live.** Build and show; the client approves. Never publish on your own.
- **Whether a product may be changed in the picture.** Recolouring, reshaping or removing a
  feature of the product misrepresents it. Only lighting, background and placement are yours.
- **Anything the photograph does not show.** If a client asks for an angle, a colourway or a
  detail you do not have a photograph of, say so and ask for the photograph. Never generate it.

## The cut

`scripts/cutout.py` cuts a product off a plain backdrop and returns coverage per pixel.

```bash
python3 scripts/cutout.py photo.jpg out.png --report
```

It needs `numpy`, `scipy`, `scikit-image`, `pillow` and `pymatting`. The output is RGBA: the alpha
channel is the coverage, 0 to 1, with a true soft edge.

When many packshots share one product outline — one die-cut, one bottle, one box — give the script
that outline as a shape prior and it holds the product together where colour cannot:

```bash
SHAPE_PRIOR=outline.npy python3 scripts/cutout.py photo.jpg out.png
```

The prior is a boolean `.npy` mask of the product's silhouette at any size; the script fits it by
scale and position. Build one from the cleanest packshot you have. Without a prior the script runs
on colour and brightness alone, which is right for a one-off photograph.

**Read [cutout.md](cutout.md) before you change the cut or explain it.** It says why the method is
colour and matting rather than a segmentation model, what each constant does, and the four faults
that a rebuild of all 57 images exposed.

## Placing the product on a photograph

**Un-premultiply the cut before you blend it.** A cut saved over a white backdrop already carries
that white in its soft pixels. Blending it again adds `A(1-A)(255-C)` of extra white, which on one
image reached 64 levels and drew a pale rim between the product and the model's hand. Recover the
product's own colour first with `Cp = P - 255*(1-A)`, then blend `out = base*(1-A) + Cp`.

**Fit body to body, never box to box.** If a strap, a cord or a cable trails past the product,
half that overhang goes into the placement and the product lands off centre. Open the thin lobes
away, fit what is left, then paste the whole cut including the overhang.

**Repaint only the seam.** Where the new product is smaller than the old one in the photograph,
repaint the ring just around it from the base photograph, and only where the base photograph is
still truthful there. Painting a wider region puts the old product, or the model's own body, back
over what the new image draws.

[compositing.md](compositing.md) has the measurements behind all three.

## Judging the result

**Never grade with the function you snapped with.** If the edge measurement both places the
outline and scores it, its number measures convergence and says nothing about accuracy. The team
read such a table as accuracy for two weeks.

Grade against the photograph instead. For each row over the middle 84 % of the product, take the
rightmost pixel of `binary_opening(L < 240, iterations=3)` and subtract the rightmost pixel of the
cut. A positive number is product the cut dropped. On a healthy cut the median lands within 2 px.

Two cautions on that metric:

- `L < 250` is not a product test. A white backdrop reads 248 to 249 in its darker corners, so the
  silhouette over-reaches by 30 to 60 px and a healthy cut scores as over-long.
- Where a trailing end is pale it reads above 240, so the test misses it and the metric reports the
  cut reaching far past the product. That is the yardstick, not a defect.

Then look at it, at 4× or more, against a saturated ground. A number cannot see a comb of notches
along a straight edge or a ghost ring inside a punched hole; the eye sees both at once.

## Showing the client

Show a before and after at the same zoom, on the same crop, side by side. One close-up of a real
defect carries more than a page of description. State what changed in plain numbers, and name what
you did not fix.

## Traps that cost days

- **A route chosen by an environment variable leaves no mark in the output.** Four rebuilds ran on
  a superseded code path because nobody set the variable, and the only symptom was that measured
  fixes did not show. Default to the current route and make the old ones opt-in.
- **Brightness alone cannot separate a product from its own shadow.** A pale patch of product and
  the shadow beside it overlap in brightness. Use colour, or bound the brightness test by the
  product's own outline.
- **A shape prior fitted to a damaged mask is damaged too.** Repair the mask first, then fit.
- **Segmentation models answer the wrong question.** They return a hard in-or-out mask; a product
  edge needs coverage between 0 and 1. Six of them were measured against the real edge and missed
  by 1 to 199 px.