from setuptools import setup, find_packages

requirements = [
    'tornado>=6.0',
]

with open('README.md') as rm:
    long_description = rm.read()

setup(
    name='clb-voting-demo',
    version='0.1.0',
    description='The Collaboratory Voting Demo',
    long_description=long_description,
    author='Human Brain Project Collaboratory Team',
    author_email='support@humanbrainproject.eu',
    url='https://wiki.humanbrainproject.eu/',
    packages=find_packages(),
    install_requires=requirements
)
