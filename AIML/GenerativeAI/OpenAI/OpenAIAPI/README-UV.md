# UV: Installation, Uninstallation & Basic Commands

### Documentation site: https://docs.astral.sh/uv/

## 1. Installation (macOS and Linux)

To install **UV** on macOS or Linux, run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
After installation, check the availability of `uv` by running the following command:

```bash
uv
```

```
echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
```


## 2. UV Uninstallation
```
$ uv cache clean
$ rm -r "$(uv python dir)"
$ rm -r "$(uv tool dir)"
```





## 3. Basic commands

### 3.1. Upgrade uv

``` 
$ uv self update
output: info: Checking for updates...
success: Upgraded uv from v0.7.2 to v0.7.4! https://github.com/astral-sh/uv/releases/tag/0.7.4

```

### 3.2 Getting started with a project [basicGenAI]

```
uv init basicGenAI  :  Create a new Python project.
```
Initialized project `basicgenai` at `/PATH/basicGenAI`
```
ls
```
basicGenAI	README.md


```
tree -a
.
├── basicGenAI
│   ├── .git
│   │   ├── config
│   │   ├── description
│   │   ├── HEAD
│   │   ├── hooks
│   │   │   ├── applypatch-msg.sample
│   │   │   ├── commit-msg.sample
│   │   │   ├── fsmonitor-watchman.sample
│   │   │   ├── post-update.sample
│   │   │   ├── pre-applypatch.sample
│   │   │   ├── pre-commit.sample
│   │   │   ├── pre-merge-commit.sample
│   │   │   ├── pre-push.sample
│   │   │   ├── pre-rebase.sample
│   │   │   ├── pre-receive.sample
│   │   │   ├── prepare-commit-msg.sample
│   │   │   ├── push-to-checkout.sample
│   │   │   └── update.sample
│   │   ├── info
│   │   │   └── exclude
│   │   ├── objects
│   │   │   ├── info
│   │   │   └── pack
│   │   └── refs
│   │       ├── heads
│   │       └── tags
│   ├── .gitignore
│   ├── .python-version
│   ├── main.py
│   ├── pyproject.toml
│   └── README.md
└── README.md
```


```
cd basicGenAI
```

Check Curretn Python
```
echo 'import sys; print(sys.version)' | uv run -
```
Using CPython 3.12.7 interpreter at: /opt/anaconda3/bin/python3.12
Creating virtual environment at: .venv
3.12.7 | packaged by Anaconda, Inc. | (main, Oct  4 2024, 08:22:19) [Clang 14.0.6 ]

Install Python version 3.13

```
uv python install 3.13 : Install Python versions.
```
Installed Python 3.13.3 in 1.20s
 + cpython-3.13.3-macos-aarch64-none

```
echo 'import sys; print(sys.version)' | uv run -
```
3.12.7 | packaged by Anaconda, Inc. | (main, Oct  4 2024, 08:22:19) [Clang 14.0.6 ]

#### 3.2.1 Create a virtual environment
```
uv venv
```
Using CPython 3.12.7 interpreter at: /opt/anaconda3/bin/python3.12
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate

```
source .venv/bin/activate
```

#### 3.2.2 Activating Python Version

```
uv venv --python 3.13
```
Using CPython 3.13.3
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate

```
python --version 
```
Python 3.12.7
```
source .venv/bin/activate

python --version 
```
        
Python 3.13.3

```
cat pyproject.toml
```
```
[project]
name = "basicgenai"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []
```

#### 3.2.3 Adding Python packages

```
uv add requests
```
```
[project]
name = "basicgenai"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "requests>=2.32.3",
]
```

```uv python pin 3.13
```
Updated `.python-version` from `3.12` -> `3.13`

Edit requires-python = ">=3.13" in pyproject.toml file

```
uv add openai
```

```
Resolved 21 packages in 170ms
Prepared 1 package in 98ms
Installed 14 packages in 21ms
 + annotated-types==0.7.0
 + anyio==4.9.0
 + distro==1.9.0
 + h11==0.16.0
 + httpcore==1.0.9
 + httpx==0.28.1
 + jiter==0.9.0
 + openai==1.78.1
 + pydantic==2.11.4
 + pydantic-core==2.33.2
 + sniffio==1.3.1
 + tqdm==4.67.1
 + typing-extensions==4.13.2
 + typing-inspection==0.4.0
```

```
 cat pyproject.toml 
```



```
[project]
name = "basicgenai"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "openai>=1.78.1",
    "requests>=2.32.3",
]
```

```
echo 'print("hello world!")' | uv run -
```
hello world!

```
uv add --dev ipykernel
```

```
cat pyproject.toml
```

```
[project]
name = "basicgenai"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "openai>=1.78.1",
    "requests>=2.32.3",
    "rich>=14.0.0",
]

[dependency-groups]
dev = [
    "ipykernel>=6.29.5",
]
```

```
uv remove --dev ipykernel
```

#### 3.2.4 Running Jupyter Notebook

```
uv run --with jupyter jupyter lab
```
