from setuptools import setup, find_packages
import re

VERSIONFILE = 'ytmusicapi/_version.py'

version_line = open(VERSIONFILE).read()
version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
match = re.search(version_re, version_line, re.M)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Could not find version in '%s'" % VERSIONFILE)

setup(name='ytmusicapi',
      version=version,
      description='Unofficial API for downloading YouTube Music for listening offline. Forked from https://github.com/sigma67/ytmusicapi',
      long_description=(open('README.rst').read()),
      url='https://github.com/un1tz3r0/ytmusicapi',
      author='un1tz3r0',
      author_email='',
      license='MIT',
      packages=find_packages(),
      install_requires=['requests >= 2.22', 'pytube >= 10.0.0', 'mutagen >= 1.45.1'],
      extras_require={
          'dev': ['pre-commit', 'flake8', 'yapf', 'coverage', 'sphinx', 'sphinx-rtd-theme']
      },
      python_requires=">=3.5",
      include_package_data=True,
      zip_safe=False)
