from setuptools import setup, find_packages

setup(
    name="resonant-bridge",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.21.0",
        "asyncpg>=0.30.0",
        "pydantic>=2.7.0",
        "fastapi>=0.111.0",
        "openai>=1.0.0",
        "httpx>=0.25.0",
    ],
    python_requires=">=3.11",
)
