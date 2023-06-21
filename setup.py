from setuptools import find_packages, setup
from pywa import __version__

setup(
    name="pywa",
    packages=find_packages(),
    version=__version__,
    description="Python wrapper for the WhatsApp Cloud API",
    long_description=(open('README.md', encoding='utf-8').read()),
    long_description_content_type="text/markdown",
    author_email='davidlev@telegmail.com',
    install_requires=["requests"],
    extras_require={
        "flask": ["flask"],
        "fastapi": ["fastapi", "uvicorn"],
    },
    project_urls={
        "Documentation": "https://github.com/david-lev/pywa#readme",
        "Issue Tracker": "https://github.com/david-lev/pywa/issues",
        "Source Code": "https://github.com/david-lev/pywa",
        "Funding": "https://github.com/sponsors/david-lev"
    },
    download_url="https://pypi.org/project/pywa/",
    author='David Lev',
    license='MIT',
    keywords=', '.join((
        'whatsapp', 'whatsapp-api', 'whatsapp-cloud-api', 'whatsapp-cloud', 'whatsapp-api-python',
        'whatsapp-cloud-api-python', 'pywa', 'wapy', 'wa', 'wa-api', 'wa-cloud-api', 'wa-cloud', 'wa-api-python',
        'wa-cloud-api-python',
    )),
    classifiers=[
        'Framework :: Robot Framework :: Library',
        'Topic :: Communications :: Chat',
        'Topic :: Communications',
        'Topic :: Utilities',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
