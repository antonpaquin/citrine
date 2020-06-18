from setuptools import setup, find_packages


setup(
    name='hivemind-ui',
    version='0.2.0',
    description='Friendly user interface for hivemind-daemon',
    packages=find_packages(),
    install_requires=[
        'pyside2',
        'requests',
        'websockets',
    ],
    entry_points={
        'console_scripts': [
            'hivemind-ui = hivemind_ui.app:main',
        ],
    },
)
