from pathlib import Path

from setuptools import find_packages, setup

cwd = Path(__file__).parent
requirements_path = cwd / "requirements.txt"
readme_path = cwd / "README.md"

requirements = []
with open(requirements_path) as f:
    requirements = f.read().splitlines()

readme = ""
with open(readme_path) as f:
    readme = f.read()

setup(
    name="csihu",
    version="2.0.0",
    packages=find_packages(),
    url="https://github.com/Vitaman02/CS-IHU-NotifierBot",
    license="MIT",
    author="Vitaman02",
    description=readme,
    install_requires=requirements,
    python_requires=">=3.10",
)
