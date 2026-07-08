"""
Setup configuration for the ClimbHill.ai package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="climbhill-ai",
    version="0.1.0",
    author="ClimbHill.ai Contributors",
    author_email="",
    description="Local-first tooling for controlled recursive repository improvement with coding agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://climbhill.ai",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "research"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
        "pydantic>=2.0.0",
        "beautifulsoup4>=4.12.0",
        "markdown>=3.5.0",
        "python-dateutil>=2.8.0",
        "typing-extensions>=4.8.0",
        "PyYAML>=6.0",
        "mcp[cli]>=1.27,<2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "isort>=5.12.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "sphinx-autodoc-typehints>=1.24.0",
        ],
        "mcp": [
            "mcp>=1.0.0",
        ],
        "all": [
            "openai>=1.0.0",
            "google-generativeai>=0.3.0",
            "anthropic>=0.7.0",
            "mcp>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "adr=awesome_deep_research.cli:main",
            "climbhill=awesome_deep_research.cli:main",
            "adr-mcp=awesome_deep_research.mcp_server:main",
            "adr-mcp-smoke=awesome_deep_research.mcp_server:smoke_main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "ai",
        "self-improvement",
        "coding-agents",
        "mcp",
        "codex",
        "repository",
        "agents",
        "llm",
        "evaluation",
        "policy",
        "sqlite",
        "automation",
    ],
    project_urls={
        "Bug Reports": "https://github.com/closedloop-technologies/awesome-deep-researchers/issues",
        "Source": "https://github.com/closedloop-technologies/awesome-deep-researchers",
        "Documentation": "https://climbhill.ai",
    },
)
