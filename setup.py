

from distutils.core import setup

setup(name='slowboy',
      version='0.0.1',
      packages=['slowboy'],
      url='https://github.com/zmarvel/slowboy/',
      author='Zack Marvel',
      author_email='zpmarvel at gmail dot com',
      install_requires=[
          "PySDL2",
      ],
      extras_require={
          "dev": [
              "Pillow",
              "pytest",
          ],
      }
     )
