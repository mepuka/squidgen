# Eval History

This page tracks judged FAO-style imgvec iterations. The public history keeps
generated SVGs, generated PNG renders, judge JSON, and score logs. It does not
publish raw fixture photos, rembg cutouts, flat intermediates, or preview
contact sheets because those contain source/reference imagery.

## Score Summary

| Iteration | Timestamp | Mean style | Min style | Mean silhouette | Min silhouette | Notes |
|---:|---|---:|---:|---:|---:|---|
| 1 | 20260510T052957Z | 1.33 | 1 | 1.33 | 1 | Baseline with forced vertical rotation. |
| 2 | 20260510T053248Z | 2.00 | 1 | 2.33 | 1 | Removed forced rotation; single-squid pose improved. |
| 3 | 20260510T053830Z | 3.33 | 2 | 3.67 | 2 | Added cleaner photo-derived interior edges, stipple, eyes, and rings. |
| 4 | 20260510T054851Z | 2.33 | 1 | 3.00 | 1 | Tested original-photo detail recovery; regressed due to watermark/raw-edge clutter. |
| 5 | 20260510T062649Z | 3.00 | 1 | 3.67 | 1 | Added stacked SVG layers and mask-derived appendage centerlines. |
| 6 | 20260510T063333Z | 3.67 | 3 | 4.33 | 3 | Split fused multi-squid masks into subject bands from projection valleys. |
| 7 | 20260510T064135Z | 3.33 | 3 | 4.33 | 4 | Reduced clutter; improved weakest silhouette floor but lost some style confidence. |
| 8 | 20260510T064627Z | 3.00 | 2 | 4.00 | 2 | Recovered full dark-background tentacles; loligo_01 reached anatomy 6 and silhouette 7. |
| 9 | 20260510T065344Z | 3.33 | 2 | 5.00 | 2 | Extended light-background recovery; improved average anatomy but over-admitted clutter. |
| 10 | 20260510T065943Z | 4.00 | 4 | 6.00 | 6 | Partial run with one malformed judge response; useful signal but not a valid full pass. |
| 11 | 20260510T070310Z | 3.00 | 3 | 5.33 | 4 | Added tolerant judge parsing and reran cleanly; scores dropped under full judging. |
| 12 | 20260510T070848Z | 3.67 | 3 | 4.67 | 4 | Tuned bolder ink, smoother outlines, larger eyes/rings, and sparser stipple. |
| 13 | 20260510T071702Z | 3.67 | 2 | 5.00 | 2 | Tested dark ridge layer; helped detail on some fixtures but hurt the stock image floor. |
| 14 | 20260510T071849Z | 4.00 | 3 | 5.33 | 3 | Kept ridge layer only for dark/pure-white backgrounds; best clean pass so far. |
| 15 | 20260510T072427Z | 3.33 | 2 | 4.33 | 3 | Tested larger eyes/rings and changed draw order; regressed, settings not kept. |
| 16 | 20260510T073346Z | 3.33 | 3 | 4.67 | 3 | Tested sparse interior detail; cleaner preview but lower judged style, settings not kept. |
| 17 | 20260510T073841Z | 3.67 | 2 | 4.33 | 3 | Tested wider sucker-ring detection; added too many mantle rings, settings not kept. |
| 18 | 20260510T074600Z | 3.00 | 2 | 5.33 | 4 | Tested external-only silhouette contours; silhouette held but style regressed, setting not kept. |
| 19 | 20260510T075038Z | 3.33 | 2 | 5.33 | 4 | Tested connected shadow-field stipple; stock fixture gained clutter, setting not kept. |
| 20 | 20260510T075621Z | 2.67 | 2 | 3.33 | 1 | Tested removing synthetic split cut-edges; broke closed silhouettes, setting not kept. |
| 21 | 20260510T100833Z | 3.33 | 2 | 3.67 | 2 | Tested thinning interior photo edges to centerlines; cleaner lines but lost anatomy, setting not kept. |
| 22 | 20260510T101734Z | 3.33 | 2 | 4.67 | 2 | Tested eye-anchored local detail; added head clutter and did not recover stock arms, setting not kept. |
| 23 | 20260510T102454Z | 2.67 | 2 | 5.00 | 4 | Tested light mask smoothing for outlines; silhouette held but style and anatomy regressed, setting not kept. |
| 24 | 20260510T102855Z | 4.33 | 3 | 5.67 | 5 | Replaced random grid stipple with photo-derived chromatophore components; new best baseline. |
| 25 | 20260510T103316Z | 4.00 | 4 | 4.33 | 4 | Tested drawing stipple below rings and eyes; style floor rose but anatomy/silhouette regressed, setting not kept. |
| 26 | 20260510T103825Z | 4.00 | 3 | 5.00 | 4 | Tested looser appendage centerlines; added clutter without recovering tentacles, setting not kept. |

