from distutils.core import setup

install_requires=[
    'numpy>=1.18.5',
    'scipy>=1.7.0',
    'scikit-image>0.18.2',
    'h5py>=3.2.0',
    'matplotlib>=3.4.0',
    'multimethod>=1.4',
]

setup(name = 'TCFtools',
      version = '2021-08-10',
      description = 'Python TCFdata utilities',
      long_description = 'Python package for handling TCF data. It works with Tomcube data',
      author = 'Dohyeon Lee',
      author_email = 'dleh428@kaist.ac.kr',
      maintainer = 'Doheyon Lee',
      classifiers = [
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
      ],
      license = 'MIT',
      )