#!/usr/bin/env python3
"""gavvy-salesmaster — build script for PyPI release

Compiles Pro-tier modules (team_pkg) to .so binary, then builds wheel.
Usage: python build_release.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

SRC_DIR = "src"

PRO_MODULES = [
    "gavvy_salesmaster/team_pkg/__init__",
    "gavvy_salesmaster/team_pkg/llm/__init__",
    "gavvy_salesmaster/team_pkg/llm/deepseek",
    "gavvy_salesmaster/team_pkg/llm/fallback",
    "gavvy_salesmaster/team_pkg/memory/__init__",
    "gavvy_salesmaster/team_pkg/memory/flywheel",
    "gavvy_salesmaster/team_pkg/team/__init__",
    "gavvy_salesmaster/team_pkg/team/agents",
    "gavvy_salesmaster/team_pkg/team/api_config",
    "gavvy_salesmaster/team_pkg/team/base",
    "gavvy_salesmaster/team_pkg/team/coordinator",
    "gavvy_salesmaster/team_pkg/team/insight",
    "gavvy_salesmaster/team_pkg/team/prompts",
    "gavvy_salesmaster/team_pkg/team/quickstart",
    "gavvy_salesmaster/team_pkg/team/safety",
    "gavvy_salesmaster/team_pkg/team/scorer",
    "gavvy_salesmaster/team_pkg/team/session",
    "gavvy_salesmaster/crm_pkg/catalog",
    "gavvy_salesmaster/core/license",
    "gavvy_salesmaster/core/flow",
    "gavvy_salesmaster/core/routers/catalog",
    "gavvy_salesmaster/core/routers/flow",
    "gavvy_salesmaster/channels_pkg/channels/desktop",
    "gavvy_salesmaster/cli",
]


def _get_module_name(mod_path):
    """Convert 'gavvy_salesmaster/team_pkg/__init__' to 'gavvy_salesmaster.team_pkg.__init__'"""
    return mod_path.replace("/", ".")


def _get_py_file(mod_path):
    return os.path.join(SRC_DIR, mod_path + ".py")


def _get_so_name(mod_path):
    """Generate the .so filename that Python expects for this module."""
    mod_name = mod_path.split("/")[-1]  # e.g. '__init__'
    if mod_name == "__init__":
        # __init__ modules produce: package.cpython-312-x86_64-linux-gnu.so
        # But actually for init modules, the dir name becomes the .so
        parent = mod_path.rsplit("/", 1)[0]  # e.g. 'gavvy_salesmaster/team_pkg'
        pkg_name = parent.split("/")[-1]  # 'team_pkg'
        return f"{pkg_name}.cpython-312-x86_64-linux-gnu.so"
    else:
        return f"{mod_name}.cpython-312-x86_64-linux-gnu.so"


def _get_expected_so_dir(mod_path):
    """Get the source directory where the .so should be placed."""
    return os.path.join(SRC_DIR, os.path.dirname(mod_path))


def _get_target_so_path(mod_path):
    """Get the full path for the compiled .so in the source tree."""
    so_name = _get_so_name(mod_path)
    return os.path.join(_get_expected_so_dir(mod_path), so_name)


def _get_built_so_path(build_dir, mod_path):
    """The build_ext puts .so in build/lib/ structure."""
    mod_name = mod_path.split("/")[-1]
    parent_dir = os.path.dirname(mod_path)
    if mod_name == "__init__":
        pkg_name = parent_dir.split("/")[-1]
        so_name = f"{pkg_name}.cpython-312-x86_64-linux-gnu.so"
    else:
        so_name = f"{mod_name}.cpython-312-x86_64-linux-gnu.so"
    return os.path.join(build_dir, parent_dir, so_name)


def build():
    print("=" * 60)
    print("gavvy-salesmaster Release Build")
    print("=" * 60)
    
    # Step 0: Clean previous builds
    for d in ["build", "dist", "*.egg-info"]:
        shutil.rmtree(d, ignore_errors=True)
    
    # Step 1: Build extensions with Cython
    print("\n[1/4] Compiling Pro-tier modules to .so...")
    
    from Cython.Build import cythonize
    from setuptools import Extension
    from setuptools.command.build_ext import build_ext
    from distutils.dist import Distribution
    
    ext_modules = []
    for mod in PRO_MODULES:
        pyfile = _get_py_file(mod)
        if os.path.isfile(pyfile):
            ext = Extension(_get_module_name(mod), [pyfile])
            ext_modules.append(ext)
            print(f"  + {_get_module_name(mod)}")
    
    compiler_directives = {
        "language_level": "3",
        "boundscheck": False,
        "wraparound": False,
        "cdivision": True,
        "embedsignature": True,
    }
    
    cythonized = cythonize(
        ext_modules,
        compiler_directives=compiler_directives,
        language_level="3",
        build_dir="build/cythonize",
    )
    
    dist = Distribution({"ext_modules": cythonized})
    cmd = build_ext(dist)
    cmd.build_lib = "build/lib"
    cmd.inplace = False  # Don't try to copy to source
    cmd.ensure_finalized()
    cmd.run()
    
    # Step 2: Copy .so files to source tree
    print("\n[2/4] Copying .so files to source tree...")
    build_lib = "build/lib"
    for mod in PRO_MODULES:
        built_so = _get_built_so_path(build_lib, mod)
        target_dir = os.path.join(SRC_DIR, os.path.dirname(mod))
        os.makedirs(target_dir, exist_ok=True)
        
        if os.path.isfile(built_so):
            target = os.path.join(target_dir, os.path.basename(built_so))
            shutil.copy2(built_so, target)
            print(f"  COPY: {built_so} -> {target}")
        else:
            print(f"  WARNING: {built_so} not found")
    
    # Step 3: Skip sdist（只发 wheel，不暴露源码）
    print("\n[3/4] Skip sdist (只发 wheel，不暴露源码)")

    # Step 4: 替换 .py 为 .so（仅用于 wheel 构建）
    print("\n[4/4] Replacing .py with .so for wheel build...")
    backup_dir = "build/source-backup"
    for mod in PRO_MODULES:
        pyfile = _get_py_file(mod)
        if os.path.isfile(pyfile):
            if mod.endswith("/__init__"):
                print(f"  KEEP: {pyfile} (shim)")
            else:
                rel = os.path.relpath(pyfile, SRC_DIR)
                bk = os.path.join(backup_dir, rel)
                os.makedirs(os.path.dirname(bk), exist_ok=True)
                shutil.copy2(pyfile, bk)
                os.remove(pyfile)
                print(f"  REPLACE: {pyfile} -> .so")

    # Step 5: Build wheel (移除 .py 只留 .so)
    print("\n[5/4] Building wheel (二进制)...")
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation"],
        capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__))
    )
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr[-500:]}")
    else:
        print("\n✅ Build complete!")
        import glob
        for whl in sorted(glob.glob("dist/*.whl")):
            print(f"   {whl} ({os.path.getsize(whl) / 1024:.0f} KB)")

    
    # Step 5: Restore .py files (don't leave source tree dirty)
    print("\n[5/4] Restoring .py source files...")
    for mod in PRO_MODULES:
        pyfile = _get_py_file(mod)
        if not mod.endswith("/__init__"):  # non-init files were removed
            rel = os.path.relpath(pyfile, SRC_DIR)
            bk = os.path.join(backup_dir, rel)
            if os.path.isfile(bk):
                shutil.copy2(bk, pyfile)
                os.remove(bk)
    
    # Clean up backup dir
    if os.path.isdir(backup_dir):
        shutil.rmtree(backup_dir, ignore_errors=True)
    
    # Clean up .so from source tree (they're in the wheel now)
    print("\n[5/5] Cleaning up .so from source tree...")
    for mod in PRO_MODULES:
        target_dir = os.path.join(SRC_DIR, os.path.dirname(mod))
        for f in os.listdir(target_dir):
            if f.endswith(".so"):
                fp = os.path.join(target_dir, f)
                os.remove(fp)
                print(f"  REMOVE: {fp}")


if __name__ == "__main__":
    build()
