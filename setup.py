from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="idea2product",
    version="0.1.0",
    author="Research Team",
    description="Multi-agent system for transforming requirements into production-ready web applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/idea2product",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "openai>=1.54.0",
        "pydantic>=2.10.0",
        "pydantic-settings>=2.7.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "astroid>=3.3.0",
        "aiofiles>=24.1.0",
        "requests>=2.32.0",
        "httpx>=0.28.0",
        "Pillow>=10.0.0",
        "selenium>=4.27.0",
        "pytest-bdd>=7.0.0",
    ],
    entry_points={
        "console_scripts": [
            "idea2product=src.cli:main",
        ],
    },
)
