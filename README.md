# Todolist

## Дипломный проект

### О проекте
Программа для создания, отслеживания и совместной работы с целями с возможностью работы через telegram-бота.

### Оновной стек проекта:
![version](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![version](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![version](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)

#### Установка зависимостей:

В корневой папке находится файл с зависимостями requirements.txt
```shell
pip install -r requirements.txt
```

#### Настройка переменных окружения:

Для работы проекта необходимо создать **.env** в корневой папке.
В нем нужно указать необходимые значения переменных:

* SECRET_KEY = **секретный ключ**
* DATABASE_URL = **psql://<имя пользователя>:<пароль пользователя>@<ip адрес>:<порт>/<имя базы>**
* SOCIAL_AUTH_VK_OAUTH2_KEY = **ключ приложения ВК**
* SOCIAL_AUTH_VK_OAUTH2_SECRET = **секрет приложения ВК**
* TG_TOKEN = **токен телеграм бота**


### Запуск проекта Django:

* Перед запуском накатываем миграции на базу данных:

```shell
python ./manage.py migrate
```
* Запуск проекта:

```shell
python ./manage.py runserver
```

* Команда для запуска telegram-бота

````shell
python ./manage.py runbot
````
