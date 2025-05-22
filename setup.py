from setuptools import find_packages, setup

setup(
    name="nolead",
    version="0.2.0",
    description="A lightweight pipeline orchestration library inspired by Luigi",
    author="Rui Vieira",
    author_email="ruidevieira@googlemail.com",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
