# PyUSTC

[![pypi](https://img.shields.io/pypi/v/pyustc.svg)](https://pypi.python.org/pypi/pyustc)
![code size](https://img.shields.io/github/languages/code-size/USTC-XeF2/pyustc)
![last commit](https://img.shields.io/github/last-commit/USTC-XeF2/pyustc)
[![commits since last release](https://img.shields.io/github/commits-since/USTC-XeF2/pyustc/latest.svg)](https://github.com/USTC-XeF2/pyustc/releases)

A Python package that allows for quick use of USTC network services.

## Installation

```bash
pip install pyustc
```

If you want to use the default validate code processer, you need to install `pytesseract` as well:

```bash
pip install pytesseract
```

And you also need to install `tesseract` on your system from [here](https://github.com/tesseract-ocr/tesseract/releases/latest).

## Usage

The project is based on the Unified Identity Authentication System of USTC, here is an example of how to login:

```python
from pyustc import Passport

passport = Passport()
passport.login('username', 'password')
```

If you have already logged in, you can save the token so that you don't need to login again next time:

```python
passport.save_token('token.json')
```

And then you can login next time with the saved token

```python
passport = Passport('token.json')
```

After you have logged in, you can use the `passport` object to access other services. For example, you can get your personal information:

```python
info = passport.get_info()
```

Or you can use the `EduSystem` to get your course table:

```python
from pyustc import EduSystem

es = EduSystem(passport)
table = es.get_course_table()
for course in table.courses:
    print(course)
```

## License

[MIT](https://github.com/USTC-XeF2/pyustc/blob/main/LICENSE)
