# Placing a cut product on a photograph

Three faults account for nearly every complaint about a composite. Each one is measured.

## The pale rim: un-premultiply before blending

A cut saved as RGB over a white backdrop already carries that white in its soft pixels:
`P = A*C + (1-A)*255`. Blending it again as `out = base*(1-A) + P*A` adds `A(1-A)(255-C)` of extra
white. Measured on one image: up to 64.3 levels, 16.9 on average, and 10.4 on average over the 329
pixels where the product's edge lay on the model's skin. That extra white is the pale gap clients
report between a product and the hand holding it.

Recover the product's own colour first, then blend:

```python
Cp = P - 255.0 * (1 - A)
out = base * (1 - A) + Cp
```

Keeping the alpha channel through to the paste avoids the whole problem: paste RGBA and let the
imaging library do it.

## The off-centre product: fit body to body

Fitting the product's whole bounding box centres the trailing ends along with it, and half that
overhang goes into the placement. The product lands off centre and whatever was underneath shows
along the opposite edge as a ragged strip. Measured as how far the old product showed past the new
one: 4,650 px and 3,078 px on two designs, against a median of 90.

Open the thin lobes away with `binary_opening`, keep the largest piece, fit that body against the
body it replaces, then paste the whole cut with its overhang. Across five designs checked both
ways, the miss fell on every one: 132 → 19, 276 → 66, 885 → 204.

## The painted-over model: repaint only the seam

Where the new product is smaller than the one in the photograph, a ring of the old one is left
showing. The repair is to repaint that ring from the base photograph — and only the ring.

Two limits, both learned by breaking them.

- **Repaint a ring, not a region.** Filling everything the old product covered paints the base
  photograph's own body back over what the new image draws, which on one image put the model's
  shoulder back over her repositioned arm.
- **Decide per pixel whether the base photograph is still truthful there.** Measured on one image,
  12,782 of the 14,663 px of the old product's footprint outside the new product were neutral
  (R−B under +5) while the product's interior was +19. That strip was the model's shirt in shadow,
  not product. Only the warm pixels were still product, and only those belong in the repaint.

## Checking a composite

Three numbers, all cheap, all per image:

- **`ring_bad`** — pixels in a 22 px ring outside the pasted product that match neither the base
  photograph nor the backdrop. Anything else there is a leak: a rim, a drawn-in patch, or a
  leftover of the old product.
- **`uncovered`** — pixels of the old product's body that the new one does not cover.
- **`miss` and `extra`** from the placement fit.

A rebuild that improves the cut should move all three down together. When one moves the other way,
the cut changed something the placement depended on.