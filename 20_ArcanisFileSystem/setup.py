"""Setup script for ArcanisFileSystem."""

from setuptools import setup, find_packages

setup(
    name="arcanis-filesystem",
    version="1.0.0",
    author="Arcanis Lab",
    description="Modern filesystem for ArcanisOS with AI-powered features",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=6.0", "pytest-cov>=2.0"],
    },
    entry_points={
        "console_scripts": [
            "arcanis-fsck=tools.arcanis_fsck:main",
            "arcanis-mount=tools.arcanis_mount:main",
            "arcanis-backup=tools.arcanis_backup:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Filesystems",
    ],
)
