![full_stitch](assets/full_stitch.gif)

# Repository Overview

**Author:** David Wang Johansen <br>
**Email:** s214743@dtu.dk

This repository implements an end-to-end CT reconstruction and 3D volume stitching pipeline. The gif shown above is the result of stitching 11 CT scans into one unified volume of a T-rex.

For a non-technical report detailing the problems and solutions, with visualizations and comparisons, see **`report.md`**.

The pipeline performs:
1. FDK reconstruction using padded projections to reduce ROI artifacts - see the notebook **`padding.ipynb`** for detailed technical explanation.
2. 3D volumetric stitching of the reconstructions using registration - see the notebook **`stitching.ipynb`** for detailed explanation.

The codebase contains a combination of reusable and dataset-specific modules and scripts.

# How to Run
This section describes how to reproduce the results for the T-rex skull given the dataset is available. Of course, the pipeline can be modified to work for other datasets as well.

## Environment Variables
Start by setting the required environment variables `SCAN_ROOT` and `OUT_ROOT`.
- `SCAN_ROOT`: directory containing raw projection data
- `OUT_ROOT`: directory where reconstructions and stitched volumes are written

Select the dataset:
```
DATASET=full_res | downsampled | raw
```

## Reconstruction

```
DATASET=<dataset> python -m scripts.reconstruct
```
`<dataset>`:
- `full_res`: does FDK padded reconstruction on full resolution.
- `downsampled`: downsampled version of `full_res`. Run `python -m scripts.downsample_recons` after having reconstructed `full_res`.
- `raw`: only does FDK reconstruction

## Stitching

Stitching is organized hierarchically. Pairwise registrations are first computed between individual scans, then merged into progressively larger volumes until a single unified volume is obtained.

Run an individual stitching step with:
```
DATASET=<dataset> python -m scripts.stitch_pipeline <step>
```

The hierarchical dependency of the steps is as follows:
```
step_4_10   step_4_23   step_3_10   step_3_23   step_2
    │           │           │           │          │
    └─────┬─────┘           └─────┬─────┘          │
          │                       │                │
       step_4                  step_3          step_21
          │                       │                │
          └──────────────┬────────┘                │
                         │                         │
                      step_43                      │
                         │                         │
                         └──────────────┬──────────┘
                                        │
                                    step_4321
```
E.g., `step_4` depends on `step_4_10` and `step_4_23`, `step_43` depends on `step_4` and `step_3`, and so on.

The final output of `step_4321` consists of the fully assembled specimen.

The result of `step_4321` can be visualized slice-wise and interactively in `notebooks/viz_full_res_stitch.ipynb`.

# Dependencies
A conda environment is required to run the full pipeline due to the use of `cil` for CT reconstruction. If only doing stitching, the `pip` packages are sufficient.

**conda:**
- python=3.11.9
- cil=24.1.0 (installation guide at https://github.com/TomographicImaging/CIL?tab=readme-ov-file#installation-of-cil)

**pip:**
```
antspyx==0.6.2
qim3d==1.4.0
numpy==1.26.4
scipy==1.14.0
h5py==3.11.0
memory-profiler==0.61.0
```

Other minor version variations may be compatible.
