import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="townshell", # Replace with your own username
    version="0.1.0",
    author="mokojm",
    author_email="mokoj.triforce@gmail.com",
    description="A shell script for enhancing Townscaper experience",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mokojm/townshell",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta"
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires='>=3.8',
)
