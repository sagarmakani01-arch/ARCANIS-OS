from setuptools import setup, find_packages

setup(
    name="arcanis-brain",
    version="0.1.0",
    packages=find_packages(include=["arcanis_brain", "arcanis_brain.*"]),
    python_requires=">=3.11",
)
