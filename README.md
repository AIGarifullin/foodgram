# Проект "Фудграм" 
![workflow](https://github.com/AIGarifullin/foodgram/actions/workflows/main.yml/badge.svg)

## Описание проекта
Проект *Фудграм* позволяет зарегистрированным пользователям создавать/обновлять/получать/удалять свои публикации с рецептами, подписываться на других авторов, добавлять/удалять их рецепты из избранного, а также формировать/выгружать список покупок необходимых ингредиентов для приготовления блюда по рецепту. Пользователь может приложить свою фотографию-аватар и фотографии блюд в постах-рецептах. Фильтрация рецептов возможна при помощи тегов. 

![Header](https://pictures.s3.yandex.net/resources/image_1711954469.png)

## Стек проекта
Python, Django REST Framework, Nginx, DNS, HTTPS, Docker, PostgreSQL, GitHub Actions

## Ссылка на развернутый проект
https://foodgramprojaig.ddns.net

## Запуск документации проекта
Находясь в папке infra, выполните команду **docker-compose up**. При выполнении этой команды контейнер `frontend`, описанный в **docker-compose.yml**, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

## Запуск локальной версии проекта
Перейти в директорию с файлом **docker-compose.yml**, выполнить запуск и миграции:

```
docker compose up
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/static/. /backend_static/static/
```

## Отличия обычной версии проекта от продакш
Продакш-версия проекта позволяет:
* Автоматизировать запуск и обновление приложения;
* Сделать запуск приложения воспроизводимым на любых серверах, независимо от настроек.

## Запуск продакш-версии проекта
Для этого необходимо:
1. Собрать образы `foodgram_frontend`, `foodgram_backend` и `foodgram_gateway` и залить их на Docker Hub:

    ```
    cd frontend
    docker build -t username/foodgram_frontend .
    cd ../backend
    docker build -t username/foodgram_backend .
    cd ../infra
    docker build -t username/foodgram_gateway .
    ```
    ```
    docker push username/foodgram_frontend
    docker push username/foodgram_backend
    docker push username/foodgram_gateway
    ```    
2. Создать в корневой директории проекта файл конфигурации **docker-compose.production.yml**, который будет использовать собранные образы на Docker Hub и управлять запуском контейнеров на продакш-сервере. Отличие нового файла конфигурации от **docker-compose.yml** состоит в замене `build` на `image` с указанием ссылки на образ (`postgres:13.10` для `db`, `username/foodgram_frontend` для `frontend`, `username/foodgram_backend` для `backend` и `username/foodgram_gateway` для `gateway`).  

3. Развернуть и запустить Docker на сервере. Поочередно выполнить на сервере следующие команды:
    ```
    sudo apt update
    sudo apt install curl
    curl -fSL https://get.docker.com -o get-docker.sh
    sudo sh ./get-docker.sh
    sudo apt install docker-compose-plugin
    ```
4. Загрузить на сервер новый файл конфигурации для Docker Compose и запустить контейнеры.
    Поместить в директорию проекта на сервере файл конфигурации **docker-compose.production.yml**, а также файл **.env**.
    Выполнить команду на сервере в папке проекта:
    ```
    sudo docker compose -f docker-compose.production.yml up -d
    ```
    Выполнить миграции, собрать статические файлы бэкенда и скопировать их в `/backend_static/static/`:
    ```
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
    sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/static/. /backend_static/static/
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
    ```
5. Настроить «внешний» Nginx, что вне контейнера — для работы с приложением в контейнерах.
    Открыть файл **default** конфигурации Nginx:
    
    ```
    sudo nano /etc/nginx/sites-enabled/default
    ```
    Изменить настройки `location` в секции `server` (три блока `location` заменить на один):
    ```
    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:7000;
    }
    ```
    Сделать проверку и перезагрузку файла конфигурации:
    ```
    sudo nginx -t
    sudo service nginx reload
    ```

6. Подготовить свой удаленный сервер к публикации проекта. Очистить диск сервера от лишних данных (кеш npm, APT, старые системные логи): 
    ```
    npm cache clean --force
    sudo apt clean
    sudo journalctl --vacuum-time=1d
    ```
    Полезно будет выполнить команду `sudo docker system prune -af`: она уберёт все лишние объекты, которые вы могли создать в докере за время выполнения заданий спринта, — неиспользуемые контейнеры, образы и сети.

7. Для автоматизации запуска и обновления проекта на продакш-сервере создать в директории `.github/workflows` файл **main.yml** с описанием *workflow*. Сделать коммит проекта и разместить его в удаленный репозиторий:
    ```
    git add .
    git commit -m 'Add Actions'
    git push
    ```
    Для управления процессами *CI/CD* (*Continuous Integration/Continuous Delivery*) открыть раздел *Actions* в репозитории проекта в своем аккаунте.


_Текст данного файла составил [Адель Гарифуллин](https://github.com/AIGarifullin)._