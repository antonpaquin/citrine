from setuptools import setup, find_packages


setup(
    name='citrine-ui',
    version='0.3.0',
    description='Friendly user interface for citrine-daemon',
    packages=find_packages(),
    install_requires=[
        'pyside2',
        'requests',
        'websockets',
    ],
    entry_points={
        'console_scripts': [
            'citrine-ui = citrine_ui.app:main',
        ],
    },
)
