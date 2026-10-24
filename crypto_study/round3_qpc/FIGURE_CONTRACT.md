# Figure contract

Backend: Python/matplotlib, following the user's prior explicit choice. Quantitative two-panel grid, 7.2 by 3.4 inches. Export PDF/SVG with editable font text and PNG preview. Data: AUDIT.json only, corrected registered run; no generated or imputed values.

Claim: a smaller representation does not imply lower local processing time relative to the native binary baseline; the observed ordering differs across representation/host combinations. Panel A: worst within-cell byte ratio. Panel B: median within-pair total-time ratio. Three groups: reference JSON bitmap, reference binary bitmap, external compact. Denominators are binary-full within the reference and ordinary within the external host. No cross-language speed comparison.

Each point is a cell summary (12,12,24 points), each derived from three fixtures and 21 paired technical repeats per fixture. Domain 1/2 use different markers. Vertical offsets only prevent overlap, with no statistical meaning. No CI, inferential boxplot or significance stars. X=1 denotes equal cost. Byte axis is logarithmic; time axis linear. All cells and both domains included. Caption must explain existing versus fresh domains and method-specific denominators.
