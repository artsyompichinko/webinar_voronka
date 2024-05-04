import time
import asyncio
from typing import Any
from pyrogram import Client, filters
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta


# Словарь тригеров и стоп слов
triggers = {'trg_finish': ["прекрасно", "ожидать"], 'trg_cancel_send': 'Триггер1'}

# Словарь сообщений для отправки
answers = {'msg_1': 'Текст1',
           'msg_2': 'Текст2',
           'msg_3': 'Текст3'
           }

engine = create_engine('sqlite:///users.db')
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='alive')
    status_updated_at = Column(DateTime, default=datetime.utcnow)
    message_status = (Column(String, default='msg_0'))


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def handle_user_deactivated(func: callable) -> callable:
    """
    Декоратор для обработки исключения UserDeactivated при отправке сообщения пользователю.

    Параметры:
        func (callable): Функция, которую нужно обернуть декоратором.

    Возвращает:
        callable: Обернутая функция с обработкой исключения.

    Пример использования:
        @handle_user_deactivated
        async def send_message_with_error_handling(bot, user_id, message):
            await bot.send_message(user_id, message)
    """
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print(e)
            print(f"Не удалось отправить сообщение пользователю с id {args[1]}")
            for word in ['BotBlocked', 'UserDeactivated']:
                if word.lower() in str(e).lower():
                    session = Session()
                    try:
                        user = session.query(User).filter(User.id == args[1]).first()
                        user.status = 'dead'
                        user.status_updated_at = datetime.utcnow()
                        session.commit()
                    finally:
                        session.close()
    return wrapper


@handle_user_deactivated
async def send_message_with_error_handling(bot: Any, u_id: int, message: str) -> None:
    """
    Асинхронная функция для отправки сообщения с обработкой ошибок, связанных с отправкой сообщений.

    Параметры:
        bot (Any): Объект бота или клиента для отправки сообщения.
        u_id (int): ID пользователя, которому нужно отправить сообщение.
        message (str): Текст сообщения, которое нужно отправить.

    Возвращает:
        None

    Пример использования:
        await send_message_with_error_handling(bot, user_id, "Привет, мир!")
    """
    await bot.send_message(u_id, message)


def bot_init() -> Client:
    """
    Инициализация юзер бота.

    Возвращает:
        Client: Объект клиента Pyrogram для взаимодействия с API Telegram.

    Пример использования:
        bot = bot_init()
    """
    api_hash: str = "ВАШ_АПИ_ХЭШ"
    api_id: str = "ВАШ_АПИ_ID"
    bot: Client = Client(name="my_account", api_id=api_id, api_hash=api_hash)
    return bot


def check_finish_trigger(message: str) -> bool:
    """
    Проверяет сообщение на наличие стоп-слов для завершения воронки.

    Параметры:
        message (str): Сообщение, которое нужно проверить.

    Возвращает:
        bool: True, если в сообщении есть хотя бы одно стоп-слово для завершения воронки, иначе False.
    """
    return any(True for trigg in triggers['trg_finish'] if trigg.lower() in message.lower())


def mess_st(u_id: int, status: str) -> None:
    """
    Обновляет статус сообщения для пользователя в базе данных.

    Параметры:
        u_id (int): ID пользователя.
        status (str): Новый статус сообщения.

    Возвращает:
        None

    Пример использования:
        mess_st(user_id, 'msg_2')
    """
    session: Session = Session()
    try:
        user = session.query(User).filter(User.id == u_id).first()
        user.message_status = status
        user.status_updated_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()


def voronka_finish(u_id: int) -> None:
    """ Смена статуса в бд на finished

        Параметры:
            u_id (int): ID пользователя.
    """
    print(2)
    session = Session()
    try:
        user = session.query(User).filter(User.id == u_id).first()
        user.status = 'finished'
        user.message_status = 'msg_3'
        user.status_updated_at = datetime.utcnow()
        session.commit()
    except Exception as e:
        print(e)
    finally:
        session.close()


async def check_customer_status(bot: Client) -> None:
    """ Бесконечная задача для проверки статуса и отправки сообщений пользователям по заданным точкам отсчёта времени

        bot: Объект клиента Pyrogram.
    """

    # Задержка для инициализации бота
    await asyncio.sleep(5)
    while True:
        session = Session()
        try:
            # Получаем всех пользователей со статусом alive
            alive_users = session.query(User).filter(User.status == 'alive').all()
        finally:
            session.close()

        for user in alive_users:
            # Время с последней смены статуса
            time_count = datetime.utcnow() - user.status_updated_at
            if time_count >= timedelta(minutes=1560) and user.message_status == 'msg_2':
                await send_message_with_error_handling(bot, user.id, answers['msg_3'])
                print(1)
                voronka_finish(user.id)
                continue

            if time_count >= timedelta(minutes=39) and user.message_status == 'msg_1':
                # Отправка второго сообщения с проверкой на слова завершения воронки и
                # проверкой на тригеры отменяющие отправку второго сообщения
                if triggers['trg_cancel_send'].lower() in answers['msg_2'].lower():
                    # Если находим триггер, то не отправляем, меняем статус сообщения
                    # и ждём времени отправки третьего сообщения
                    mess_st(user.id, 'msg_2')
                elif check_finish_trigger(answers['msg_2']):
                    # Если находим стоп слова, завершаем воронку
                    await send_message_with_error_handling(bot, user.id, answers['msg_2'])
                    voronka_finish(user.id)
                else:
                    await send_message_with_error_handling(bot, user.id, answers['msg_2'])
                    mess_st(user.id, 'msg_2')
                continue

            if time_count >= timedelta(minutes=6) and user.message_status == 'msg_0':
                if check_finish_trigger(answers['msg_1']):
                    await send_message_with_error_handling(bot, user.id, answers['msg_1'])
                    voronka_finish(user.id)
                else:
                    await send_message_with_error_handling(bot, user.id, answers['msg_1'])
                    mess_st(user.id, 'msg_1')

        await asyncio.sleep(5)


async def main():
    """ Основная функция скрипта.

        Инициализирует бота, обрабатывает сообщения от пользователей и запускает проверку статуса клиентов.

        Возвращает:
            None
    """
    bot_ = bot_init()
    # Задержка для инициализации бота
    time.sleep(1)

    @bot_.on_message(filters.private)
    async def handle_message(client, message):
        """ Обработчик сообщений от пользователей.

               Параметры:
                   client: Объект клиента Pyrogram.
                   message: Сообщение от пользователя.
        """
        # Получаем сообщение от клиента и если оно первое, заносим в базу
        user_id = message.from_user.id
        session = Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                user = User(id=user_id, chat_id=message.chat.id)
                session.add(user)
                session.commit()
        finally:
            session.close()
    # Запуск бота и задачи для отправки сообщений по времени от последнего действия клиента
    await asyncio.gather(bot_.start(), check_customer_status(bot_))

if __name__ == '__main__':
    asyncio.run(main())
