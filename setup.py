from setuptools import setup, find_packages

setup(
    name="smc-forex-analyzer",
    version="1.0.0",
    description="A-grade Forex Analyzer with Smart Money Concepts and Structural Market Analysis",
    author="SMC-Forez Team",
    packages=find_packages(),
    install_requires=[
        "MetaTrader5>=5.0.45",
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "plotly>=5.17.0",
        "python-dotenv>=0.19.0",
        "dataclasses-json>=0.5.7",
        "typing-extensions>=4.0.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)