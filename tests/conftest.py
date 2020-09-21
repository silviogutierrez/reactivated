import site
from typing import Any


def pytest_configure(config: Any) -> None:
    # See: https://github.com/typeddjango/pytest-mypy-plugins/issues/34
    site_packages = site.getsitepackages()[0]
    for file_name, line_numbers in FILES:
        file_path = f"{site_packages}/{file_name}.pyi"

        with open(file_path, "r") as file_in:
            file_lines = []

            for index, line in enumerate(file_in.readlines()):
                line_number = index + 1
                if line_number in line_numbers and "ignore" not in line:
                    file_lines.append(
                        f"{line.rstrip()}  # type: ignore[var-annotated]\n"
                    )
                else:
                    file_lines.append(line)
        with open(file_path, "w") as file_out:
            file_out.writelines(file_lines)


FILES = [
    ("django-stubs/contrib/auth/base_user", (18, 19)),
    (
        "django-stubs/contrib/auth/models",
        (23, 24, 25, 34, 35, 57, 58, 59, 70, 71, 72, 73, 74, 75, 76),
    ),
    ("django-stubs/contrib/sites/models", (17, 18)),
]
