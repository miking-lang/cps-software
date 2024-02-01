from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
#import numpy

extensions = [
    Extension(
        "mi_cps",
        ["mi_cps.pyx"],
        include_dirs=[
            #"/opt/quanser/hil_sdk/include",
            #numpy.get_include(),
        ],
        libraries=[
            "mi_cps",
            #"rt",
            #"pthread",
            #"dl",
            #"m",
            #"c",
        ],
        library_dirs=["/usr/local/lib"],
    )
]
cy_extensions = cythonize(extensions, compiler_directives={"language_level" : "3"})
setup(
    name="mi_cps",
    version='0.0.1',
    ext_modules=cy_extensions,
    #include_dirs=[numpy.get_include()],
)
