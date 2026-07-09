from setuptools import setup, find_packages

setup(
    name="arcanisdb",
    version="0.1.0",
    description="A fast, lightweight database for AI memory and applications",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Arcanis Lab",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
    ],
    extras_require={
        "encryption": ["cryptography>=3.4.0"],
        "rest": ["flask>=2.0.0"],
        "full": ["cryptography>=3.4.0", "flask>=2.0.0"],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
