from pathlib import Path
import subprocess


PROJECT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = PROJECT_DIR.parent / "lab_env" / "Scripts" / "python.exe"
PARSER_SCRIPT = PROJECT_DIR / "kazan_news.py"
TASK_NAME = "KazanNewsRSSCollector"


def main():
    missing_paths = [path for path in (PYTHON_EXE, PARSER_SCRIPT) if not path.is_file()]
    if missing_paths:
        for path in missing_paths:
            print(f"Не найден файл: {path}")
        raise SystemExit(1)

    task_command = f'"{PYTHON_EXE}" "{PARSER_SCRIPT}"'
    command = [
        "schtasks",
        "/Create",
        "/TN",
        TASK_NAME,
        "/SC",
        "MINUTE",
        "/MO",
        "30",
        "/TR",
        task_command,
        "/F",
    ]

    result = subprocess.run(command, check=False, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print(f"Задача {TASK_NAME} создана: запуск каждые 30 минут.")
    print(f"Python: {PYTHON_EXE}")
    print(f"Парсер: {PARSER_SCRIPT}")
    print(f"Рабочая папка проекта: {PROJECT_DIR}")
    print("Планировщик запускает задачу от имени текущего пользователя Windows.")
    print("Лог парсера: logs\\kazan_news.log")


if __name__ == "__main__":
    main()
