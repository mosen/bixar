from setuptools import setup, find_packages

setup(
    name="moxar",
    version="0.1",
    description="Support for the XAR (Extensible Archive Format) Format",
    packages=['moxar'],
    author="mosen",
    license="MIT",
    url="https://github.com/mosen/moxar",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='XAR',
    install_requires=[
    ],
    python_requires='>=3.5',
    tests_require=[
        'pytest',
        'mock'
    ],
    setup_requires=['pytest-runner'],
    entry_points={
        'console_scripts': [
            'moxar=moxar.cli:main',
        ]
    },
    zip_safe=False
)


