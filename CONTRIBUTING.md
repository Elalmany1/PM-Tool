# CONTRIBUTING.md

## Contributing to PM-Tool

We welcome contributions! Here's how to get started:

### Local Setup

```bash
# Clone the repo
git clone https://github.com/Elalmany1/PM-Tool.git
cd PM-Tool

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r api_requirements.txt

# Run the API
python kpi_api.py
```

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Test locally at `http://localhost:8000/docs`
4. Commit: `git commit -am 'Add feature description'`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request

### Code Style

- Use descriptive variable names
- Add docstrings to functions
- Follow PEP 8 conventions
- Add type hints where possible

### Adding New Metrics

1. Create a new endpoint in `kpi_api.py`
2. Add Pydantic model for request validation
3. Implement metric calculation
4. Add benchmark interpretation
5. Add to Postman collection
6. Document in `API_DOCUMENTATION.md`

### Testing

All changes should be compatible with:
- FastAPI 0.104+
- Python 3.8+
- Deployment via Docker

### PR Guidelines

- One feature per PR
- Clear description of changes
- Reference any related issues
- Ensure GitHub Actions pass

---

Thank you for contributing! 🎉
