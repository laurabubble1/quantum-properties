#!/usr/bin/env python
"""Setup script for quantum-properties package."""

from setuptools import setup, find_packages

setup(
    name="quantum-properties",
    version="0.1.0",
    description="Modern property-based testing framework for Qiskit quantum circuits",
    author="Laura Bubble",
    author_email="laura@example.com",
    license="Apache 2.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "qiskit>=2.0.0",
        "qiskit-aer>=0.17.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "ruff>=0.1.0",
        ],
    },
)
