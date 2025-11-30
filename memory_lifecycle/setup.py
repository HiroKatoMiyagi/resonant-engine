from setuptools import setup, find_packages

setup(
    name="resonant-memory-lifecycle",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "asyncpg>=0.30.0",
        "pydantic>=2.7.0",
    ],
    python_requires=">=3.11",
)
