/** Avatar pose model + gesture library. Pure data - no React. Angles are degrees, "outward-positive". */

export type Fingers = [number, number, number, number, number]; // thumb, index, middle, ring, pinky (0..1 extension)

export interface ArmPose {
  sh: number; // upper-arm rotation at the shoulder (positive = swing outward)
  el: number; // forearm rotation at the elbow, relative to the upper arm
  wr: number; // wrist tilt
  fingers: Fingers;
  spread: number; // finger fan-out in degrees
}

export interface Pose {
  armL: ArmPose; // the arm on the viewer's left. The right arm is drawn mirrored with the same convention.
  armR: ArmPose;
  head: { rot: number; tx: number; ty: number };
  gaze: { x: number; y: number }; // -1..1
  brow: { l: number; r: number; furrow: number }; // lift 0..1
  mouth: { open: number; wide: number; smile: number };
  blink: number; // 0 open .. 1 closed
  breath: number; // -1..1
}

const OPEN: Fingers = [1, 1, 1, 1, 1];
const RELAX: Fingers = [0.55, 0.72, 0.78, 0.72, 0.62];
const SOFT: Fingers = [0.7, 0.9, 0.95, 0.9, 0.8];
const POINT: Fingers = [0.35, 1, 0.3, 0.3, 0.3];

const P = (sh: number, el: number, fingers: Fingers, spread: number, wr = 0): ArmPose => ({ sh, el, wr, fingers, spread });

export const REST_ARM = P(12.5, -60.6, RELAX, 5, 6);

export interface Gesture {
  L: ArmPose;
  R: ArmPose;
}

export const GESTURES = {
  rest: { L: REST_ARM, R: REST_ARM },
  presentR: { L: REST_ARM, R: P(6, 112, OPEN, 16) },
  presentRHigh: { L: REST_ARM, R: P(14, 122, OPEN, 14) },
  presentL: { L: P(6, 112, OPEN, 16), R: REST_ARM },
  presentLHigh: { L: P(14, 122, OPEN, 14), R: REST_ARM },
  presentBoth: { L: P(6, 112, OPEN, 16), R: P(6, 112, OPEN, 16) },
  welcome: { L: P(1, 79, OPEN, 18), R: P(1, 79, OPEN, 18) },
  pointR: { L: REST_ARM, R: P(9, 133.6, POINT, 4) },
  chestR: { L: REST_ARM, R: P(25.7, -133, SOFT, 4) },
  wave: { L: REST_ARM, R: P(69, 120, OPEN, 20) },
  moment: { L: REST_ARM, R: P(8, 108, OPEN, 12) },
  beat: { L: P(5, 80, SOFT, 10), R: P(5, 80, SOFT, 10) },
} satisfies Record<string, Gesture>;

export type GestureName = keyof typeof GESTURES;

export const SPEAKING_GESTURES: [GestureName, number][] = [
  ["presentR", 3], ["presentL", 2], ["presentBoth", 2], ["pointR", 1.5], ["chestR", 1], ["beat", 2], ["presentRHigh", 1.5], ["welcome", 1], ["presentLHigh", 1],
];

export const initialPose = (): Pose => ({
  armL: { ...REST_ARM, fingers: [...REST_ARM.fingers] as Fingers },
  armR: { ...REST_ARM, fingers: [...REST_ARM.fingers] as Fingers },
  head: { rot: 0, tx: 0, ty: 0 },
  gaze: { x: 0, y: 0 },
  brow: { l: 0, r: 0, furrow: 0 },
  mouth: { open: 0, wide: 0.3, smile: 0.5 },
  blink: 0,
  breath: 0,
});
