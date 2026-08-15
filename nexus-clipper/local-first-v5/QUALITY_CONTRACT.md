# NexuX V5 Media Quality Contract

Every canonical render must produce a real, decodable MP4 before a job can become `completed`.

## Required output contract

- video stream present
- audio stream present
- exact requested output width/height
- positive duration
- decodable sampled frames
- no excessive dark/black-frame ratio
- no obvious under/over-exposure according to deterministic frame sampling
- basic sharpness sanity check

## Vision signals

The local vision layer provides:

- frame-difference scene boundaries
- OpenCV face/subject observations
- media stream metadata from FFprobe
- sampled brightness/sharpness statistics

These signals are deterministic engineering signals. They are not claims of semantic object recognition or commercial editor parity.

## Failure behavior

A compositor output that fails the contract raises an error. The job remains failed and the invalid output is never reported as a successful clip.

B-roll is not part of this contract and remains disabled.