## Iteration 1

- [loligo_01.svg](../out/eval/0001-20260510T052957Z/loligo_01.svg) · [png](../out/eval/0001-20260510T052957Z/loligo_01.png) · [judge](../out/eval/0001-20260510T052957Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0001-20260510T052957Z/loligo_02_isolated.svg) · [png](../out/eval/0001-20260510T052957Z/loligo_02_isolated.png) · [judge](../out/eval/0001-20260510T052957Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0001-20260510T052957Z/loligo_03.svg) · [png](../out/eval/0001-20260510T052957Z/loligo_03.png) · [judge](../out/eval/0001-20260510T052957Z/loligo_03.judge.json)

## Iteration 2

- [loligo_01.svg](../out/eval/0002-20260510T053248Z/loligo_01.svg) · [png](../out/eval/0002-20260510T053248Z/loligo_01.png) · [judge](../out/eval/0002-20260510T053248Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0002-20260510T053248Z/loligo_02_isolated.svg) · [png](../out/eval/0002-20260510T053248Z/loligo_02_isolated.png) · [judge](../out/eval/0002-20260510T053248Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0002-20260510T053248Z/loligo_03.svg) · [png](../out/eval/0002-20260510T053248Z/loligo_03.png) · [judge](../out/eval/0002-20260510T053248Z/loligo_03.judge.json)

## Iteration 3

- [loligo_01.svg](../out/eval/0003-20260510T053830Z/loligo_01.svg) · [png](../out/eval/0003-20260510T053830Z/loligo_01.png) · [judge](../out/eval/0003-20260510T053830Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0003-20260510T053830Z/loligo_02_isolated.svg) · [png](../out/eval/0003-20260510T053830Z/loligo_02_isolated.png) · [judge](../out/eval/0003-20260510T053830Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0003-20260510T053830Z/loligo_03.svg) · [png](../out/eval/0003-20260510T053830Z/loligo_03.png) · [judge](../out/eval/0003-20260510T053830Z/loligo_03.judge.json)

## Iteration 4

- [loligo_01.svg](../out/eval/0004-20260510T054851Z/loligo_01.svg) · [png](../out/eval/0004-20260510T054851Z/loligo_01.png) · [judge](../out/eval/0004-20260510T054851Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0004-20260510T054851Z/loligo_02_isolated.svg) · [png](../out/eval/0004-20260510T054851Z/loligo_02_isolated.png) · [judge](../out/eval/0004-20260510T054851Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0004-20260510T054851Z/loligo_03.svg) · [png](../out/eval/0004-20260510T054851Z/loligo_03.png) · [judge](../out/eval/0004-20260510T054851Z/loligo_03.judge.json)

## Iteration 5

- [loligo_01.svg](../out/eval/0005-20260510T062649Z/loligo_01.svg) · [png](../out/eval/0005-20260510T062649Z/loligo_01.png) · [judge](../out/eval/0005-20260510T062649Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0005-20260510T062649Z/loligo_02_isolated.svg) · [png](../out/eval/0005-20260510T062649Z/loligo_02_isolated.png) · [judge](../out/eval/0005-20260510T062649Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0005-20260510T062649Z/loligo_03.svg) · [png](../out/eval/0005-20260510T062649Z/loligo_03.png) · [judge](../out/eval/0005-20260510T062649Z/loligo_03.judge.json)

## Iteration 6

- [loligo_01.svg](../out/eval/0006-20260510T063333Z/loligo_01.svg) · [png](../out/eval/0006-20260510T063333Z/loligo_01.png) · [judge](../out/eval/0006-20260510T063333Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0006-20260510T063333Z/loligo_02_isolated.svg) · [png](../out/eval/0006-20260510T063333Z/loligo_02_isolated.png) · [judge](../out/eval/0006-20260510T063333Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0006-20260510T063333Z/loligo_03.svg) · [png](../out/eval/0006-20260510T063333Z/loligo_03.png) · [judge](../out/eval/0006-20260510T063333Z/loligo_03.judge.json)

## Iteration 7

