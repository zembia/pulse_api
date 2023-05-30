from setuptools import setup

setup(
    name="your_module",
    version="0.0.1",
    description="API para plataforma Pulse de Zembia",
    author="Zembia SpA"
    packages=["pulse_api"],
    install_requires=["PyInquirer>=1.0.3","requests>=2.25.1"],
    python_requires='>=3.7.9',
    zip_safe=False,
)


  