import { expect, test } from "@playwright/test";

const DEFAULT_URL = "http://127.0.0.1:8765/dist/function-graph-cubic.html";
const simulationUrl = process.env.FUNCTION_GRAPH_URL || DEFAULT_URL;
const derivativeCurveId = "curve-derivative-0";
const primitiveCurveId = "curve-antiderivative-0";

function withParams(params: Record<string, string | number>) {
  const url = new URL(simulationUrl);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, String(value));
  }
  url.searchParams.set("cb", String(Date.now()));
  return url.toString();
}

test.describe("function graph renderer", () => {
  test("keeps scene navigation exact and reversible", async ({ page }) => {
    await page.goto(withParams({ ms: 0 }));

    const sceneId = async () => page.evaluate(() => {
      const payload = JSON.parse(document.getElementById("simulation-data")!.textContent!);
      const duration = payload.renderModel.timeline.duration_ms;
      const ms = Number((document.getElementById("timeline") as HTMLInputElement).value) * duration;
      const scenes = payload.renderModel.timeline.scenes;
      if (ms <= 0) return scenes[0].id;
      if (ms >= duration) return scenes[scenes.length - 1].id;
      return scenes.find((scene: { start_ms: number; end_ms: number }) => ms >= scene.start_ms && ms < scene.end_ms).id;
    });

    await expect.poll(sceneId).toBe("axes");
    await page.locator("#next").click();
    await expect.poll(sceneId).toBe("curve");
    await page.locator("#next").click();
    await expect.poll(sceneId).toBe("trace");
    await page.locator("#prev").click();
    await expect.poll(sceneId).toBe("curve");
  });

  test("maps scene boundaries as half-open intervals", async ({ page }) => {
    await page.goto(withParams({ ms: 0 }));

    const boundaryState = await page.evaluate(() => {
      const debug = (window as any).__functionGraphDebug;
      const scenes = debug.model.timeline.scenes;
      const duration = debug.model.timeline.duration_ms;
      return scenes.flatMap((scene: { id: string; start_ms: number; end_ms: number }, index: number) => {
        const rows = [
          { probe: `${scene.id}:start`, scene: debug.sceneAt(scene.start_ms).scene.id },
          { probe: `${scene.id}:end-minus-one`, scene: debug.sceneAt(Math.max(0, scene.end_ms - 1)).scene.id },
        ];
        if (index < scenes.length - 1) {
          rows.push({ probe: `${scene.id}:end`, scene: debug.sceneAt(scene.end_ms).scene.id });
        } else {
          rows.push({ probe: `${scene.id}:duration`, scene: debug.sceneAt(duration).scene.id });
        }
        return rows;
      });
    });

    for (const row of boundaryState) {
      const [sceneId, probe] = row.probe.split(":");
      if (probe === "end" && sceneId !== "validation") {
        continue;
      }
      expect(row.scene).toBe(sceneId);
    }
    expect(boundaryState.find((row) => row.probe === "axes:end")!.scene).toBe("curve");
    expect(boundaryState.find((row) => row.probe === "curve:end")!.scene).toBe("trace");
  });

  test("renders derivative and primitive curves visibly inside the SVG", async ({ page }) => {
    const curveState = async (ms: number, domId: string) => {
      await page.goto(withParams({ ms }));
      return page.evaluate((curveId) => {
        const path = document.getElementById(curveId) as SVGPathElement;
        const rect = path.getBoundingClientRect();
        const svg = document.getElementById("plot")!.getBoundingClientRect();
        const style = getComputedStyle(path);
        return {
          className: path.getAttribute("class"),
          dLength: (path.getAttribute("d") || "").length,
          inside: rect.left >= svg.left - 2 && rect.top >= svg.top - 2 && rect.right <= svg.right + 2 && rect.bottom <= svg.bottom + 2,
          opacity: Number(style.opacity),
          stroke: style.stroke,
        };
      }, domId);
    };

    const derivative = await curveState(7350, derivativeCurveId);
    expect(derivative.dLength).toBeGreaterThan(100);
    expect(derivative.inside).toBe(true);
    expect(derivative.opacity).toBeGreaterThan(0.9);
    expect(derivative.stroke).not.toBe("none");

    const primitive = await curveState(8650, primitiveCurveId);
    expect(primitive.className).toContain("primitive");
    expect(primitive.dLength).toBeGreaterThan(100);
    expect(primitive.inside).toBe(true);
    expect(primitive.opacity).toBeGreaterThan(0.9);
    expect(primitive.stroke).not.toBe("none");
  });

  test("preserves exact millisecond scene on reload", async ({ page }) => {
    await page.goto(withParams({ ms: 7500 }));
    await expect(page.locator("#caption strong")).toContainText("Conectar la funcion con una primitiva.");
    await page.reload();
    await expect(page.locator("#caption strong")).toContainText("Conectar la funcion con una primitiva.");
  });

  test("keeps mobile overlay and controls separated", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 760 });
    await page.goto(withParams({ ms: 8100 }));
    const state = await page.evaluate(() => {
      const footer = document.querySelector("footer")!.getBoundingClientRect();
      const formula = document.getElementById("formula-panel")!.getBoundingClientRect();
      const caption = document.getElementById("caption")!.getBoundingClientRect();
      return {
        overlapFormulaFooter: formula.bottom > footer.top,
        overlapCaptionFormula: formula.top > 0 && caption.bottom > formula.top,
      };
    });
    expect(state.overlapFormulaFooter).toBe(false);
    expect(state.overlapCaptionFormula).toBe(false);
  });
});