- [loligo_01.svg](../out/eval/0007-20260510T064135Z/loligo_01.svg) · [png](../out/eval/0007-20260510T064135Z/loligo_01.png) · [judge](../out/eval/0007-20260510T064135Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0007-20260510T064135Z/loligo_02_isolated.svg) · [png](../out/eval/0007-20260510T064135Z/loligo_02_isolated.png) · [judge](../out/eval/0007-20260510T064135Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0007-20260510T064135Z/loligo_03.svg) · [png](../out/eval/0007-20260510T064135Z/loligo_03.png) · [judge](../out/eval/0007-20260510T064135Z/loligo_03.judge.json)

## Iteration 8

- [loligo_01.svg](../out/eval/0008-20260510T064627Z/loligo_01.svg) · [png](../out/eval/0008-20260510T064627Z/loligo_01.png) · [judge](../out/eval/0008-20260510T064627Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0008-20260510T064627Z/loligo_02_isolated.svg) · [png](../out/eval/0008-20260510T064627Z/loligo_02_isolated.png) · [judge](../out/eval/0008-20260510T064627Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0008-20260510T064627Z/loligo_03.svg) · [png](../out/eval/0008-20260510T064627Z/loligo_03.png) · [judge](../out/eval/0008-20260510T064627Z/loligo_03.judge.json)

## Iteration 9

- [loligo_01.svg](../out/eval/0009-20260510T065344Z/loligo_01.svg) · [png](../out/eval/0009-20260510T065344Z/loligo_01.png) · [judge](../out/eval/0009-20260510T065344Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0009-20260510T065344Z/loligo_02_isolated.svg) · [png](../out/eval/0009-20260510T065344Z/loligo_02_isolated.png) · [judge](../out/eval/0009-20260510T065344Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0009-20260510T065344Z/loligo_03.svg) · [png](../out/eval/0009-20260510T065344Z/loligo_03.png) · [judge](../out/eval/0009-20260510T065344Z/loligo_03.judge.json)

## Iteration 10

- [loligo_01.svg](../out/eval/0010-20260510T065943Z/loligo_01.svg) · [png](../out/eval/0010-20260510T065943Z/loligo_01.png) · [judge](../out/eval/0010-20260510T065943Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0010-20260510T065943Z/loligo_02_isolated.svg) · [png](../out/eval/0010-20260510T065943Z/loligo_02_isolated.png) · [judge](../out/eval/0010-20260510T065943Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0010-20260510T065943Z/loligo_03.svg) · [png](../out/eval/0010-20260510T065943Z/loligo_03.png) · [judge](../out/eval/0010-20260510T065943Z/loligo_03.judge.json)

## Iteration 11

- [loligo_01.svg](../out/eval/0011-20260510T070310Z/loligo_01.svg) · [png](../out/eval/0011-20260510T070310Z/loligo_01.png) · [judge](../out/eval/0011-20260510T070310Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0011-20260510T070310Z/loligo_02_isolated.svg) · [png](../out/eval/0011-20260510T070310Z/loligo_02_isolated.png) · [judge](../out/eval/0011-20260510T070310Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0011-20260510T070310Z/loligo_03.svg) · [png](../out/eval/0011-20260510T070310Z/loligo_03.png) · [judge](../out/eval/0011-20260510T070310Z/loligo_03.judge.json)

## Iteration 12

- [loligo_01.svg](../out/eval/0012-20260510T070848Z/loligo_01.svg) · [png](../out/eval/0012-20260510T070848Z/loligo_01.png) · [judge](../out/eval/0012-20260510T070848Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0012-20260510T070848Z/loligo_02_isolated.svg) · [png](../out/eval/0012-20260510T070848Z/loligo_02_isolated.png) · [judge](../out/eval/0012-20260510T070848Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0012-20260510T070848Z/loligo_03.svg) · [png](../out/eval/0012-20260510T070848Z/loligo_03.png) · [judge](../out/eval/0012-20260510T070848Z/loligo_03.judge.json)

## Iteration 13

- [loligo_01.svg](../out/eval/0013-20260510T071702Z/loligo_01.svg) · [png](../out/eval/0013-20260510T071702Z/loligo_01.png) · [judge](../out/eval/0013-20260510T071702Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0013-20260510T071702Z/loligo_02_isolated.svg) · [png](../out/eval/0013-20260510T071702Z/loligo_02_isolated.png) · [judge](../out/eval/0013-20260510T071702Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0013-20260510T071702Z/loligo_03.svg) · [png](../out/eval/0013-20260510T071702Z/loligo_03.png) · [judge](../out/eval/0013-20260510T071702Z/loligo_03.judge.json)

