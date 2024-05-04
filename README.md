Описание проекта

Данный проект представляет собой скрипт для автоматизации взаимодействия с пользователями в мессенджере Telegram. С помощью этого скрипта можно организовать процесс отправки сообщений пользователям в зависимости от определенных условий и времени.

Стек технологий
Python 3
Pyrogram - клиент Telegram API для Python
SQLAlchemy - инструмент для работы с базами данных в Python
SQLite - встроенная СУБД, используемая для хранения данных
asyncio - модуль Python для организации асинхронного программирования
Установка зависимостей
Для установки зависимостей выполните следующую команду:

pip install pyrogram sqlalchemy


Использование
Настройка бота в Telegram:
Получите api_id и api_hash через my.telegram.org.

Настройка конфигурации:
Вставьте полученные api_id и api_hash в соответствующие переменные в коде.

Запуск скрипта:
python main.py

Описание скрипта

Скрипт состоит из следующих основных компонентов:

handle_user_deactivated: Декоратор для обработки исключений, возникающих при отправке сообщений пользователю, например, когда пользователь заблокировал бота или удален из Telegram.
send_message_with_error_handling: Асинхронная функция для отправки сообщения с обработкой ошибок.
bot_init: Инициализация бота Telegram.
check_finish_trigger: Проверка сообщения на наличие стоп-слов для завершения воронки.
mess_st: Обновление статуса сообщения для пользователя в базе данных.
voronka_finish: Смена статуса пользователя в базе данных на "finished".
check_customer_status: Бесконечная задача для проверки статуса пользователей и отправки сообщений по заданным условиям.
main: Основная функция скрипта, инициализирующая бота и запускающая задачи для обработки сообщений и проверки статуса пользователей.
