from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_contract(simulation: dict[str, Any]) -> str:
    return json.dumps(simulation, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def contract_hash(simulation: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_contract(simulation).encode("utf-8")).hexdigest()


def scene_actions(simulation: dict[str, Any]) -> set[str]:
    return {scene["action"] for scene in simulation.get("scenes", [])}


def required_checks_for(simulation: dict[str, Any]) -> set[str]:
    simulation_type = simulation.get("type")
    actions = scene_actions(simulation)
    if simulation_type == "surface_of_revolution":
        return {
            "domain_is_valid",
            "derivative_exists_on_interval",
            "surface_parametrization_matches_axis",
            "area_formula_matches_surface_of_revolution",
        }
    if simulation_type == "indefinite_integral":
        return {
            "integrand_matches_statement",
            "visual_domain_avoids_singularities",
            "weierstrass_substitution_is_valid",
            "rational_integrand_matches_substitution",
            "partial_fractions_match",
            "antiderivative_differentiates_to_integrand",
        }
    if simulation_type == "function_graph":
        required = {
            "function_expression_is_valid",
            "visual_domain_is_ordered",
            "declared_points_match_function",
            "declared_intervals_match_function",
            "declared_asymptotes_match_function",
            "declared_discontinuities_match_function",
        }
        derivative_actions = {
            "show_tangent",
            "show_extrema",
            "show_inflection",
            "show_derivative_graph",
            "compare_function_and_derivative",
        }
        if "derivative" in simulation.get("math", {}) or actions & derivative_actions:
            required.add("derivative_matches_function")
        if "antiderivative" in simulation.get("math", {}) or "show_antiderivative_graph" in actions:
            required.add("antiderivative_matches_function")
        return required
    return set()


def allowed_actions_for(simulation_type: str) -> set[str]:
    shared = {"draw_axes", "show_formula", "show_validation"}
    if simulation_type == "surface_of_revolution":
        return shared | {
            "draw_curve",
            "highlight_interval",
            "show_rotation_axis",
            "rotate_curve_into_surface",
            "move_camera",
        }
    if simulation_type == "indefinite_integral":
        return shared | {
            "draw_integrand_graph",
            "sweep_signed_area",
            "draw_primitive_curve",
            "show_primitive_family",
            "introduce_substitution",
            "transform_integrand",
            "split_partial_fractions",
            "integrate_terms",
            "back_substitute",
            "verify_derivative",
        }
    if simulation_type == "function_graph":
        return shared | {
            "draw_function_graph",
            "trace_point",
            "show_tangent",
            "show_extrema",
            "show_inflection",
            "show_asymptote",
            "show_discontinuity",
            "show_derivative_graph",
            "show_antiderivative_graph",
            "compare_function_and_derivative",
        }
    return set()


def validate_contract_semantics(simulation: dict[str, Any]) -> None:
    simulation_type = simulation.get("type", "")
    actions = scene_actions(simulation)
    illegal_actions = actions - allowed_actions_for(simulation_type)
    if illegal_actions:
        raise ValueError(f"Actions not allowed for {simulation_type}: {sorted(illegal_actions)}")

    missing_checks = required_checks_for(simulation) - set(simulation.get("checks", []))
    if missing_checks:
        raise ValueError(f"Missing required checks for {simulation_type}: {sorted(missing_checks)}")

    parameter_names = set(simulation.get("parameters", {}).keys())
    slider_names = set(simulation.get("controls", {}).get("parameter_sliders", []))
    unknown_sliders = slider_names - parameter_names
    if unknown_sliders:
        raise ValueError(f"Parameter sliders reference unknown parameters: {sorted(unknown_sliders)}")

    features = simulation.get("features", {})
    target_ids = {
        item["id"]
        for collection in ("special_points", "highlighted_intervals")
        for item in features.get(collection, [])
    }
    if target_ids:
        for scene in simulation.get("scenes", []):
            unknown_targets = set(scene.get("targets", [])) - target_ids
            if unknown_targets:
                raise ValueError(
                    f"Scene {scene['id']} references unknown targets: {sorted(unknown_targets)}"
                )
            point_id = scene.get("args", {}).get("point_id")
            if point_id and point_id not in target_ids:
                raise ValueError(f"Scene {scene['id']} references unknown point_id: {point_id}")
