"""
Setup script for fastx402
"""

from setuptools import setup, find_packages

setup(
    name="fastx402",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "httpx>=0.25.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "eth-account>=0.9.0",
        "eth-utils>=2.0.0",
    ],
)

