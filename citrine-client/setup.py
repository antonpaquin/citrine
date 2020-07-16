from setuptools import setup, find_packages


setup(
    name='citrine-client',
    version='0.3.0',
    description='Utility for interacting with citrine-daemon',
    packages=find_packages(),
    install_requires=[
        'requests',
        'progress',
    ],
    entry_points={
        'console_scripts': [
            'citrine = citrine_client.__main__:main',
        ],
    },
)
