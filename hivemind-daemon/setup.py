from setuptools import setup, find_packages


setup(
    name='hivemind-daemon',
    version='0.1.0',
    description='Last mile neural inference',
    packages=find_packages(),
    install_requires=[
        'aiofiles',
        'aiohttp',
        'Cerberus',
        'numpy',
        'onnx',
        'onnxruntime',
        'Pillow',
        'protobuf',
        'pyyaml',
        'requests',
        'stopit',
    ],
    entry_points={
        'console_scripts': [
            'hivemind-daemon = hivemind_daemon.app:main',
        ],
    },
)
