from setuptools import setup

setup(name='cloud_pipe',
      version='0.0.2',
      description='Automatic tool for setting up your image processing work flow on the cloud',
      url='https://github.com/wangyx2005/cloud_pipe.git',
      author='Yuxing Wang',
      author_email='wangyx2005@gmail.com',
      packages=['cloud_pipe', 'cloud_pipe.wrapper', 'cloud_pipe.pipeline'],
      install_requires=['boto3', 'Haikunator'],
      scripts=['bin/wrap', 'bin/setup_pipe'],
      entry_points = {
            'console_scripts': [
                  'clean=cloud_pipe.pipeline.cleanup.main'
            ]
      },
      include_package_data=True,
      zip_safe=False)
