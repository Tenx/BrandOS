#!/usr/bin/env python3
"""Shared Etsy shop profile utilities for etsy-listing-manager scripts."""

import os
from pathlib import Path
from typing import Optional

import yaml


PROFILE_NAME = "etsy_shop_profile.yaml"


def consume_profile_arg(argv: list[str]) -> Optional[str]:
    """Remove --profile from argv before a script's own argparse runs."""
    for index, arg in list(enumerate(argv)):
        if arg == "--profile" and index + 1 < len(argv):
            value = argv[index + 1]
            del argv[index:index + 2]
            return value
        if arg.startswith("--profile="):
            value = arg.split("=", 1)[1]
            del argv[index]
            return value
    if "--help" in argv or "-h" in argv:
        return "__HELP__"
    return os.environ.get("ETSY_SHOP_PROFILE")


def find_profile(start: Optional[Path] = None) -> Path:
    """Find etsy_shop_profile.yaml from a start directory or its parents."""
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for directory in [current, *current.parents]:
        candidate = directory / PROFILE_NAME
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Could not find {PROFILE_NAME}. Run from a project directory or pass --profile."
    )


def _load_local_env(env_file: Path) -> None:
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_profile(profile_path: Optional[str] = None) -> dict:
    if profile_path == "__HELP__":
        temp_root = Path("/tmp/etsy-listing-manager-help")
        return {
            "shop": {},
            "paths": {
                "project_root": str(temp_root),
                "listing_dir": ".",
                "image_dir": ".",
                "token_file": ".etsy_token.json",
                "reports_dir": "reports",
            },
            "etsy_api": {},
            "publishing": {},
            "taxonomy": {},
            "shop_sections": {},
            "variations": {},
            "verification": {},
        }
    path = Path(profile_path).expanduser().resolve() if profile_path else find_profile()
    if not path.exists():
        raise FileNotFoundError(f"Missing Etsy shop profile: {path}")
    os.environ["ETSY_SHOP_PROFILE"] = str(path)
    profile = yaml.safe_load(path.read_text(encoding="utf-8"))
    profile["_profile_path"] = str(path)
    profile.setdefault("paths", {})
    profile["paths"].setdefault("project_root", str(path.parent))
    local_env = profile.get("etsy_api", {}).get("local_env_file")
    if local_env:
        _load_local_env(resolve_path(local_env, profile=profile))
    return profile


def resolve_path(value: str, *, profile: dict) -> Path:
    root = Path(profile["paths"]["project_root"])
    path = Path(value)
    return path if path.is_absolute() else root / path


def project_path(key: str, *, profile: dict) -> Path:
    return resolve_path(profile["paths"][key], profile=profile)


def env_or_value(mapping: dict, value_key: str, env_key: str):
    if value_key in mapping and mapping[value_key] not in (None, ""):
        return mapping[value_key]
    env_name = mapping.get(env_key)
    if env_name:
        value = os.environ.get(env_name)
        if value not in (None, ""):
            return value
    return None


def api_credentials(profile: dict) -> tuple[str, str]:
    api = profile.get("etsy_api", {})
    key = env_or_value(api, "api_key", "api_key_env")
    secret = env_or_value(api, "api_secret", "api_secret_env")
    if not key or not secret:
        raise RuntimeError(
            "Missing Etsy API credentials. Set "
            f"{api.get('api_key_env', 'ETSY_API_KEY')} and "
            f"{api.get('api_secret_env', 'ETSY_API_SECRET')}."
        )
    return str(key), str(secret)


def optional_int(mapping: dict, value_key: str, env_key: str):
    value = env_or_value(mapping, value_key, env_key)
    return int(value) if value not in (None, "") else None


def first_matching_rule(text: str, rules: list[dict], id_key: str, env_key: str):
    text = text.lower()
    for rule in rules or []:
        if any(term.lower() in text for term in rule.get("match_any", [])):
            value = env_or_value(rule, id_key, env_key)
            return int(value) if value not in (None, "") else None
    return None
