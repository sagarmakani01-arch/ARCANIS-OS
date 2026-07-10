from setuptools import setup

setup(
    name="arcanis-os",
    version="9.0.0",
    description="Arcanis OS — AI-Native Operating System Simulation",
    long_description="Arcanis OS is the most comprehensive unified OS architecture ever conceived. "
                     "86 modules spanning kernels, AI, quantum, blockchain, and distributed consciousness. "
                     "Real filesystem, real SHA256 blockchain, real quantum circuits, real neural network.",
    author="Sagar Makani",
    url="https://github.com/sagarmakani01-arch/ARCANIS-OS",
    py_modules=["demo"],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "arcanis=demo:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Operating System",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
