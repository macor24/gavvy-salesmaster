#!/usr/bin/env python3
"""gavvy-salesmaster setup.py — Cython build configuration

Pro-tier modules (team_pkg) are compiled to .so for IP protection.
Community-tier modules (core, crm_pkg, trade_pkg, channels_pkg) remain as .py source.

Build modes:
    python setup.py build_ext --inplace    # Dev: keep .py, compile .so alongside (no protection)
    python setup.py sdist                  # sdist: include all .py (user can see source)
    python setup.py bdist_wheel            # Wheel: compile .py → .so, EXCLUDE .py source
    
    python -m build                        # Both sdist + wheel
"""

import os
import sys
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py

SRC_DIR = "src"

# ── Pro-tier modules to compile to .so ────────────────────
# These are the "closed-source" modules protected by Cython compilation.
# Community modules (not listed here) stay as .py source.

PRO_EXTENSIONS = [
    # team_pkg — AI Agent framework, LLM engine, memory
    "gavvy_salesmaster/team_pkg/__init__",
    "gavvy_salesmaster/team_pkg/llm/__init__",
    "gavvy_salesmaster/team_pkg/llm/deepseek",
    "gavvy_salesmaster/team_pkg/llm/fallback",
    "gavvy_salesmaster/team_pkg/memory/__init__",
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
]

# Try to use Cython; fall back to standard setuptools
try:
    from Cython.Build import cythonize
    from Cython.Distutils import build_ext as cython_build_ext
    HAS_CYTHON = True
except ImportError:
    HAS_CYTHON = False
    cythonize = None
    cython_build_ext = build_ext


def get_ext_modules():
    """Build Extension list — either .so (wheel) or .c (sdist)."""
    if not HAS_CYTHON:
        print("[gavvy-build] Cython not installed — skipping .so compilation", file=sys.stderr)
        return []

    from Cython.Build import cythonize
    
    ext_modules = []
    for mod_path in PRO_EXTENSIONS:
        # Convert module path to file path relative to SRC_DIR
        py_file = os.path.join(SRC_DIR, mod_path.replace("/", os.sep) + ".py")
        if not os.path.isfile(py_file):
            print(f"[gavvy-build] WARNING: {py_file} not found, skipping", file=sys.stderr)
            continue
        
        from setuptools import Extension
        ext = Extension(
            mod_path.replace("/", "."),
            [py_file],
        )
        ext_modules.append(ext)
    
    compiler_directives = {
        "language_level": "3",
        "boundscheck": False,
        "wraparound": False,
        "cdivision": True,
        "embedsignature": True,
    }
    
    return cythonize(
        ext_modules,
        compiler_directives=compiler_directives,
        language_level="3",
        build_dir=os.path.join("build", "cython"),
    )


class CythonBuildExt(build_ext):
    """Build extensions, optionally with Cython."""

    def run(self):
        if HAS_CYTHON:
            print(f"[gavvy-build] Cython compilation enabled for {len(PRO_EXTENSIONS)} Pro-tier modules")
            self.distribution.ext_modules = get_ext_modules()
        else:
            print("[gavvy-build] Cython not available — Pro modules remain as .py source")
        super().run()


class PyPIBuildPy(build_py):
    """Custom build_py: EXCLUDE .py source for compiled modules from wheel.
    
    When a module is compiled to .so, we must NOT include its .py source
    in the wheel. This class removes the .py files that have corresponding .so.
    """
    
    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        
        if not HAS_CYTHON:
            return modules  # No .so compiled — keep all .py
        
        # Get list of compiled .py files (they become .so)
        pro_py_files = set()
        for mod_path in PRO_EXTENSIONS:
            py_file = os.path.join(SRC_DIR, mod_path.replace("/", os.sep) + ".py")
            pro_py_files.add(os.path.normpath(py_file))
        
        # Filter out .py files that were compiled to .so
        filtered = []
        for (package_pkg, module_name, module_path) in modules:
            normalized = os.path.normpath(module_path)
            if normalized in pro_py_files:
                # This .py was compiled to .so — exclude it
                print(f"[gavvy-build] EXCLUDING .py from wheel: {normalized}")
                continue
            filtered.append((package_pkg, module_name, module_path))
        
        return filtered


# ── Read README ──────────────────────────────────────────

this_dir = os.path.dirname(os.path.abspath(__file__))
readme_path = os.path.join(this_dir, "README.md")
long_description = ""
if os.path.isfile(readme_path):
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()


packages = find_packages(where=SRC_DIR, include=["gavvy_salesmaster*"])

package_data = {
    "gavvy_salesmaster": [
        "core/web/*.html",
        "core/web/*.js",
        "core/web/*.css",
        "core/web/_customers.json",
        "core/web/_messages/*.json",
    ],
}


setup(
    cmdclass={
        "build_ext": CythonBuildExt,
        "build_py": PyPIBuildPy,
    },
    ext_modules=[],  # Filled by CythonBuildExt.run()
    packages=packages,
    package_dir={"": SRC_DIR},
    package_data=package_data,
    zip_safe=False,
)
