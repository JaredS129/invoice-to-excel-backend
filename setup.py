"""Setup configuration for invoice-to-excel-backend."""
from setuptools import setup, find_packages

setup(
    name="invoice-to-excel-backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'pdfplumber>=0.10.0',
        'openpyxl>=3.1.0',
        'Flask>=3.0.0',
        'Flask-CORS>=4.0.0',
        'waitress>=3.0.0',
        'python-magic>=0.4.27',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-flask>=1.3.0',
            'PyInstaller>=6.0.0',
        ]
    },
    python_requires='>=3.12',
)
