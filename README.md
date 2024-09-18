# Foodgram приложение

![workflow branch main](https://github.com/VadimVolkov87/foodgram/actions/workflows/main.yml/badge.svg?branch=main)

Репозиторий `foodgram` содержит SPA приложение для развертывания web сайта, который предоставляет возможность пользователям поделиться опытом в приготовлении разнообразных и вкусных блюд. Приложение позволяет создавать, редактировать, удалять, получать информацию о рецептах различных блюд, подписываться на любимых авторов, выбирать понравившиеся рецептыБ и формировать корзину продуктов для покупок.Просмотр контента доступен любому пользователю, а редактирование\удаление контента, подписки, создание избранного и корзины для покупок доступно только только авторизованным пользователям и авторам.

## Стек приложения

Приложение создано на основе:

* Python 3.9.13
* Django 3.2.16
* djangorestframework 3.12.4
* djoser 2.2.2
* gunicorn 20.1.0
* Node.js 18
* postgres 13

## Для запуска проекта необходимо

Клонировать репозиторий:

```text
git clone https://github.com/VadimVolkov87/foodgram.git
```

В корне проекта создать файл .env

Внести в файл следующие переменные:

* POSTGRES_USER - имя пользователя БД
* POSTGRES_PASSWORD - пароль пользователя БД
* POSTGRES_DB - название базы данных (необязательная переменная, по умолчанию совпадает с POSTGRES_USER)
* DB_HOST — адрес, по которому Django будет соединяться с базой данных
* DB_PORT — порт, по которому Django будет обращаться к базе данных (по умолчанию 5432)

Внести в Actions secrets следующие переменные:

* DOCKER_USERNAME - логин для Docker
* DOCKER_PASSWORD - пароль аккаунта Docker
* HOST - ip сервера
* USER - логин на сервере
* SSH_KEY - закрытый SSH-ключ к аккаунту на сервере
* SSH_PASSPHRASE - кодовая фраза к аккаунту на сервере
* TELEGRAM_TO - ID вашего телеграмм аккаунта
* TELEGRAM_TOKEN - токен вашего телеграмм-бота

Отправить приложение в свой репозиторий на GitHub:

git push

После получения уведомления от телеграмм-бота открыть страницу по вашему доменному имени приложения в браузере.

## Авторы проекта

Вадим Волков - разработка

```text
https://github.com/VadimVolkov87/foodgram
```

Евгений Салахутдинов - код-ревью
