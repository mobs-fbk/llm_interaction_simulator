from setuptools import find_packages, setup

setup(
    name="LLMSimulator",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyautogen",
        "ollama",
        "itakello-logging",
        "pymongo",
        "inquirer",
        "prompt_toolkit",
        "nltk",
        "inflect",
        "pytest",
        "pytest-mock",
    ],
    python_requires=">=3.9",
)
