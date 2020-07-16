from setuptools import setup, find_packages


setup(
    name='citrine',
    version='0.3.0',
    python_requires='>3.7.0',
    description='Last mile neural inference',
    packages=find_packages(),
    install_requires=[
        'onnxruntime',
        'onnx',
        'aiofiles',
        'aiohttp',
        'Cerberus',
        'numpy',
        'Pillow',
        'protobuf',
        'pyyaml',
        'requests',
        'stopit',
    ],
    entry_points={
        'console_scripts': [
            'citrine-daemon = citrine_daemon.app:main',
        ],
    },
)
