from setuptools import setup, find_packages


setup(name='yunpipe2',
      version='0.0.0',
      description='An Automatic tool for setting up your image processing work flow on the cloud',

      url='https://github.com/nujhedtozu/yunpipe',

      author='Yuxing Wang',
      author_email='wangyx2005@gmail.com',
    
      maintainer='Deh-Jun Tzou',
      maintainer_email='junior.tzou@gmail.com',

      packages=find_packages(),
      install_requires=['boto3', 'Haikunator'],

      license='Apache v2.0',
      # scripts=['bin/wrap', 'bin/setup_pipe'],
      entry_points={
          'console_scripts': [
              'wrap = yunpipe.scripts.wrap:main',
              'clean-up = yunpipe.pipeline.cleanup:main',
              'setup-pipe = yunpipe.scripts.setup_pipe:main',
              'create-lambda-exec-role = yunpipe.pipeline.set_pipe:create_lambda_exec_role']
      },
      include_package_data=True,
      zip_safe=False)
