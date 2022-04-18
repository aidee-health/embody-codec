from setuptools import setup

setup(
    name='embody-protocol-codec',
    version='1.0',
    package_dir={'': 'src'},
    packages=setup.find_packages(where='src'),
    url='',
    license='',
    author='espenwest',
    author_email='espenwest@gmail.com',
    description='Codec for the Embody project',
    python_requires='>=3.8'
)
