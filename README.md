# PyUSTC

[![pypi](https://img.shields.io/pypi/v/pyustc.svg)](https://pypi.python.org/pypi/pyustc)
![code size](https://img.shields.io/github/languages/code-size/USTC-XeF2/pyustc)
![last commit](https://img.shields.io/github/last-commit/USTC-XeF2/pyustc)
[![commits since last release](https://img.shields.io/github/commits-since/USTC-XeF2/pyustc/latest.svg)](https://github.com/USTC-XeF2/pyustc/releases)

A Python package that allows for quick use of USTC network services.

## Features

- **Central Authentication Service**: Simplifies login and session management.
- **Educational Administration Management System**: Access course table, grades, and course planning tools.
- **Young Platform**: Manage Second Classes.
- **Venue Booking (sport)**: Explore venues, query availability, and manage own orders.

## Installation and Usage

Install PyUSTC via pip:

```bash
pip install pyustc
```

For examples and detailed documentation, see [Examples](https://github.com/USTC-XeF2/pyustc/tree/main/examples).

Quick venue-booking example (see `examples/venue_booking.py` for details):

```python
import asyncio

from pyustc.venue_booking.core.auth import cas_login, login_with_token
from pyustc.venue_booking.personal import profile
from pyustc.venue_booking.venue.query import sport_index, venue_daily


async def main() -> None:
    client = login_with_token(token="...", open_id="...")

    await profile.my_current(client)
    await sport_index(client)
    await venue_daily(client, "tennis")
    await client.aclose()

    # 或 CAS 账密登录: client = await cas_login(username="...", password="...")


asyncio.run(main())
```

Booking and check-in writes are not included: those endpoints require a client-side generated verification field that cannot be reliably constructed from Python.

## Contributing

We welcome contributions of all types! Submit issues, code, or suggestions via [GitHub](https://github.com/USTC-XeF2/pyustc).

## License

[MIT](https://github.com/USTC-XeF2/pyustc/blob/main/LICENSE)
