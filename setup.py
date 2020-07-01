"pykokkos setup module."

def main():

    import sys

    from setuptools import setup, find_packages

    console_scripts = ["pykokkos=pykokkos.__main__:main"]

    setup(
        name="pykokkos",
        version="0.1.0",
        description="Pythonic Kokkos",
        author="Youngsung Kim",
        author_email="youngsung.kim.act2@gmail.com",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Build Tools",
            "License :: OSI Approved :: Apache Software License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
        ],
        keywords="kokkos",
        packages=find_packages(exclude=["tests"]),
        include_package_data=True,
        install_requires=["microapp"],
        entry_points={ "console_scripts": console_scripts,
            "microapp.projects": "pykokkos = pykokkos"},
        test_suite="tests.pykokkos_unittest_suite",
        project_urls={
            "Bug Reports": "https://github.com/grnydawn/pykokkos/issues",
            "Source": "https://github.com/grnydawn/pykokkos",
        }
    )

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
