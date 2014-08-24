from setuptools import setup

setup(
    name='wot_clan_history',
    license='MIT',
    version='0.1',
    url='https://github.com/ceari/wot_clan_history',
    author='Daniel Diepold',
    author_email='daniel.diepold@gmail.com',
    py_modules=['clan_history'],
    install_requires=[
        'flask-restful>=0.2.12',
        'pymongo',
        'Celery-with-redis',
        'requests'
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ]
)