from setuptools import setup

setup(
    name="iodized",
    version="0.0.1",
    packages=["grinder"],
    install_requires=["salt==2014.1.0", "docopts==0.6.1"],
    package_dir={'': 'src'},
    entry_points = {
    'console_scripts': [
    'grinder = grinder:main']
    }
)
