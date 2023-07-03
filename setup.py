from setuptools import setup

setup(
    name="pulse_api",
    version="0.0.5",
    description="API para plataforma Pulse de Zembia",
    author="Zembia SpA",
    packages=["pulse_api"],
    install_requires=["PyInquirer>=1.0.3", "requests>=2.25.1"],
    python_requires=">=3.7.5",
    zip_safe=False,
)
