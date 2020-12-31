# Run pip outside of environment

At a glance:

```console
$ virtualenv --no-pip myenv  # Create environment without pip.

$ source myenv/bin/activate  # Activate environment.

$ pip --version      # pip is not available.
bash: pip: command not found

$ ouo install six    # But we can still do this.
Collecting six
  Using cached six-1.15.0-py2.py3-none-any.whl (10 kB)
Installing collected packages: six
Successfully installed six-1.15.0

$ python -c 'import six; print(six.__file__)'
.../myenv/lib/python3.9/site-packages/six.py
```

## How?

`ouo` downloads pip wheels into the user's data dirctory. When executed, it
executes pip with something like

```
/path/to/python /path/to/pip-20.3.3-py2.py3-none-any.whl/pip
```

where the path of the Python interpreter is detected with the `VIRTUAL_ENV`
environment variable. The interpreter would then perform a zip import to
execute the pip module inside the wheel.


## What's up with the name?

I often mistype `pip` on one of my keyboards. `ouo` is `pip` shifted one
position to the left on QWERTY.


## Future Works

* `setuptools` and `wheel` are still needed to build legacy (non-PEP-517)
  source distributions. This makes `python -m venv --no-pip` unrealistic.
* Invocation is slow. This has two causes: `ouo` needs to iterate through
  the wheel directory to find a suitable pip version for the current Python
  version. Also, zip imports are very slow.
