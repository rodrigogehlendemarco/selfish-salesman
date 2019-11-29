from setuptools import setup

setup(name='selfish_salesman',
      version='0.1',
      author='Rodrigo Gehlen De Marco',
      author_email='rodrigo.g.marco@gmail.com',
      description='Python API wrapper for the traveling salesman problem',
      packages=['selfish_salesman'],
      install_requires=['httpx'],
      zip_safe=False)
