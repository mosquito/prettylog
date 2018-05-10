from setuptools import setup


setup(
    name='prettylog',
    version='0.2.0',
    platforms="all",
    author="Dmitry Orlov",
    author_email="me@mosquito.su",
    maintainer="Dmitry Orlov",
    maintainer_email="me@mosquito.su",
    description="Let's write beautiful logs",
    long_description=open('README.rst').read(),
    package_dir={'': 'src'},
    packages=[''],
    license="Apache 2",
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
    ],
    install_requires=[
        'colorlog',
        'fast-json',
    ],
    extras_require={
        'develop': [
            'coverage!=4.3',
            'pylama',
            'pytest',
            'pytest-cov',
            'timeout-decorator',
            'tox>=2.4',
        ],
        ':python_version < "3.5"': 'typing >= 3.5.3',
    },
)
