from setuptools import setup, find_packages

def read_requirements(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line and not line.startswith('#')]

def install_requirements():
    all_requirements = []
    all_requirements.extend(read_requirements('requirements.txt'))
    all_requirements.append("setuptools")
    return all_requirements

setup(
    name='http-request-smuggling',
    version='0.2',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            "smuggle.py=src.start:start_tools",
        ],
    },
    install_requires=install_requirements(),
    python_requires='>=3.6',
    author='manesec, silentsignal',
    author_email='mane@manesec.com',
    description='collection for pipx with redteam tools.',
    include_package_data=True,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/manesec/http-request-smuggling',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