## Iteration 14

- [loligo_01.svg](../out/eval/0014-20260510T071849Z/loligo_01.svg) · [png](../out/eval/0014-20260510T071849Z/loligo_01.png) · [judge](../out/eval/0014-20260510T071849Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0014-20260510T071849Z/loligo_02_isolated.svg) · [png](../out/eval/0014-20260510T071849Z/loligo_02_isolated.png) · [judge](../out/eval/0014-20260510T071849Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0014-20260510T071849Z/loligo_03.svg) · [png](../out/eval/0014-20260510T071849Z/loligo_03.png) · [judge](../out/eval/0014-20260510T071849Z/loligo_03.judge.json)

## Iteration 15

- [loligo_01.svg](../out/eval/0015-20260510T072427Z/loligo_01.svg) · [png](../out/eval/0015-20260510T072427Z/loligo_01.png) · [judge](../out/eval/0015-20260510T072427Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0015-20260510T072427Z/loligo_02_isolated.svg) · [png](../out/eval/0015-20260510T072427Z/loligo_02_isolated.png) · [judge](../out/eval/0015-20260510T072427Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0015-20260510T072427Z/loligo_03.svg) · [png](../out/eval/0015-20260510T072427Z/loligo_03.png) · [judge](../out/eval/0015-20260510T072427Z/loligo_03.judge.json)

## Iteration 16

- [loligo_01.svg](../out/eval/0016-20260510T073346Z/loligo_01.svg) · [png](../out/eval/0016-20260510T073346Z/loligo_01.png) · [judge](../out/eval/0016-20260510T073346Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0016-20260510T073346Z/loligo_02_isolated.svg) · [png](../out/eval/0016-20260510T073346Z/loligo_02_isolated.png) · [judge](../out/eval/0016-20260510T073346Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0016-20260510T073346Z/loligo_03.svg) · [png](../out/eval/0016-20260510T073346Z/loligo_03.png) · [judge](../out/eval/0016-20260510T073346Z/loligo_03.judge.json)

## Iteration 17

- [loligo_01.svg](../out/eval/0017-20260510T073841Z/loligo_01.svg) · [png](../out/eval/0017-20260510T073841Z/loligo_01.png) · [judge](../out/eval/0017-20260510T073841Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0017-20260510T073841Z/loligo_02_isolated.svg) · [png](../out/eval/0017-20260510T073841Z/loligo_02_isolated.png) · [judge](../out/eval/0017-20260510T073841Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0017-20260510T073841Z/loligo_03.svg) · [png](../out/eval/0017-20260510T073841Z/loligo_03.png) · [judge](../out/eval/0017-20260510T073841Z/loligo_03.judge.json)

## Iteration 18

- [loligo_01.svg](../out/eval/0018-20260510T074600Z/loligo_01.svg) · [png](../out/eval/0018-20260510T074600Z/loligo_01.png) · [judge](../out/eval/0018-20260510T074600Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0018-20260510T074600Z/loligo_02_isolated.svg) · [png](../out/eval/0018-20260510T074600Z/loligo_02_isolated.png) · [judge](../out/eval/0018-20260510T074600Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0018-20260510T074600Z/loligo_03.svg) · [png](../out/eval/0018-20260510T074600Z/loligo_03.png) · [judge](../out/eval/0018-20260510T074600Z/loligo_03.judge.json)

## Iteration 19

- [loligo_01.svg](../out/eval/0019-20260510T075038Z/loligo_01.svg) · [png](../out/eval/0019-20260510T075038Z/loligo_01.png) · [judge](../out/eval/0019-20260510T075038Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0019-20260510T075038Z/loligo_02_isolated.svg) · [png](../out/eval/0019-20260510T075038Z/loligo_02_isolated.png) · [judge](../out/eval/0019-20260510T075038Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0019-20260510T075038Z/loligo_03.svg) · [png](../out/eval/0019-20260510T075038Z/loligo_03.png) · [judge](../out/eval/0019-20260510T075038Z/loligo_03.judge.json)

## Iteration 20

- [loligo_01.svg](../out/eval/0020-20260510T075621Z/loligo_01.svg) · [png](../out/eval/0020-20260510T075621Z/loligo_01.png) · [judge](../out/eval/0020-20260510T075621Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0020-20260510T075621Z/loligo_02_isolated.svg) · [png](../out/eval/0020-20260510T075621Z/loligo_02_isolated.png) · [judge](../out/eval/0020-20260510T075621Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0020-20260510T075621Z/loligo_03.svg) · [png](../out/eval/0020-20260510T075621Z/loligo_03.png) · [judge](../out/eval/0020-20260510T075621Z/loligo_03.judge.json)

