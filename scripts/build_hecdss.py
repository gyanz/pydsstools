"""Build hec-dss C library from the submodule and update static libs used by pydsstools.

Usage:
    python scripts/build_hecdss.py                         # build only
    python scripts/build_hecdss.py --setup-env             # initialise Intel oneAPI env, then build
    python scripts/build_hecdss.py --update                # pull latest submodule commit, then build
    python scripts/build_hecdss.py --update-only           # pull latest submodule commit, skip build
    python scripts/build_hecdss.py --sync-headers          # build + sync headers from upstream

--setup-env (Windows only):
    Calls heclib's vs_env.bat which runs Intel oneAPI setvars.bat to initialise
    the IFX Fortran compiler and Visual Studio 2022 toolchain in the environment
    used by this script's subprocess calls.  Required if nmake/IFX are not already
    on PATH (i.e. you have not run vs_env.bat or a Developer Command Prompt first).
    vs_env.bat default: C:\Program Files (x86)\Intel\oneAPI\setvars.bat intel64 vs2022
    Override the install root via the ONEAPI_ROOT environment variable.

Branch notes (pydsstools/src/external/hec-dss):
    master  (7-IW, 7-IX, ...)  DSS-6 and DSS-7.  Fortran source in heclib/heclib_f/.
    main    (7-JA, 7-JB, ...)  DSS-7 only.  Fortran and DSS-6 headers removed.

    The submodule currently tracks master.  Switch with:
        git submodule set-branch --branch <name> pydsstools/src/external/hec-dss

CMake build (this script):
    Builds heclib_c only (pure C).  The Fortran component (heclib_f.lib / heclib.a)
    must be built separately:
        Windows: Intel Fortran + heclib/heclib_f/heclib_f.vfproj
        Linux:   gfortran  +  make -C heclib/heclib_f

Outputs (Windows):
    pydsstools/src/external/dss/win64/heclib_c.lib   <- C component (this script)
    pydsstools/src/external/dss/win64/heclib_f.lib   <- Fortran (build separately, see below)
    pydsstools/src/external/dss/win64/heclib.lib     <- combined C+Fortran (this script,
                                                         requires heclib_f.lib to exist first)

    heclib_f.lib must be built with Intel Fortran:
        open heclib/heclib_f/heclib_f.vfproj in Visual Studio and build Release x64,
        then copy the output to pydsstools/src/external/dss/win64/heclib_f.lib.
    Once heclib_f.lib is in place, re-run this script to produce the combined heclib.lib.

Outputs (Linux):
    This script does NOT write to linux64/heclib.a on Linux.
    The CMake build is C-only; copying it would silently break the combined lib.
    Use the upstream Makefile instead:
        make -C pydsstools/src/external/hec-dss/heclib
        cp  pydsstools/src/external/hec-dss/heclib/Output/heclib.a \
            pydsstools/src/external/dss/linux64/heclib.a

After updating libs:
    git add -f pydsstools/src/external/dss/win64/heclib_c.lib  (Windows)
    git add -f pydsstools/src/external/dss/win64/heclib_f.lib  (Windows)
    git add -f pydsstools/src/external/dss/win64/heclib.lib    (Windows)
    git add -f pydsstools/src/external/dss/linux64/heclib.a    (Linux)

Header sync (--sync-headers):
    - upstream ∩ local   ->  updated from upstream
    - upstream only      ->  added
    - local only         ->  preserved unchanged (never deleted)

    On master the upstream contains all headers pydsstools needs.
    On main (DSS-7 only) the upstream drops hecdssFort.h, heclib6.h, and
    zdssMessagesFort.h; the preserve rule keeps them intact so pydsstools
    continues to compile against DSS-6 functions.

    checlib.pxd is always scanned after the sync and the script aborts if
    any header it references is missing — useful safety net when switching
    between branches.
"""

