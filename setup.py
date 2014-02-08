# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='rollbackcontext',
    version='0.1-2',
    description='A context manager to do rollbacks automatically',
    url='https://github.com/edwardbadboy/rollbackcontext',
    long_description=readme(),
    author='Zhou Zheng Sheng',
    author_email='zhshzhou@linux.vnet.ibm.com',
    license='LGPL2+',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or '
            'later (LGPLv2+)',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='rollback context manager',
    packages=['rollbackcontext'],
    zip_safe=True,
    include_package_data=True,
    tests_require=['nose'],
    test_suite='nose.collector',
    )
