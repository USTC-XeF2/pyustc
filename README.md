# PyUSTC

[![pypi](https://img.shields.io/pypi/v/pyustc.svg)](https://pypi.python.org/pypi/pyustc)
![code size](https://img.shields.io/github/languages/code-size/USTC-XeF2/pyustc)
![last commit](https://img.shields.io/github/last-commit/USTC-XeF2/pyustc)
[![commits since last release](https://img.shields.io/github/commits-since/USTC-XeF2/pyustc/latest.svg)](https://github.com/USTC-XeF2/pyustc/releases)

A Python package that allows for quick use of USTC network services.

## Features

- **Unified Identity Authentication System**: Simplifies login and session management.
- **Educational System**: Access course table, grades, and course planning tools.
- **Young Platform**: Manage Second Classes.

## Installation

Install PyUSTC via pip:

```bash
pip install pyustc
```

## Quick Start

Here's an example of logging in via the UIAS:

```python
from pyustc import Passport

passport = Passport()
passport.login_by_pwd('username', 'password')
```

Access your course table via the EduSystem module:

```python
from pyustc import EduSystem

es = EduSystem(passport)
table = es.get_course_table()
for course in table.courses:
    print(course)
```

For more examples and detailed documentation, see [here](https://github.com/USTC-XeF2/pyustc/wiki).

## Contributing

We welcome contributions of all types! Submit issues, code, or suggestions via [GitHub](https://github.com/USTC-XeF2/pyustc).

## License

[MIT](https://github.com/USTC-XeF2/pyustc/blob/main/LICENSE)
