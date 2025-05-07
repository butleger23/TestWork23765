### Описание проекта:

Данный проект был создан для тестового задания по созданию простого ToDo приложения на FastApi.

### Как развернуть проект локально:

Склонировать проект:

```
git clone https://github.com/butleger23/TestWork23765.git

cd TestWork23765
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env

source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip

pip install -r requirements.txt
```

### Для запуска проекта в Docker (необходимо иметь Docker Desktop):

```
docker compose up -d
```
### Для запуска тестов:
Перейти в папку с приложением:
```
cd app
```
Запустить pytest
```
pytest или pytest main_test.py
```
