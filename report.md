# Introduction

Imagine you want to CT scan an object that is too large for the field of view of a cone-beam CT scanner. Therefore, you decide to scan parts of it, each scan capturing a subregion of the object. That was the case with the baby dinosaur skull from a T-rex called Casper that was scanned using a micro-CT scanner at DTU 3D imaging center. This required 11 scans, distributed over 4 layers as visualized in the figure below.

<figure>
    <img src="assets/layer_sketch.png" width="800">
    <figcaption>
        Sketch of the scan layout. The overlap is a rough approximation for visualization purposes. 11 scans are distributed over the 4 layers.
    </figcaption>
</figure>

This introduces two problems
- The region of interest problem. 
- The stitching problem.

# The region of interest problem
A CT scanner sends X-rays through an object from multiple angles by rotating about an axis. In our scenario, the object extends out of the field of view of the CT-scanner. Because of that, large parts of the object are not actually hit by the X-rays. The part of the object not being hit changes at each angle, which creates inconsistency in the CT model, where it is assumed that every part of the object is always hit by a ray. Doing the reconstruction despite this results in a volume containing region of interest artifacts. See the Figure below for an example from one of the Casper scans. These show up as cylindrical artifacts centered around the rotation axis. Furthermore, there is an artificial non-linear intensity gradient increase as you move away from the center. Even though we do not know how the "ideal" data should have looked like, we apply a data augmentation technique padding. The reconstruction of this augmented data is also seen in the Figure below. It is seen that it is highly effective at mitigating the artifacts.

<figure>
    <img src="assets/top_4_3-raw_vs_padded.png" width="800">
    <figcaption>
        Left: without padding (raw data), Right: with padding (augmented data)
    </figcaption>
</figure>

This technique is then applied on all individual scans before moving on to the next step.

## Note about proprietary reconstruction
Normally, the scanner will allow reconstruction with their proprietary software. This has some options to apply algorithms to correct for some of the artifacts seen in CT. However, this breaks down when suddenly it does not work as intended or does not have a method for the artifact you are dealing with. However, since they give you the reconstruction, this is extremely difficult to do anything further about since we do not know what was done to achieve this. Fortunately, the scanner also supplies the raw CT data. But that leaves us with all the artifacts, however, if we can take care of the worst offenders like in this case, we might get more satisfactory results than the proprietary reconstruction.

# The stitching problem
If we could have fit the object in one scan, we would have gotten a single complete volume. In our scenario, however, we have 11 volumes, that each may or may not partly overlap with each other.

This can be done manually in some volumetric image editing software by moving and rotating (and even scale in some cases) each scan around one-by-one and aligning based on visual judgment. But this requires a lot of nudging around and is humanly time consuming. Furthermore, it might not lead to ideal results due to potential human errors and there is a tradeoff between how much time to spend and how precise the alignments will be.

Therefore, it would be great if we could automate this process. The way we do it here is by stitching 2 volumes at a time. To do this, we need to estimate the geometric transformation that makes the overlapping regions aligned. This is done by optimizing for the numerically best alignment based on some metric. Thus, each scan must overlap to some extent with at least one other scan.

This way, the volumes are pair-wise stitched, building up each layer, whereafter the layers then are combined pairwise until they have been unified into one big volume.

In our setup, it needs to be specified which pairs to be combined, which of course requires a mental overview of which volumes are overlapping, but that would be a natural result of organizing the capture of the scans in the first place since you need to ensure every part of the object is covered. In the figures below we show side-by-side comparison of manually stitching the propriety reconstrctions vs automatically stitching using our custom reconstruction. Note that the comparisons are only of approximately corresponding slices of the object since the methods used were different.

<figure>
    <img src="assets/comparison1.png" width="800">
    <figcaption>
        Left: Previous manual stitching. Right: New automatic stitching. The red parts highlights the artifacts. On the left, there are clear circular artifacts, with the intensity transitions being completely off. This is not a problem on the right, where it is not possible to guess the stitching boundaries.
    </figcaption>
</figure>

<figure>
    <img src="assets/comparison2.png" width="400">
    <figcaption>
        Left: Previous manual stitching. Right: New automatic stitching. The red parts highlights the artifacts. Here we also see the left being more blurry than the right in the bottom red circle.
    </figcaption>
</figure>

<figure>
    <img src="assets/comparison4.png" width="800">
    <figcaption>
        Left: Previous manual stitching. Right: New automatic stitching. As seen, some part is missing on the left. This could perhaps be due to having to crop bad artifacts away.
    </figcaption>
</figure>

<figure>
    <img src="assets/comparison3.png" width="800">
    <figcaption>
        Left: Previous manual stitching. Right: New automatic stitching. More artifacts shown in red.
    </figcaption>
</figure>
