export interface Point2d {
  x: number;
  y: number;
}

export function sampleCurve(
  fn: (x: number) => number,
  start: number,
  end: number,
  steps: number
): Point2d[] {
  const safeSteps = Math.max(2, Math.floor(steps));
  return Array.from({ length: safeSteps + 1 }, (_, index) => {
    const t = index / safeSteps;
    const x = start + (end - start) * t;
    return { x, y: fn(x) };
  });
}
