from setuptools import setup, find_packages


setup(
    name='hivemind-client',
    version='0.2.0',
    description='Utility for interacting with hivemind-daemon',
    packages=find_packages(),
    install_requires=[
        'requests',
        'progress',
    ],
    entry_points={
        'console_scripts': [
            'hivemind = hivemind_client.__main__:main',
        ],
    },
)