## Iteration 21

- [loligo_01.svg](../out/eval/0021-20260510T100833Z/loligo_01.svg) · [png](../out/eval/0021-20260510T100833Z/loligo_01.png) · [judge](../out/eval/0021-20260510T100833Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0021-20260510T100833Z/loligo_02_isolated.svg) · [png](../out/eval/0021-20260510T100833Z/loligo_02_isolated.png) · [judge](../out/eval/0021-20260510T100833Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0021-20260510T100833Z/loligo_03.svg) · [png](../out/eval/0021-20260510T100833Z/loligo_03.png) · [judge](../out/eval/0021-20260510T100833Z/loligo_03.judge.json)

## Iteration 22

- [loligo_01.svg](../out/eval/0022-20260510T101734Z/loligo_01.svg) · [png](../out/eval/0022-20260510T101734Z/loligo_01.png) · [judge](../out/eval/0022-20260510T101734Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0022-20260510T101734Z/loligo_02_isolated.svg) · [png](../out/eval/0022-20260510T101734Z/loligo_02_isolated.png) · [judge](../out/eval/0022-20260510T101734Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0022-20260510T101734Z/loligo_03.svg) · [png](../out/eval/0022-20260510T101734Z/loligo_03.png) · [judge](../out/eval/0022-20260510T101734Z/loligo_03.judge.json)

## Iteration 23

- [loligo_01.svg](../out/eval/0023-20260510T102454Z/loligo_01.svg) · [png](../out/eval/0023-20260510T102454Z/loligo_01.png) · [judge](../out/eval/0023-20260510T102454Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0023-20260510T102454Z/loligo_02_isolated.svg) · [png](../out/eval/0023-20260510T102454Z/loligo_02_isolated.png) · [judge](../out/eval/0023-20260510T102454Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0023-20260510T102454Z/loligo_03.svg) · [png](../out/eval/0023-20260510T102454Z/loligo_03.png) · [judge](../out/eval/0023-20260510T102454Z/loligo_03.judge.json)

## Iteration 24

- [loligo_01.svg](../out/eval/0024-20260510T102855Z/loligo_01.svg) · [png](../out/eval/0024-20260510T102855Z/loligo_01.png) · [judge](../out/eval/0024-20260510T102855Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0024-20260510T102855Z/loligo_02_isolated.svg) · [png](../out/eval/0024-20260510T102855Z/loligo_02_isolated.png) · [judge](../out/eval/0024-20260510T102855Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0024-20260510T102855Z/loligo_03.svg) · [png](../out/eval/0024-20260510T102855Z/loligo_03.png) · [judge](../out/eval/0024-20260510T102855Z/loligo_03.judge.json)

## Iteration 25

- [loligo_01.svg](../out/eval/0025-20260510T103316Z/loligo_01.svg) · [png](../out/eval/0025-20260510T103316Z/loligo_01.png) · [judge](../out/eval/0025-20260510T103316Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0025-20260510T103316Z/loligo_02_isolated.svg) · [png](../out/eval/0025-20260510T103316Z/loligo_02_isolated.png) · [judge](../out/eval/0025-20260510T103316Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0025-20260510T103316Z/loligo_03.svg) · [png](../out/eval/0025-20260510T103316Z/loligo_03.png) · [judge](../out/eval/0025-20260510T103316Z/loligo_03.judge.json)

## Iteration 26

- [loligo_01.svg](../out/eval/0026-20260510T103825Z/loligo_01.svg) · [png](../out/eval/0026-20260510T103825Z/loligo_01.png) · [judge](../out/eval/0026-20260510T103825Z/loligo_01.judge.json)
- [loligo_02_isolated.svg](../out/eval/0026-20260510T103825Z/loligo_02_isolated.svg) · [png](../out/eval/0026-20260510T103825Z/loligo_02_isolated.png) · [judge](../out/eval/0026-20260510T103825Z/loligo_02_isolated.judge.json)
- [loligo_03.svg](../out/eval/0026-20260510T103825Z/loligo_03.svg) · [png](../out/eval/0026-20260510T103825Z/loligo_03.png) · [judge](../out/eval/0026-20260510T103825Z/loligo_03.judge.json)
