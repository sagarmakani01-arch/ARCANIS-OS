from setuptools import setup, find_packages

setup(
    name="arcanis-memory",
    version="0.1.0",
    packages=find_packages(include=["arcanis_memory", "arcanis_memory.*"]),
    python_requires=">=3.11",
    install_requires=[
        "arcanisdb>=0.1.0",
        "numpy>=1.20.0",
    ],
    extras_require={
        "crypto": ["cryptography>=3.4.0"],
        "dev": ["pytest>=7.0.0"],
    },
)