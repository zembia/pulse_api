from setuptools import setup

setup(
    name="pulse_api",
    version="0.1.1",
    description="API para plataforma Pulse de Zembia",
    author="Zembia SpA",
    packages=["pulse_api"],
    install_requires=["InquirerPy>=0.3.4", "requests>=2.25.1"],
    python_requires=">=3.7.5",
    zip_safe=False,
)
