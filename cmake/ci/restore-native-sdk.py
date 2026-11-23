"""Restore the SDK versions selected in .env.example for one CI profile."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

SOURCE = Path(__file__).resolve().parents[2]
SELECTION = {
    key: value
    for line in (SOURCE / ".env.example").read_text(encoding="utf-8").splitlines()
    if line and not line.startswith("#")
    for key, value in [line.split("=", 1)]
}
INFRA = SOURCE / "build" / "upstream" / "vcpkg-cache"
RESTORE = ["python", str(INFRA / "scripts" / "restore-native-dependency.py")]
PACKAGES = {
    "salts-base": ("SALTS_BASE", "SaltsBase"),
    "cmeta": ("CMETA", "CMeta"),
    "salts-utils": ("SALTS_UTILS", "SaltsUtils"),
}
RE2C = {
    "schema": 1,
    "source": {
        "kind": "package",
        "feed": "https://nuget.pkg.github.com/qigao/index.json",
        "id": "Qigao.Re2c.Binary",
        "version": "4.6.7",
    },
    "sha256": "fe3c64ef3c25a28a9e5143bf2e85e3a7f25691f9bf47bec490f3e6be8e461305",
}


def capture(*args):
    return json.loads(subprocess.check_output(args, text=True, encoding="utf-8"))


def verify_digest(path, expected, size):
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if path.stat().st_size != size or expected != actual:
        raise ValueError(f"SDK archive size or checksum mismatch: {path.name}")


def release_asset(repository, version, destination, asset):
    subprocess.run(
        ["gh", "release", "download", f"v{version}", "--repo", repository,
         "--pattern", asset["name"], "--dir", str(destination)],
        check=True,
    )
    path = destination / asset["name"]
    verify_digest(path, asset["digest"].removeprefix("sha256:"), asset["size"])
    return path


def restore_sdk(name, version_key, cmake_name, profile, destination, base):
    version = SELECTION[f"{version_key}_VERSION"]
    repo = f"qigao/{name}"
    release = capture("gh", "api", f"repos/{repo}/releases/tags/v{version}")
    assets = {item["name"]: item for item in release["assets"]}
    manifest_file = release_asset(repo, version, destination, assets[f"{name}-{version}-manifest.json"])
    manifest = json.loads(manifest_file.read_text(encoding="utf-8-sig"))
    if manifest["version"] != version or manifest["repository"].removeprefix("https://github.com/") != repo:
        raise ValueError(f"Upstream manifest identity mismatch: {repo}")
    [sdk] = (row for row in manifest["sdks"] if row.get("platform", row.get("profile")) == profile)
    filename = sdk.get("file", sdk.get("asset"))
    archive = release_asset(repo, version, destination, assets[filename])
    verify_digest(archive, sdk["sha256"], sdk["sizeBytes"])
    details = sdk.get("sdk_manifest", sdk)
    if base and details["base"]["sha256"] != base["sha256"]:
        raise ValueError(f"{repo} was built against a different Base SDK")
    if name == "cmeta" and sdk["checkout"] != SELECTION["CMETA_REF"]:
        raise ValueError("CMeta commit differs from .env.example")
    if name == "salts-utils" and details["cmeta_ref"] != SELECTION["CMETA_REF"]:
        raise ValueError("SaltsUtils was built against a different CMeta commit")

    root = destination / name
    root.mkdir()
    with tarfile.open(archive) as tar:
        tar.extractall(root, filter="data")
    config = root / "lib" / "cmake" / cmake_name / f"{cmake_name}Config.cmake"
    if not config.is_file():
        raise ValueError(f"Missing SDK package config: {config}")
    return root, {"version": version, "sha256": sdk["sha256"], "commit": manifest["commit"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--triplet", required=True)
    parser.add_argument("--host", required=True)
    args = parser.parse_args()
    destination = SOURCE / "build" / "upstream" / args.profile
    destination.mkdir(parents=True)
    environment = {key: SELECTION[key] for key in
                   ("VCPKG_CACHE_VERSION", "SALTS_BASE_VERSION", "SALTS_CNET_VERSION",
                    "SALTS_CNET_REF", "CMETA_VERSION", "SALTS_UTILS_VERSION")}
    os.environ.update(environment)

    versions = {}
    for name, (version_key, cmake_name) in PACKAGES.items():
        root, versions[name] = restore_sdk(name, version_key, cmake_name, args.profile,
                                           destination, versions.get("salts-base"))
        environment[f"{version_key}_ROOT"] = root.as_posix()

    selection = destination / "vcpkg-release.json"
    selection.write_text(json.dumps({
        "schema": 1,
        "source": {"kind": "github-release", "repository": "qigao/vcpkg-cache",
                   "version_env": "VCPKG_CACHE_VERSION", "asset": f"installed-{args.triplet}.tar.xz"},
    }), encoding="utf-8")
    cache_lock = destination / "vcpkg.lock.json"
    subprocess.run([*RESTORE, "resolve-release", str(selection), "--output-lock", str(cache_lock)], check=True)
    cache = capture(*RESTORE, "locked", str(cache_lock),
                    "--destination", str(destination / "vcpkg"), "--payload", "vcpkg_installed")
    environment["VCPKG_INSTALLED_DIR"] = cache["root"]
    environment["VCPKG_CACHE_REPOSITORY_ROOT"] = INFRA.as_posix()

    lock = destination / "re2c.lock.json"
    lock.write_text(json.dumps(RE2C), encoding="utf-8")
    tool_suffix = ".exe" if args.host.startswith("windows-") else ""
    re2c = capture(*RESTORE, "locked", str(lock), "--destination", str(destination / "re2c"),
                   "--payload", f"tools/{args.host}", "--executable", f"bin/re2c{tool_suffix}")
    environment["RE2C_ROOT"] = re2c["root"]
    lemon = capture(*RESTORE, "locked", str(SOURCE / "cmake" / "lemon.lock.json"),
                    "--destination", str(destination / "lemon"), "--payload", f"tools/{args.host}",
                    "--require", "share/lemon/lempar.c", "--require", "share/lemon/source.json",
                    "--executable", f"bin/lemon{tool_suffix}")
    environment["LEMON_ROOT"] = lemon["root"]

    provenance = destination / "inputs.json"
    provenance.write_text(json.dumps({
        "sdks": versions,
        "vcpkg_cache": {"version": environment["VCPKG_CACHE_VERSION"], "sha256": cache["sha256"]},
        "re2c": {"version": RE2C["source"]["version"], "sha256": re2c["sha256"]},
        "lemon": {"version": lemon["source"]["version"], "sha256": lemon["sha256"]},
    }, indent=2), encoding="utf-8")
    environment["SALTSNET_INPUTS"] = provenance.as_posix()
    with Path(os.environ["GITHUB_ENV"]).open("a", encoding="utf-8") as output:
        for key, value in environment.items():
            print(f"{key}={value}", file=output)


if __name__ == "__main__":
    main()
