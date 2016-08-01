from setuptools import setup

setup(name='cloud_pipe',
      version='0.0.1',
      description='Automatic tool for setting up your image processing work flow on the cloud',
      url='https://github.com/wangyx2005/cloud_pipe.git',
      author='Yuxing Wang',
      author_email='wangyx2005@gmail.com',
      packages=['cloud_pipe'],
      install_requires=['boto3', 'Haikunator'],
      zip_safe=False)
