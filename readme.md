cloud_pipe is an automatic setup tool for setting up the data analysis pipeline on the Amazon Web Services (AWS). It provides an easy to deploy, use and scale your data analysis algorithm and work flow on the cloud as well as sharing between colleges and institutions. It is developed in Python 3 using boto, the AWS SDK for Python.

Now cloud_pipe is on Pypi, and it supports pip. The latest version is v0.0.3. To install yunpipe, use pip.
```
pip install yunpipe
```. 

After install yunpipe:

To submit an algorithm or bring your analyze tool, use `wrap -ds`. For more options, check: `wrap --help`

To run single algorithm or deploy you analytical work flow, use `setup-pipe -f your-workflow-json`. For more options, check: `setup-pipe --help`

For documentation, see [yunpipe documentation](http://cloud-pipe.readthedocs.io/en/latest/)
