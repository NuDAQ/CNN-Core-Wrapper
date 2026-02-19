# CNN-Core-Wrapper
A CNN Core Wrapper for ARIANNA Trigger System. 

## Dependency
```
python -m venv .venv
pip install -r requirements.txt
```

## Bender
```
bender update
bender script vivado > add_sources.tcl
```

Open Vivado
```
source /path/to/add_sources.tcl
```

`.xdc` files should be added manually.

## Notice
- Open Vivado from this directory, not from root or project repository.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
