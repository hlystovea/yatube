# Личный блог (учебный проект на Яндекс.Практикум)

### Описание
Сайт предназначен для ведения своего блога.

### Возможности
- Создание постов
- Подписка на авторов
- Подписка на группы

### Технологии
- Python 3
- Django

### Начало работы

1. Склонируйте проект:


```git clone https://github.com/hlystovea/hw05_final.git```  


2. Создайте файл .env по примеру env.example.


3. Создайте и активируйте виртуальное окружение:

```python -m venv venv```
```source venv/bin/activate ```

4. Установите зависимости из файла requirements.txt

```pip install -r requirements.txt```

4. Запустите миграции:

```python manage.py migrate```

5. Соберите статику:

```python manage.py collectstatic```

6. Создайте своего суперпользователя:

```python manage.py createsuperuser```

7. Сайт будет доступен по адресу:
 
```http://127.0.0.1:8000```


