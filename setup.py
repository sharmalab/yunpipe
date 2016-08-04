from setuptools import setup, find_packages


setup(name='cloud_pipe',
      version='0.0.3.dev',
      description='An Automatic tool for setting up your image processing work flow on the cloud',
      url='https://github.com/wangyx2005/cloud_pipe.git',
      author='Yuxing Wang',
      author_email='wangyx2005@gmail.com',
      packages=find_packages(),
      install_requires=['boto3', 'Haikunator'],
      # scripts=['bin/wrap', 'bin/setup_pipe'],
      entry_points={
          'console_scripts': [
              'wrap = cloud_pipe.scripts.wrap:main',
              'clean-up = cloud_pipe.pipeline.cleanup:main',
              'setup-pipe = cloud_pipe.scripts.setup_pipe:main',
              'create-lambda-exec-role = cloud_pipe.scripts.setup_pipe: create_lambda_exec_role']
      },
      include_package_data=True,
      zip_safe=False)
