from setuptools import setup, find_packages

setup(
    name='devpilot',
    version='0.1',
    packages=find_packages(),  # This will find devpilot/
    include_package_data=True,
    install_requires=[
        'rich',
    ],
    entry_points={
        'console_scripts': [
            'devpilot=devpilot.onboarder:main',  # 👈 CLI entry now points inside devpilot/
        ],
    },
    author='Sandeeb Adhikari',
    description='AI-powered CLI for onboarding, explaining, and refactoring legacy codebases.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.7',
)

