from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "mi_cps",
        ["mi_cps.pyx"],
        include_dirs=[
            "/usr/local/include",
        ],
        libraries=[
            "mi_cps",
        ],
        library_dirs=["/usr/local/lib"],
    )
]
cy_extensions = cythonize(extensions, compiler_directives={"language_level" : "3"})
setup(
    name="mi_cps",
    version='0.0.1',
    ext_modules=cy_extensions,
    extra_compile_args=["--std=c99"],
)
