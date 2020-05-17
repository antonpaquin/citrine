from setuptools import setup, find_packages


setup(
    name='hivemind-client',
    version='0.0.1',
    description='Utility for interacting with hivemind-daemon',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'hivemind = hivemind_client.cli:main',
        ],
    },
)
