# envchain

Lightweight utility to manage and validate environment variable chains across dev/staging/prod configs.

---

## Installation

```bash
pip install envchain
```

---

## Usage

Define your environment variable chain in a `.envchain.yml` file:

```yaml
chains:
  database:
    - DB_HOST
    - DB_PORT
    - DB_NAME
  auth:
    - SECRET_KEY
    - JWT_EXPIRY
```

Then validate and load your config in Python:

```python
from envchain import EnvChain

chain = EnvChain(env="staging", config=".envchain.yml")
chain.validate()  # Raises if any required variables are missing

db_host = chain.get("DB_HOST")
```

Run validation from the command line:

```bash
envchain validate --env production
```

If any variables in the chain are missing, `envchain` will report exactly which ones are absent and in which environment — no more silent misconfigurations at deploy time.

---

## Features

- Validate required environment variables per environment (dev/staging/prod)
- Chain dependencies so related vars are checked together
- CLI and Python API support
- Minimal dependencies, easy to integrate into CI/CD pipelines

---

## License

MIT © [envchain contributors](https://github.com/yourname/envchain)