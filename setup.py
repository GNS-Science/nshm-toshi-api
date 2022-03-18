from setuptools import setup, find_packages

setup(
    name='toshi-api',
    version='0.1.0',
    packages=find_packages(include=['graphql_api', 'graphql_api.*'])
)