# Contributing to PQT Generator

Thank you for your interest in contributing!

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/jpmicrosoft/pqt_generator.git
   cd pqt_generator
   ```

2. Verify your Python version (3.8+ required):
   ```bash
   python --version
   ```

3. Run the tool to confirm it works:
   ```bash
   python process_dataflows.py --help
   ```

## Development

### No External Dependencies

This project uses only the Python standard library. Do not add external dependencies without discussion.

### Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints on all public functions
- Use `pathlib.Path` for file operations (not `os.path`)
- Use UTF-8 encoding for all file operations

### Running Tests

```bash
python -m pytest tests/ -v
```

### Testing on Multiple Platforms

Please test on both Windows and macOS/Linux when possible, especially for path-related changes.

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-change`
3. Make your changes with clear commit messages
4. Run tests: `python -m pytest tests/ -v`
5. Push and open a Pull Request

## Reporting Issues

Use [GitHub Issues](https://github.com/jpmicrosoft/pqt_generator/issues) with:
- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Error output (if applicable)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
