export interface SurfaceSample {
  x: number;
  y: number;
  z: number;
}

export function sampleSurfaceOfRevolution(
  radiusFunction: (x: number) => number,
  x: number,
  theta: number
): SurfaceSample {
  const radius = radiusFunction(x);
  return {
    x,
    y: radius * Math.cos(theta),
    z: radius * Math.sin(theta),
  };
}
