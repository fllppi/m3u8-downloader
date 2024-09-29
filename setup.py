from setuptools import setup, find_packages

setup(
    name='m3u8-downloader',
    version='0.1.0',
    author='Flippi',
    author_email='74378751+fllppi@users.noreply.github.com',  # Your email
    description='A tool to download videos from m3u8 streams',
    long_description=open('README.md').read(), 
    long_description_content_type='text/markdown',
    url='https://github.com/fllppi/m3u8-downloader',
    packages=find_packages(),
    install_requires=[
        'requests',
        'tqdm',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'm3u8-downloader=m3u8_downloader.cli:main',
        ],
    },
)
