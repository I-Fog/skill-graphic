export type SimulationType = "surface_of_revolution";

export type SceneAction =
  | "draw_axes"
  | "draw_curve"
  | "highlight_interval"
  | "show_rotation_axis"
  | "rotate_curve_into_surface"
  | "move_camera"
  | "show_formula"
  | "show_validation";

export interface SimulationScene {
  id: string;
  goal: string;
  action: SceneAction;
  duration_ms?: number;
  caption?: string;
  formula?: string;
}

export interface SimulationContract {
  id: string;
  type: SimulationType;
  title: string;
  language: "es" | "en";
  parameters: Record<string, {
    value: number | string;
    domain: string;
    min?: number;
    max?: number;
    step?: number;
    label?: string;
  }>;
  math: {
    function: string;
    variable: string;
    domain: [string, string];
    rotation_axis: "x" | "y" | "z";
  };
  scenes: SimulationScene[];
  checks: string[];
}
