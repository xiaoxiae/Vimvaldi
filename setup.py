from setuptools import setup, find_packages
from os import path

script_location = path.abspath(path.dirname(__file__))

setup(
    # information about the package
    name="vimvaldi",
    version="0.1",
    author="Tomáš Sláma",
    author_email="tomas@slama.dev",
    keywords="notes notesheet editor curses",
    url="https://github.com/xiaoxiae/Vimvaldi",
    description="A terminal note sheet editor.",
    long_description=open(path.join(script_location, "README.md"), "r").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    # where to look for files
    packages=["vimvaldi"],
    data_files=[("", ["LICENSE.txt", "README.md"])],

    entry_points={'console_scripts': ['vimvaldi=vimvaldi.__init__:run']},

    # requirements
    python_requires='>=3.8',
)
