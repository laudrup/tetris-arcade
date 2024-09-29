from setuptools import setup


setup(
    name='tetris-arcade',
    version='1.0.0',
    description='Tetris implemented with Python Arcade',
    long_description='Tetris clone based on the tetris example from the python arcade distribution.',
    url='https://github.com/laudrup/tetris-arcade',
    author='Kasper Laudrup',
    author_email='laudrup@stacktrace.dk',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    packages=['tetris_arcade'],
    package_data={'tetris_arcade': ['data/*']},
    install_requires=[
        'arcade'
    ],
    entry_points={
        'gui_scripts': [
            'tetris_arcade = tetris_arcade:main',
        ]
    }
)
