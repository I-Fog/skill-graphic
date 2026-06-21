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


def _register_id(registry: dict[str, str], item_id: str, owner: str) -> None:
    previous = registry.get(item_id)
    if previous:
        raise ValueError(f"Duplicate id {item_id!r} used by {previous} and {owner}.")
    registry[item_id] = owner


def _feature_maps(simulation: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    features = simulation.get("features", {})
    return {
        "points": {item["id"]: item for item in features.get("special_points", [])},
        "intervals": {item["id"]: item for item in features.get("highlighted_intervals", [])},
        "asymptotes": {item["id"]: item for item in features.get("vertical_asymptotes", [])},
        "discontinuities": {item["id"]: item for item in features.get("discontinuities", [])},
    }


def _validate_unique_ids(simulation: dict[str, Any]) -> None:
    registry: dict[str, str] = {}
    for scene in simulation.get("scenes", []):
        _register_id(registry, scene["id"], f"scene:{scene['action']}")

    features = simulation.get("features", {})
    for collection in (
        "special_points",
        "highlighted_intervals",
        "vertical_asymptotes",
        "discontinuities",
    ):
        for item in features.get(collection, []):
            _register_id(registry, item["id"], f"features.{collection}")


def _require_targets(scene: dict[str, Any], allowed_ids: set[str], label: str) -> None:
    targets = set(scene.get("targets", []))
    if not targets:
        raise ValueError(f"Scene {scene['id']} action {scene['action']} requires {label} targets.")
    wrong = targets - allowed_ids
    if wrong:
        raise ValueError(
            f"Scene {scene['id']} action {scene['action']} has incompatible targets: {sorted(wrong)}"
        )


def _validate_scene_targets(simulation: dict[str, Any]) -> None:
    simulation_type = simulation.get("type", "")
    maps = _feature_maps(simulation)
    all_target_ids = set().union(*(collection.keys() for collection in maps.values()))

    for scene in simulation.get("scenes", []):
        unknown_targets = set(scene.get("targets", [])) - all_target_ids
        if unknown_targets:
            raise ValueError(
                f"Scene {scene['id']} references unknown targets: {sorted(unknown_targets)}"
            )

        point_id = scene.get("args", {}).get("point_id")
        if point_id and point_id not in maps["points"]:
            raise ValueError(f"Scene {scene['id']} references unknown point_id: {point_id}")

        action = scene["action"]
        point_ids = set(maps["points"].keys())
        interval_ids = set(maps["intervals"].keys())
        asymptote_ids = set(maps["asymptotes"].keys())
        discontinuity_ids = set(maps["discontinuities"].keys())
        extrema_ids = {
            item_id for item_id, item in maps["points"].items() if item.get("kind") == "extremum"
        }
        inflection_ids = {
            item_id for item_id, item in maps["points"].items() if item.get("kind") == "inflection"
        }

        if action == "highlight_interval" and simulation_type == "function_graph":
            _require_targets(scene, interval_ids, "interval")
        elif action == "trace_point":
            if scene.get("targets"):
                _require_targets(scene, point_ids, "point")
        elif action == "show_tangent":
            if not point_id:
                raise ValueError(f"Scene {scene['id']} action show_tangent requires args.point_id.")
            if scene.get("targets"):
                _require_targets(scene, point_ids, "point")
        elif action == "show_extrema":
            _require_targets(scene, extrema_ids, "extremum point")
        elif action == "show_inflection":
            _require_targets(scene, inflection_ids, "inflection point")
        elif action == "show_asymptote":
            _require_targets(scene, asymptote_ids, "asymptote")
        elif action == "show_discontinuity":
            _require_targets(scene, discontinuity_ids, "discontinuity")


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

    _validate_unique_ids(simulation)
    _validate_scene_targets(simulation)
