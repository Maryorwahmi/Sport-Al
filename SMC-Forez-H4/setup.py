from setuptools import setup, find_packages

setup(
    name="smc-forez",
    version="1.0.0",
    author="SMC Forez Team",
    description="Professional Forex Analyzer using Smart Money Concepts",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "MetaTrader5>=5.0.40",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "scipy>=1.9.0",
        "plotly>=5.10.0",
        "yfinance>=0.1.87",
        "ta-lib>=0.4.0",
        "dataclasses-json>=0.5.7",
        "python-dotenv>=0.19.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)