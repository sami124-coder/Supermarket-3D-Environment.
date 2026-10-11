#!/usr/bin/env python3
"""Offline spatial/budget audit, not a substitute for a Unity lighting review.

Checks authored light targets against ranges, spot cones at key retail locations,
reflection influence coverage, and the explicit real-time shadow budget. Does not
claim to model occlusion, surface response, exposure, or a baked image.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESET = ROOT / "Assets/Settings/SipoCinematicLighting.json"


def vector(value, label):
    assert isinstance(value, list) and len(value) == 3, f"{label}: expected three values"
    assert all(isinstance(x, (int, float)) and math.isfinite(x) for x in value), label
    return value


def distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def illuminates(light, point):
    """Geometric cone/range coverage only; no claim about occlusion or brightness."""
    pos = light["position"]
    offset = [x - y for x, y in zip(point, pos)]
    dist = distance(point, pos)
    if not 0.01 < dist < light["range"] * 0.9:
        return False
    if light["type"] == "point":
        return True
    axis = [x - y for x, y in zip(light["target"], pos)]
    axis_length = math.sqrt(sum(x * x for x in axis))
    cosine = sum(x * y for x, y in zip(offset, axis)) / (dist * axis_length)
    return cosine > math.cos(math.radians(light["spotAngle"] * 0.46))


def main():
    config = json.loads(PRESET.read_text())
    metadata = json.loads((ROOT / "Assets/Environment/scene-data.json").read_text())
    assert config["schemaVersion"] == 1
    assert 0 < config["lightIntensityMultiplier"] <= 4
    lights = config["lights"]
    assert 20 <= len(lights) <= 40, "Unexpected total light budget"
    assert len({l["name"] for l in lights}) == len(lights), "Duplicate light names"
    shadows = [l for l in lights if l["shadow"] and not l["bakeOnly"]]
    assert len(shadows) <= 3 and all(l["type"] == "spot" for l in shadows), "Real-time shadow budget exceeded"
    bounds = metadata["environmentBounds"]
    for light in lights:
        name = light["name"]
        pos = vector(light["position"], name + " position")
        target = vector(light["target"], name + " target")
        color = vector(light["color"], name + " color")
        assert light["type"] in ("spot", "point"), name
        assert all(0 <= x <= 1 for x in color), name + " color is not sRGB in [0,1]"
        assert 0 < light["intensity"] <= 250 and 0 < light["range"] <= 35, name
        assert 1 < light["spotAngle"] < 150, name
        assert all(abs(p - c) < s / 2 for p, c, s in zip(pos, bounds["center"], bounds["size"])), name + " is outside environment bounds"
        assert 0.1 < distance(pos, target) < light["range"] * 0.9, name + " cannot reach target effectively"

    landmarks = {
        "arrival": [0, 1.5, 24],
        "reception": [0, 1.2, 3],
        "mascot": [-8.52, 10.75, 4.83],
        "ceiling": [0, 15.5, -3],
        "produce": [-14.2, 1.4, -2],
        "drinks island": [10, 1.2, 6],
        "escalators": [16, 4, -14],
        "checkout": [25, 1.5, 16],
        "west upper lounge": [-26, 8.2, 14],
        "east upper lounge": [26, 8.2, 14],
        "west lower aisle": [-27, 1, 7],
        "east lower aisle": [27, 1, 7],
    }
    for department in metadata["departments"]:
        pos = department["position"][:]
        pos[1] += 1.5
        landmarks[department["name"]] = pos
    uncovered = [name for name, pos in landmarks.items() if not any(illuminates(l, pos) for l in lights)]
    assert not uncovered, "Landmarks outside light cones/ranges: " + str(uncovered)

    probes = config["reflections"]
    assert len(probes) <= 6
    assert len({p["name"] for p in probes}) == len(probes)
    assert sum(p["resolution"] > 256 for p in probes) <= 1
    for probe in probes:
        name = probe["name"]
        pos = vector(probe["position"], name)
        center = vector(probe["center"], name)
        size = vector(probe["size"], name)
        assert probe["resolution"] in (128, 256, 512)
        assert all(x > 0 for x in size)
        assert all(abs(x - c) <= s / 2 for x, c, s in zip(pos, center, size)), name + " capture lies outside influence"
    for name, pos in landmarks.items():
        assert any(all(abs(x - c) <= s / 2 for x, c, s in zip(pos, p["center"], p["size"])) for p in probes), name + " lacks reflection influence"
    estimated_mip_texels = sum(6 * p["resolution"] ** 2 * 4 / 3 for p in probes)
    print("SIPO_CINEMATIC_LAYOUT_VALIDATION_PASSED")
    print(json.dumps({
        "lights": len(lights),
        "spotLights": sum(l["type"] == "spot" for l in lights),
        "pointLights": sum(l["type"] == "point" for l in lights),
        "realTimeShadowFaces": len(shadows),
        "reflectionProbes": len(probes),
        "reflectionMemoryEstimateRGBAHalfMiB": round(estimated_mip_texels * 8 / 1024 ** 2, 1),
        "landmarksWithGeometricLightAndReflectionCoverage": len(landmarks),
        "nativeRenderedAppearanceVerified": False,
    }, indent=2))


if __name__ == "__main__":
    main()
