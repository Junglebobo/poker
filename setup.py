from distutils.core import setup
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import os

pokeher_cythons = ["cards.pyx", "handscore.pyx", "hand_simulator.pyx"]
sources = map(lambda filename: os.path.join('pokeher', filename), pokeher_cythons)

ext_modules = cythonize(sources)

setup(
  name = 'Pokeher core ops',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)
