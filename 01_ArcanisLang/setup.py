from setuptools import setup, find_packages

setup(
    name="arcanislang",
    version="0.1.0",
    description="A beginner-friendly, AI-native programming language",
    author="Arcanis Labs",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "arcanis=src.cli:main",
        ],
    },
)
