# Releasing Numeralform

1. Run the full unit suite.

   ```bash
   python -m unittest discover -s tests -v
   ```

2. Run offline validation with the committed corpora.

   ```bash
   python tools/validation/check.py --corpus tests/validation
   ```

3. Measure branch coverage and enforce the configured threshold.

   ```bash
   python -m coverage run --branch -m unittest discover -s tests -v
   python -m coverage report --fail-under=90
   ```

4. Check quality and build artifacts.

   ```bash
   ruff check .
   ruff format --check .
   python -m build --no-isolation
   ```

5. Inspect both artifacts. Their metadata and filenames must report `0.1.0`.

6. Install the wheel and sdist in clean environments. Verify:

   ```python
   import numeralform
   assert numeralform.__version__ == "0.1.0"
   assert numeralform.render(42, locale="en") == "forty-two"
   ```

   Also run `numeralform --version`, the rendering command, and verify `numeralform/py.typed`.

7. Create the `v0.1.0` tag only after required CI jobs pass. Publish the wheel and sdist using the project publishing policy.

8. After publishing, install from the published artifacts and repeat the version and rendering smoke tests.