import argparse
import glob
import os
import platform
import re
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
SUBMODULE_DIR = os.path.join(ROOT_DIR, "pydsstools", "src", "external", "hec-dss")
BUILD_DIR = os.path.join(SUBMODULE_DIR, "build")
DSS_DIR = os.path.join(ROOT_DIR, "pydsstools", "src", "external", "dss")
HEADERS_SRC = os.path.join(SUBMODULE_DIR, "heclib", "heclib_c", "src", "headers")
HEADERS_DST = os.path.join(DSS_DIR, "headers")
CHECLIB_PXD = os.path.join(ROOT_DIR, "pydsstools", "src", "checlib.pxd")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Populated by capture_intel_env(); None means inherit the current process env.
_BUILD_ENV: "dict | None" = None


def run(cmd, cwd=None):
    print(f">> {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd, env=_BUILD_ENV)
    if result.returncode != 0:
        sys.exit(f"Command failed with exit code {result.returncode}")


def capture_intel_env():
    """Run vs_env.bat and capture the resulting environment into _BUILD_ENV.

    vs_env.bat calls Intel oneAPI setvars.bat which sets up IFX (Intel Fortran),
    nmake, lib.exe, and the Visual Studio 2022 toolchain.  Because a batch file's
    environment changes don't propagate back to Python, we run:
        cmd /c "call vs_env.bat && set"
    and parse the output to capture all resulting variables.
    """
    global _BUILD_ENV
    vs_env_bat = os.path.join(SUBMODULE_DIR, "vs_env.bat")
    if not os.path.isfile(vs_env_bat):
        sys.exit(f"ERROR: vs_env.bat not found at {vs_env_bat}")

    print(f"Sourcing Intel oneAPI environment from {vs_env_bat} ...")
    result = subprocess.run(
        ["cmd", "/c", f'call "{vs_env_bat}" && set'],
        capture_output=True, text=True, cwd=SUBMODULE_DIR,
    )
    if result.returncode != 0:
        sys.exit(
            f"ERROR: vs_env.bat failed (exit {result.returncode}):\n{result.stderr}"
        )

    env = {}
    for line in result.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            env[key] = value
    _BUILD_ENV = env
    print(f"Intel oneAPI environment captured ({len(env)} variables).\n")


def _find_lib(pattern):
    matches = glob.glob(pattern, recursive=True)
    return matches[0] if matches else None


def get_submodule_branch():
    """Return the configured tracking branch from .gitmodules, or None."""
    result = subprocess.run(
        ["git", "config", "--file", ".gitmodules",
         "submodule.pydsstools/src/external/hec-dss.branch"],
        cwd=ROOT_DIR, capture_output=True, text=True,
    )
    return result.stdout.strip() or None


def _branch_label(branch):
    """Human-readable DSS support label for a branch name."""
    if branch == "master":
        return f"{branch}  (DSS-6 and DSS-7)"
    if branch == "main":
        return f"{branch}  (DSS-7 only)"
    return branch or "unknown"


def parse_pxd_headers(pxd_path):
    """Return the set of .h filenames referenced by 'cdef extern from' in a .pxd file."""
    if not os.path.isfile(pxd_path):
        print(f"WARNING: checlib.pxd not found at {pxd_path}; skipping pxd scan.")
        return set()
    with open(pxd_path, encoding="utf-8") as f:
        content = f.read()
    return {
        os.path.basename(m.group(1))
        for m in re.finditer(r'cdef\s+extern\s+from\s+"([^"]+\.h)"', content)
    }


# ---------------------------------------------------------------------------
# Submodule update
# ---------------------------------------------------------------------------

def update_submodule():
    branch = get_submodule_branch()
    print(f"Updating hec-dss submodule (tracking: {_branch_label(branch)}) ...")
    run(
        ["git", "submodule", "update", "--remote", "--checkout",
         "pydsstools/src/external/hec-dss"],
        cwd=ROOT_DIR,
    )
    print("Submodule updated.\n")


# ---------------------------------------------------------------------------
# Build + copy libs
# ---------------------------------------------------------------------------

def build():
    """Build heclib (C + Fortran) and copy results into pydsstools/src/external/dss/.

    Windows: CMake builds heclib_c.lib; nmake builds heclib_f.lib; lib.exe combines them.
    Linux:   heclib/Makefile builds both C and Fortran and combines into heclib.a.
    """
    branch = get_submodule_branch()
    print(f"Building heclib (submodule branch: {_branch_label(branch)}) ...")

    if platform.system() == "Windows":
        _build_windows()
    else:
        _build_linux()


def _build_windows():
    dst_dir = os.path.join(DSS_DIR, "win64")
    os.makedirs(dst_dir, exist_ok=True)
    heclib_f_dir = os.path.join(SUBMODULE_DIR, "heclib", "heclib_f")

    # --- Step 1: C library via CMake ---
    print("\n-- Step 1: build heclib_c (CMake) --")
    os.makedirs(BUILD_DIR, exist_ok=True)
    run(["cmake", "-S", SUBMODULE_DIR, "-B", BUILD_DIR,
         "-DCMAKE_BUILD_TYPE=Release", "-A", "x64"])
    run(["cmake", "--build", BUILD_DIR, "--config", "Release", "--target", "heclib"])

    src_c = _find_lib(os.path.join(BUILD_DIR, "**", "heclib_c", "Release", "heclib.lib"))
    if src_c is None:
        src_c = _find_lib(os.path.join(BUILD_DIR, "**", "heclib.lib"))
    if src_c is None:
        sys.exit("ERROR: Could not find heclib.lib (C) in CMake build output.")

    dst_c = os.path.join(dst_dir, "heclib_c.lib")
    shutil.copy2(src_c, dst_c)
    print(f"Copied  {src_c}  ->  {dst_c}")

    # --- Step 2: Fortran library via nmake + Intel Fortran ---
    print("\n-- Step 2: build heclib_f (nmake / Intel Fortran IFX) --")
    run(["nmake", "/f", "Makefile.win", "clean"], cwd=heclib_f_dir)
    run(["nmake", "/f", "Makefile.win"], cwd=heclib_f_dir)

    src_f = _find_lib(os.path.join(heclib_f_dir, "x64", "Release", "heclib_f.lib"))
    if src_f is None:
        src_f = _find_lib(os.path.join(heclib_f_dir, "**", "heclib_f.lib"))
    if src_f is None:
        sys.exit("ERROR: Could not find heclib_f.lib in nmake build output.")

    dst_f = os.path.join(dst_dir, "heclib_f.lib")
    shutil.copy2(src_f, dst_f)
    print(f"Copied  {src_f}  ->  {dst_f}")

    # --- Step 3: combine into heclib.lib (used by setup.py) ---
    print("\n-- Step 3: combine into heclib.lib (lib.exe) --")
    dst_combined = os.path.join(dst_dir, "heclib.lib")
    run(["lib.exe", f"/OUT:{dst_combined}", dst_c, dst_f])
    print(f"Combined  ->  {dst_combined}")


def _build_linux():
    """Use the upstream heclib/Makefile which builds C + Fortran and combines them."""
    heclib_dir = os.path.join(SUBMODULE_DIR, "heclib")
    dst_dir = os.path.join(DSS_DIR, "linux64")
    os.makedirs(dst_dir, exist_ok=True)

    print("\n-- Building heclib (C + Fortran) via heclib/Makefile --")
    run(["make", "-C", heclib_dir, "clean"])
    run(["make", "-C", heclib_dir])

    src = os.path.join(heclib_dir, "Output", "heclib.a")
    if not os.path.isfile(src):
        sys.exit(f"ERROR: Combined heclib.a not found at {src}")

    dst = os.path.join(dst_dir, "heclib.a")
    shutil.copy2(src, dst)
    print(f"Copied  {src}  ->  {dst}")


# ---------------------------------------------------------------------------
# Header sync
# ---------------------------------------------------------------------------

def sync_headers():
    """Sync headers from the upstream submodule, preserving pydsstools-local headers.

    Strategy (never deletes):
      - upstream ∩ local   ->  update from upstream
      - upstream only      ->  add to pydsstools headers dir
      - local only         ->  preserve unchanged

    After the sync, verifies every header required by checlib.pxd is present.
    Aborts if any required header is missing — this catches branch switches
    (e.g. master -> main) that would remove DSS-6 headers still needed by pydsstools.
    """
    if not os.path.isdir(HEADERS_SRC):
        sys.exit(f"ERROR: Upstream headers not found at:\n  {HEADERS_SRC}")

    branch = get_submodule_branch()
    print(f"Syncing headers from upstream (branch: {_branch_label(branch)}) ...")

    upstream_headers = {f for f in os.listdir(HEADERS_SRC) if f.endswith(".h")}
    local_headers = {f for f in os.listdir(HEADERS_DST) if f.endswith(".h")}

    required_by_pxd = parse_pxd_headers(CHECLIB_PXD)
    print(f"checlib.pxd requires: {', '.join(sorted(required_by_pxd)) or '(none found)'}\n")

    local_only = local_headers - upstream_headers
    if local_only:
        print("Preserved (pydsstools-local, not in upstream):")
        for h in sorted(local_only):
            tag = " [required by checlib.pxd]" if h in required_by_pxd else ""
            print(f"  KEEP    {h}{tag}")
        print()

    updated, added = [], []
    for fname in sorted(upstream_headers):
        src = os.path.join(HEADERS_SRC, fname)
        dst = os.path.join(HEADERS_DST, fname)
        shutil.copy2(src, dst)
        if fname in local_headers:
            updated.append(fname)
        else:
            added.append(fname)

    if updated:
        print(f"Updated {len(updated)} headers from upstream:")
        for h in updated:
            print(f"  UPDATE  {h}")
        print()
    if added:
        print(f"Added {len(added)} new headers from upstream:")
        for h in added:
            print(f"  ADD     {h}")
        print()

    # Safety check: every header required by checlib.pxd must exist after sync
    final_headers = {f for f in os.listdir(HEADERS_DST) if f.endswith(".h")}
    missing = required_by_pxd - final_headers
    if missing:
        sys.exit(
            "ERROR: Header sync would break checlib.pxd — missing required headers:\n"
            + "".join(f"  {h}\n" for h in sorted(missing))
        )

    print(
        f"Safety check passed: all {len(required_by_pxd)} headers required by "
        f"checlib.pxd are present."
    )
    print(
        f"\nSummary: {len(updated)} updated, {len(added)} added, "
        f"{len(local_only)} preserved (pydsstools-local)."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--setup-env", action="store_true",
        help="(Windows) source vs_env.bat (Intel oneAPI + VS 2022) before building",
    )
    parser.add_argument(
        "--update", action="store_true",
        help="Pull latest submodule commit before building",
    )
    parser.add_argument(
        "--update-only", action="store_true",
        help="Pull latest submodule commit and exit without building",
    )
    parser.add_argument(
        "--sync-headers", action="store_true",
        help="After building, sync headers from upstream (never deletes local-only headers)",
    )
    args = parser.parse_args()

    if args.setup_env:
        if platform.system() != "Windows":
            print("WARNING: --setup-env is Windows-only; ignoring.")
        else:
            capture_intel_env()

    if args.update or args.update_only:
        update_submodule()
        if args.update_only:
            return

    build()

    if args.sync_headers:
        print("\n--- Header sync ---")
        sync_headers()

    print(
        "\nDone.  Updated libs are in pydsstools/src/external/dss/\n"
        "Remember to 'git add -f' the .lib/.a files and commit."
    )


if __name__ == "__main__":
    main()
