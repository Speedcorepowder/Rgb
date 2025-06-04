import logging
import asyncio
import sqlite3
import os
import threading
import aiohttp
import json
import math
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Конфигурация
API_TOKEN = os.getenv('API_TOKEN')
DRIVER_GROUP_ID = -1002619469979
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# === ЛОКАЛИЗАЦИЯ ===
TRANSLATIONS = {
    'ru': {
        # Главное меню
        'welcome': 'Добро пожаловать в RigaGo! Выберите действие:',
        'order_taxi': '🚖 Заказать водителя',
        'back': '🔙 Назад',

        # Водительское меню
        'driver_menu': 'Меню водителя\nДобро пожаловать, {}!',
        'not_registered_driver': 'Вы не зарегистрированы как водитель. Заполните анкету:',
        'fill_driver_form': '📝 Заполнить анкету водителя',
        'balance': '💰 Баланс',
        'my_profile': '📋 Моя анкета',
        'order_stats': '📊 Количество заказов',
        'request_balance': '💳 Запросить баланс',

        # Регистрация водителя
        'enter_name': 'Введите ваше имя и фамилию:',
        'enter_car_number': 'Введите номер автомобиля:',
        'enter_car_model': 'Введите марку автомобиля:',
        'check_data': '📋 <b>Проверьте данные анкеты:</b>\n\n👤 Имя: {}\n🚗 Номер авто: {}\n🏷 Марка авто: {}\n\nВсё верно?',
        'save_profile': '💾 Сохранить анкету',
        'cancel': '❌ Отменить',
        'profile_saved': '✅ Анкета успешно сохранена! Добро пожаловать в команду водителей!\n\n🚗 <b>Меню водителя</b>\n👤 Добро пожаловать, {}!',
        'already_registered': 'Вы уже зарегистрированы! Для изменения данных обратитесь к администратору.',

        # Заказ водителя
        'send_location': 'Пожалуйста, отправьте вашу текущую геолокацию или введите адрес вручную.',
        'send_location_btn': '📍 Отправить локацию',
        'enter_address_manually': '✍️ Ввести адрес вручную',
        'enter_current_address': 'Введите ваш текущий адрес:',
        'order_cancelled': '🚫 Заказ отменен.',
        'your_location': '📍 Ваше местоположение: {}\n\nТеперь введите адрес назначения:',
        'enter_destination': '✍️ Ввести адрес назначения',
        'enter_destination_text': '✍️ Введите адрес назначения текстом:',
        'address_not_found': '❌ Не удалось найти указанный адрес. Попробуйте ввести адрес более точно.',
        'order_details': '📋 <b>Детали заказа:</b>\n🔹 Откуда: {}\n🔹 Куда: {}\n📏 Расстояние: {:.1f} км\n⏱ Время: {:.0f} мин\n💰 Стоимость: {}€\n\nПодтвердить заказ?',
        'confirm_order': '✅ Подтвердить заказ',
        'order_placed': '✅ Заказ размещен в группе водителей!\nОжидайте, когда водитель свяжется с вами напрямую.',
        'order_error': '❌ Произошла ошибка при размещении заказа.\nПопробуйте еще раз или обратитесь в поддержку.',
        'suggest_price': 'Предложить свою цену',

        # Информация водителя
        'current_balance': '💰 Ваш текущий баланс: {:.2f}€',
        'profile_info': '📋 <b>Ваша анкета:</b>\n\n👤 Имя: {}\n🚗 Номер авто: {}\n🏷 Марка авто: {}\n💰 Баланс: {:.2f}€\n{}\n\n<i>Для изменения данных обратитесь к администратору</i>',
        'rating_info': '⭐ Рейтинг: {}/5.0 ({} оценок)',
        'no_rating': '⭐ Рейтинг: нет оценок',
        'stats_info': '📊 <b>Ваша статистика:</b>\n\n📅 <b>За сегодня:</b>\n🚖 Заказов: {}\n💰 Заработок: {:.2f}€\n\n📅 <b>За неделю:</b>\n🚖 Заказов: {}\n💰 Заработок: {:.2f}€\n\n📅 <b>За месяц:</b>\n🚖 Заказов: {}\n💰 Заработок: {:.2f}€',
        'balance_request_sent': '💳 Ваш запрос на пополнение баланса отправлен администратору.',
        'balance_topped_up': 'Ваш баланс пополнен администратором на {0}€\nНовый баланс: {1:.2f}€',

        # Заказы
        'new_order': '🚖 <b>НОВЫЙ ЗАКАЗ! #{}</b>\n\n👤 Клиент: {}\n📱 Username: {}\n{}\n📍 <b>Откуда:</b> {}\n🎯 <b>Куда:</b> {}\n📏 Расстояние: {:.1f} км\n⏱ Время: {:.0f} мин\n💰 <b>Цена:</b> {}€\n\n',
        'accept_order': '✅ Принять заказ',
        'order_accepted': '✅ <b>ЗАКАЗ #{} ПРИНЯТ</b>\n\n🚗 Водитель: {}\n📱 Username: @{}\n{}\n\n👤 Клиент: {}\n📍 <b>Откуда:</b> {}\n🎯 <b>Куда:</b> {}\n📏 Расстояние: {:.1f} км\n⏱ Время: {:.0f} мин\n💰 <b>Цена:</b> {}€',
        'order_taken_by_driver': '🚗 <b>Ваш заказ принят!</b>\n\nВодитель: {}\nUsername: @{}\n{}\nКонтакт: <a href=\'tg://user?id={}\'>Написать водителю</a>\n\nВодитель скоро с вами свяжется!',
        'complete_order': '✅ Завершить заказ',
        'order_completed': '✅ <b>Заказ #{} завершен!</b>\n\nОцените поездку с водителем {}:',
        'rate_trip': '✅ <b>Заказ #{} завершен!</b>\n\nВаша оценка: {}\nСпасибо за использование RigaGo!',
        'rate_client': '✅ <b>Заказ #{} завершен!</b>\n\nОцените клиента {}:',
        'client_rated': 'Спасибо за оценку клиента! {}',

        # Ошибки
        'not_driver': 'Вы не зарегистрированы как водитель.',
        'order_not_found': '❌ Заказ не найден или уже удален',
        'order_already_taken': '❌ Заказ уже принят другим водителем',
        'not_registered': '❌ Вы не зарегистрированы как водитель',
        'driver_banned': '❌ Вы заблокированы до {} из-за низкого рейтинга',
        'low_balance': '❌ Недостаточно средств на балансе. Минимум 0.50€ для принятия заказа',
        'active_order_exists': '❌ У вас уже есть активный заказ. Завершите его перед принятием нового.',

        # Админ
        'admin_panel': '🛠 <b>Админ-панель</b>\n\nВыберите раздел:',
        'drivers': '👥 Водители',
        'orders': '📋 Заказы',
        'no_access': '❌ У вас нет доступа к админ-панели.',

        # Дополнительные сообщения
        'already_rated': 'Вы уже оценили этот заказ',
        'thanks_for_rating': 'Спасибо за оценку! {}',
        'order_completed_driver': '✅ Заказ завершен!',
        'order_payment_info': '✅ <b>Заказ #{} завершен!</b>\n\n💰 Оплата: {:.2f}€ (получите наличными от клиента)\n💳 Комиссия: 0.50€ (списана с баланса)\n\nСпасибо за работу!',
        'new_rating_received': '📊 <b>Новая оценка: {}</b>\n\nВаш текущий рейтинг: {}',
        'rating_ban_warning': '📊 <b>Новая оценка: {}</b>\n\nВаш текущий рейтинг: {}\n\n⚠️ <b>ВНИМАНИЕ!</b> Ваш рейтинг упал ниже 4.1. Вы заблокированы на неделю до {}.\nДля разблокировки повысьте качество обслуживания.',
        'minimum_price_error': 'Минимальная цена заказа {}€.',
        'enter_valid_price': 'Пожалуйста, введите корректную цену (число).',
        'active_order_client': '❌ У вас уже есть активный заказ. Дождитесь его завершения или отмены перед созданием нового.'
    },
    'lv': {
        # Главное меню
        'welcome': 'Laipni lūdzam RigaGo! Izvēlieties darbību:',
        'order_taxi': '🚖 Pasūtīt šoferi',
        'back': '🔙 Atpakaļ',

        # Водительское меню
        'driver_menu': 'Šofera izvēlne\nLaipni lūdzam, {}!',
        'not_registered_driver': 'Jūs neesat reģistrēts kā šoferis. Aizpildiet anketu:',
        'fill_driver_form': '📝 Aizpildīt šofera anketu',
        'balance': '💰 Bilance',
        'my_profile': '📋 Mana anketa',
        'order_stats': '📊 Pasūtījumu skaits',
        'request_balance': '💳 Pieprasīt bilanci',

        # Регистрация водителя
        'enter_name': 'Ievadiet savu vārdu un uzvārdu:',
        'enter_car_number': 'Ievadiet automašīnas numuru:',
        'enter_car_model': 'Ievadiet automašīnas marku:',
        'check_data': '📋 <b>Pārbaudiet anketas datus:</b>\n\n👤 Vārds: {}\n🚗 Auto numurs: {}\n🏷 Auto marka: {}\n\nViss pareizi?',
        'save_profile': '💾 Saglabāt anketu',
        'cancel': '❌ Atcelt',
        'profile_saved': '✅ Anketa veiksmīgi saglabāta! Laipni lūdzam šoferu komandā!\n\n🚗 <b>Šofera izvēlne</b>\n👤 Laipni lūdzam, {}!',
        'already_registered': 'Jūs jau esat reģistrēts! Lai mainītu datus, sazinieties ar administratoru.',

        # Заказ водителя
        'send_location': 'Lūdzu, nosūtiet savu pašreizējo ģeogrāfisko atrašanās vietu vai ievadiet adresi manuāli.',
        'send_location_btn': '📍 Nosūtīt atrašanās vietu',
        'enter_address_manually': '✍️ Ievadīt adresi manuāli',
        'enter_current_address': 'Ievadiet savu pašreizējo adresi:',
        'order_cancelled': '🚫 Pasūtījums atcelts.',
        'your_location': '📍 Jūsu atrašanās vieta: {}\n\nTagad ievadiet galamērķa adresi:',
        'enter_destination': '✍️ Ievadīt galamērķa adresi',
        'enter_destination_text': '✍️ Ievadiet galamērķa adresi ar tekstu:',
        'address_not_found': '❌ Neizdevās atrast norādīto adresi. Mēģiniet ievadīt adresi precīzāk.',
        'order_details': '📋 <b>Pasūtījuma detaļas:</b>\n🔹 No kurienes: {}\n🔹 Uz kurieni: {}\n📏 Attālums: {:.1f} km\n⏱ Laiks: {:.0f} min\n💰 Izmaksas: {}€\n\nApstiprināt pasūtījumu?',
        'confirm_order': '✅ Apstiprināt pasūtījumu',
        'order_placed': '✅ Pasūtījums ievietots šoferu grupā!\nGaidiet, kad šoferis ar jums sazināsies tieši.',
        'order_error': '❌ Pasūtījuma ievietošanas laikā radās kļūda.\nMēģiniet vēlreiz vai sazinieties ar atbalstu.',
        'suggest_price': 'Piedāvāt savu cenu',

        # Информация водителя
        'current_balance': '💰 Jūsu pašreizējā bilance: {:.2f}€',
        'profile_info': '📋 <b>Jūsu anketa:</b>\n\n👤 Vārds: {}\n🚗 Auto numurs: {}\n🏷 Auto marka: {}\n💰 Bilance: {:.2f}€\n{}\n\n<i>Lai mainītu datus, sazinieties ar administratoru</i>',
        'rating_info': '⭐ Reitings: {}/5.0 ({} vērtējumi)',
        'no_rating': '⭐ Reitings: nav vērtējumu',
        'stats_info': '📊 <b>Jūsu statistika:</b>\n\n📅 <b>Šodien:</b>\n🚖 Pasūtījumi: {}\n💰 Ieņēmumi: {:.2f}€\n\n📅 <b>Šonedēļ:</b>\n🚖 Pasūtījumi: {}\n💰 Ieņēmumi: {:.2f}€\n\n📅 <b>Šomēnes:</b>\n🚖 Pasūtījumi: {}\n💰 Ieņēmumi: {:.2f}€',
        'balance_request_sent': '💳 Jūsu pieprasījums bilances papildināšanai nosūtīts administratoram.',
        'balance_topped_up': 'Jūsu bilance ir papildināta par {0}€\nJaunā bilance: {1:.2f}€',

        # Заказы
        'new_order': '🚖 <b>JAUNS PASŪTĪJUMS! #{}</b>\n\n👤 Klients: {}\n📱 Lietotājvārds: {}\n{}\n📍 <b>No kurienes:</b> {}\n🎯 <b>Uz kurieni:</b> {}\n📏 Attālums: {:.1f} km\n⏱ Laiks: {:.0f} min\n💰 <b>Cena:</b> {}€\n\n',
        'accept_order': '✅ Pieņemt pasūtījumu',
        'order_accepted': '✅ <b>PASŪTĪJUMS #{} PIEŅEMTS</b>\n\n🚗 Šoferis: {}\n📱 Lietotājvārds: @{}\n{}\n\n👤 Klients: {}\n📍 <b>No kurienes:</b> {}\n🎯 <b>Uz kurieni:</b> {}\n📏 Attālums: {:.1f} km\n⏱ Laiks: {:.0f} min\n💰 <b>Cena:</b> {}€',
        'order_taken_by_driver': '🚗 <b>Jūsu pasūtījums pieņemts!</b>\n\nŠoferis: {}\nLietotājvārds: @{}\n{}\nKontakts: <a href=\'tg://user?id={}\'>Rakstīt šoferim</a>\n\nŠoferis drīz ar jums sazināsies!',
        'complete_order': '✅ Pabeigt pasūtījumu',
        'rate_trip': '✅ <b>Pasūtījums #{} pabeigts!</b>\n\nJūsu vērtējums: {}\nPaldies, ka izmantojat RigaGo!',
        'rate_client': '✅ <b>Pasūtījums #{} pabeigts!</b>\n\nNovērtējiet klientu {}:',
        'client_rated': 'Paldies par klienta vērtējumu! {}',

        # Ошибки
        'not_driver': 'Jūs neesat reģistrēts kā šoferis.',
        'order_not_found': '❌ Pasūtījums nav atrasts vai jau dzēsts',
        'order_already_taken': '❌ Pasūtījumu jau pieņēmis cits šoferis',
        'not_registered': '❌ Jūs neesat reģistrēts kā šoferis',
        'driver_banned': '❌ Jūs esat bloķēts līdz {} zema reitinga dēļ',
        'low_balance': '❌ Nepietiek līdzekļu bilancē. Minimums 0.50€ pasūtījuma pieņemšanai',
        'active_order_exists': '❌ Jums jau ir aktīvs pasūtījums. Pabeidziet to pirms jauna pieņemšanas.',

        # Админ
        'admin_panel': '🛠 <b>Administratora panelis</b>\n\nIzvēlieties sadaļu:',
        'drivers': '👥 Šoferi',
        'orders': '📋 Pasūtījumi',
        'no_access': '❌ Jums nav piekļuves administratora panelim.',

        # Дополнительные сообщения
        'already_rated': 'Jūs jau esat novērtējis šo pasūtījumu',
        'thanks_for_rating': 'Paldies par vērtējumu! {}',
        'order_completed_driver': '✅ Pasūtījums pabeigts!',
        'order_payment_info': '✅ <b>Pasūtījums #{} pabeigts!</b>\n\n💰 Maksājums: {:.2f}€ (saņemiet skaidrā naudā no klienta)\n💳 Komisija: 0.50€ (norakstīta no bilances)\n\nPaldies par darbu!',
        'new_rating_received': '📊 <b>Jauns vērtējums: {}</b>\n\nJūsu pašreizējais reitings: {}',
        'rating_ban_warning': '📊 <b>Jauns vērtējums: {}</b>\n\nJūsu pašreizējais reitings: {}\n\n⚠️ <b>UZMANĪBU!</b> Jūsu reitings nokritis zem 4.1. Jūs esat bloķēts uz nedēļu līdz {}.\nLai atbloķētu, uzlabojiet pakalpojumu kvalitāti.',
        'minimum_price_error': 'Minimālā pasūtījuma cena {}€.',
        'enter_valid_price': 'Lūdzu, ievadiet pareizu cenu (skaitli).',
        'active_order_client': '❌ Jums jau ir aktīvs pasūtījums. Gaidiet tā pabeigšanu vai atcelšanu pirms jauna izveidošanas.'
    },
    'en': {
        # Главное меню
        'welcome': 'Welcome to RigaGo! Choose an action:',
        'order_taxi': '🚖 Order driver',
        'back': '🔙 Back',

        # Водительское меню
        'driver_menu': 'Driver menu\nWelcome, {}!',
        'not_registered_driver': 'You are not registered as a driver. Fill out the form:',
        'fill_driver_form': '📝 Fill driver form',
        'balance': '💰 Balance',
        'my_profile': '📋 My profile',
        'order_stats': '📊 Order statistics',
        'request_balance': '💳 Request balance',

        # Регистрация водителя
        'enter_name': 'Enter your first and last name:',
        'enter_car_number': 'Enter car number:',
        'enter_car_model': 'Enter car model:',
        'check_data': '📋 <b>Check form data:</b>\n\n👤 Name: {}\n🚗 Car number: {}\n🏷 Car model: {}\n\nIs everything correct?',
        'save_profile': '💾 Save profile',
        'cancel': '❌ Cancel',
        'profile_saved': '✅ Profile successfully saved! Welcome to the driver team!\n\n🚗 <b>Driver menu</b>\n👤 Welcome, {}!',
        'already_registered': 'You are already registered! To change data, contact administrator.',

        # Заказ водителя
        'send_location': 'Please send your current geolocation or enter address manually.',
        'send_location_btn': '📍 Send location',
        'enter_address_manually': '✍️ Enter address manually',
        'enter_current_address': 'Enter your current address:',
        'order_cancelled': '🚫 Order cancelled.',
        'your_location': '📍 Your location: {}\n\nNow enter destination address:',
        'enter_destination': '✍️ Enter destination address',
        'enter_destination_text': '✍️ Enter destination address as text:',
        'address_not_found': '❌ Could not find the specified address. Try entering the address more precisely.',
        'order_details': '📋 <b>Order details:</b>\n🔹 From: {}\n🔹 To: {}\n📏 Distance: {:.1f} km\n⏱ Time: {:.0f} min\n💰 Cost: {}€\n\nConfirm order?',
        'confirm_order': '✅ Confirm order',
        'order_placed': '✅ Order placed in drivers group!\nWait for a driver to contact you directly.',
        'order_error': '❌ Error occurred while placing order.\nTry again or contact support.',
        'suggest_price': 'Suggest your price',

        # Информация водителя
        'current_balance': '💰 Your current balance: {:.2f}€',
        'profile_info': '📋 <b>Your profile:</b>\n\n👤 Name: {}\n🚗 Car number: {}\n🏷 Car model: {}\n💰 Balance: {:.2f}€\n{}\n\n<i>To change data, contact administrator</i>',
        'rating_info': '⭐ Rating: {}/5.0 ({} ratings)',
        'no_rating': '⭐ Rating: no ratings',
        'stats_info': '📊 <b>Your statistics:</b>\n\n📅 <b>Today:</b>\n🚖 Orders: {}\n💰 Earnings: {:.2f}€\n\n📅 <b>This week:</b>\n🚖 Orders: {}\n💰 Earnings: {:.2f}€\n\n📅 <b>This month:</b>\n🚖 Orders: {}\n💰 Earnings: {:.2f}€',
        'balance_request_sent': '💳 Your balance top-up request sent to administrator.',
        'balance_topped_up': 'Your balance has been topped up by {0}€\nNew balance: {1:.2f}€',

        # Заказы
        'new_order': '🚖 <b>NEW ORDER! #{}</b>\n\n👤 Client: {}\n📱 Username: {}\n{}\n📍 <b>From:</b> {}\n🎯 <b>To:</b> {}\n📏 Distance: {:.1f} km\n⏱ Time: {:.0f} min\n💰 <b>Price:</b> {}€\n\n',
        'accept_order': '✅ Accept order',
        'order_accepted': '✅ <b>ORDER #{} ACCEPTED</b>\n\n🚗 Driver: {}\n📱 Username: @{}\n{}\n\n👤 Client: {}\n📍 <b>From:</b> {}\n🎯 <b>To:</b> {}\n📏 Distance: {:.1f} km\n⏱ Time: {:.0f} min\n💰 <b>Price:</b> {}€',
        'order_taken_by_driver': '🚗 <b>Your order accepted!</b>\n\nDriver: {}\nUsername: @{}\n{}\nContact: <a href=\'tg://user?id={}\'>Message driver</a>\n\nDriver will contact you soon!',
        'complete_order': '✅ Complete order',
        'order_completed': '✅ <b>Order #{} completed!</b>\n\nRate the trip with driver {}:',
        'rate_trip': '✅ <b>Order #{} completed!</b>\n\nYour rating: {}\nThank you for using RigaGo!',
        'rate_client': '✅ <b>Order #{} completed!</b>\n\nRate the client {}:',
        'client_rated': 'Thank you for rating the client! {}',

        # Ошибки
        'not_driver': 'You are not registered as a driver.',
        'order_not_found': '❌ Order not found or already deleted',
        'order_already_taken': '❌ Order already taken by another driver',
        'not_registered': '❌ You are not registered as a driver',
        'driver_banned': '❌ You are banned until {} due to low rating',
        'low_balance': '❌ Insufficient balance. Minimum 0.50€ required to accept order',
        'active_order_exists': '❌ You already have an active order. Complete it before accepting a new one.',

        # Админ
        'admin_panel': '🛠 <b>Admin panel</b>\n\nSelect section:',
        'drivers': '👥 Drivers',
        'orders': '📋 Orders',
        'no_access': '❌ You do not have access to admin panel.',

        # Дополнительные сообщения
        'already_rated': 'You have already rated this order',
        'thanks_for_rating': 'Thank you for rating! {}',
        'order_completed_driver': '✅ Order completed!',
        'order_payment_info': '✅ <b>Order #{} completed!</b>\n\n💰 Payment: {:.2f}€ (receive cash from client)\n💳 Commission: 0.50€ (deducted from balance)\n\nThank you for your work!',
        'new_rating_received': '📊 <b>New rating: {}</b>\n\nYour current rating: {}',
        'rating_ban_warning': '📊 <b>New rating: {}</b>\n\nYour current rating: {}\n\n⚠️ <b>WARNING!</b> Your rating dropped below 4.1. You are banned for a week until {}.\nTo unblock, improve service quality.',
        'minimum_price_error': 'Minimum order price {}€.',
        'enter_valid_price': 'Please enter a valid price (number).',
        'active_order_client': '❌ You already have an active order. Wait for its completion or cancellation before creating a new one.'
    }
}

# === СОСТОЯНИЯ FSM ===
class LanguageSelection(StatesGroup):
    waiting_for_language = State()

class OrderTaxi(StatesGroup):
    waiting_for_location = State()
    waiting_for_address = State()
    waiting_for_destination = State()
    waiting_for_confirmation = State()
    waiting_for_suggested_price = State()

class DriverRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_car_number = State()
    waiting_for_car_model = State()
    waiting_for_confirmation = State()

class AdminOperations(StatesGroup):
    waiting_for_balance_amount = State()

# === БАЗА ДАННЫХ ===
class Database:
    def __init__(self, db_name='driver_bot.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.lock = threading.Lock()
        self._init_tables()

    def _init_tables(self):
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT, 
                car_number TEXT, 
                car_model TEXT,
                balance REAL DEFAULT 0, 
                registered INTEGER DEFAULT 0,
                is_driver INTEGER DEFAULT 0,
                language TEXT DEFAULT 'ru',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_orders INTEGER DEFAULT 0
            )""")
            # Добавляем колонки если их нет
            try:
                c.execute("ALTER TABLE users ADD COLUMN is_driver INTEGER DEFAULT 0")
            except:
                pass
            try:
                c.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ru'")
            except:
                pass
            try:
                c.execute("ALTER TABLE users ADD COLUMN ban_until TIMESTAMP")
            except:
                pass
            try:
                c.execute("ALTER TABLE users ADD COLUMN total_orders INTEGER DEFAULT 0")
            except:
                pass

            c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER, 
                address TEXT, 
                region TEXT, 
                price REAL,
                status TEXT DEFAULT 'new', 
                driver_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )""")
            c.execute("""
            CREATE TABLE IF NOT EXISTS balance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                operation_type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            c.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                driver_id INTEGER,
                client_id INTEGER,
                rating INTEGER,
                rating_type TEXT DEFAULT 'driver',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            # Добавляем колонку rating_type если её нет
            try:
                c.execute("ALTER TABLE ratings ADD COLUMN rating_type TEXT DEFAULT 'driver'")
            except:
                pass

            self.conn.commit()

    def get_user(self, user_id):
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return c.fetchone()

    def set_user_language(self, user_id, language):
        with self.lock:
            c = self.conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, language) VALUES (?, ?)", (user_id, language))
            c.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            self.conn.commit()

    def get_user_language(self, user_id):
        user = self.get_user(user_id)
        if user and len(user) > 7 and user[7]:
            return user[7]
        return 'ru'  # по умолчанию русский

    def register_driver(self, user_id, name, car_number, car_model):
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, name, car_number, car_model, is_driver, registered) 
                VALUES (?, ?, ?, ?, 1, 1)
            """, (user_id, name, car_number, car_model))
            self.conn.commit()

    def update_user_balance(self, user_id, amount, operation_type, description):
        with self.lock:
            c = self.conn.cursor()
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            c.execute("""
                INSERT INTO balance_history (user_id, amount, operation_type, description) 
                VALUES (?, ?, ?, ?)
            """, (user_id, amount, operation_type, description))
            self.conn.commit()

    def create_order(self, client_id, address, price, region):
        with self.lock:
            c = self.conn.cursor()
            c.execute("INSERT INTO orders (client_id, address, price, region, status) VALUES (?, ?, ?, ?, 'new')",
                      (client_id, address, price, region))
            self.conn.commit()
            return c.lastrowid

    def accept_order(self, driver_id, order_id):
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM orders WHERE id = ? AND status = 'new'", (order_id,))
            order = c.fetchone()
            if order:
                c.execute("UPDATE orders SET status = 'accepted', driver_id = ? WHERE id = ?", (driver_id, order_id))
                c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (order[4], driver_id))
                self.conn.commit()
                return order
            return None

    def complete_order(self, order_id):
        with self.lock:
            c = self.conn.cursor()
            c.execute("UPDATE orders SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?", (order_id,))
            self.conn.commit()

    def get_driver_stats(self, driver_id):
        with self.lock:
            c = self.conn.cursor()
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            week_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d')
            month_ago = (now - timedelta(days=30)).strftime('%Y-%m-%d')

            # Заказы за день
            c.execute("""
                SELECT COUNT(*), COALESCE(SUM(price), 0) FROM orders 
                WHERE driver_id = ? AND status = 'completed' AND DATE(completed_at) = ?
            """, (driver_id, today))
            day_stats = c.fetchone()

            # Заказы за неделю
            c.execute("""
                SELECT COUNT(*), COALESCE(SUM(price), 0) FROM orders 
                WHERE driver_id = ? AND status = 'completed' AND DATE(completed_at) >= ?
            """, (driver_id, week_ago))
            week_stats = c.fetchone()

            # Заказы за месяц
            c.execute("""
                SELECT COUNT(*), COALESCE(SUM(price), 0) FROM orders 
                WHERE driver_id = ? AND status = 'completed' AND DATE(completed_at) >= ?
            """, (driver_id, month_ago))
            month_stats = c.fetchone()

            return {
                'day': {'orders': day_stats[0], 'earnings': day_stats[1]},
                'week': {'orders': week_stats[0], 'earnings': week_stats[1]},
                'month': {'orders': month_stats[0], 'earnings': month_stats[1]}
            }

    def get_all_drivers(self):
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT user_id, name, balance FROM users WHERE is_driver = 1 ORDER BY name")
            return c.fetchall()

    def get_recent_orders(self, limit=10):
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                SELECT o.id, o.client_id, o.address, o.region, o.price, o.status, 
                       o.driver_id, o.created_at, u1.name as client_name, u2.name as driver_name
                FROM orders o
                LEFT JOIN users u1 ON o.client_id = u1.user_id
                LEFT JOIN users u2 ON o.driver_id = u2.user_id
                ORDER BY o.created_at DESC
                LIMIT ?
            """, (limit,))
            return c.fetchall()

    def add_rating(self, order_id, driver_id, client_id, rating, rating_type='driver'):
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                INSERT INTO ratings (order_id, driver_id, client_id, rating, rating_type) 
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, driver_id, client_id, rating, rating_type))
            self.conn.commit()

    def get_driver_rating(self, driver_id):
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                SELECT AVG(CAST(rating AS FLOAT)), COUNT(*) FROM ratings 
                WHERE driver_id = ? AND rating_type = 'driver'
            """, (driver_id,))
            result = c.fetchone()
            if result and result[1] > 0:
                return round(result[0], 1), result[1]
            return None, 0

    def get_client_rating(self, client_id):
        with self.lock:
            c = self.conn.cursor()
            c.execute("""
                SELECT AVG(CAST(rating AS FLOAT)), COUNT(*) FROM ratings 
                WHERE client_id = ? AND rating_type = 'client'
            """, (client_id,))
            result = c.fetchone()
            if result and result[1] > 0:
                return round(result[0], 1), result[1]
            return None, 0

    def check_and_ban_driver(self, driver_id):
        rating, count = self.get_driver_rating(driver_id)
        if rating and count >= 5 and rating < 4.1:
            # Проверяем, не заблокирован ли уже водитель
            is_banned, existing_ban = self.is_driver_banned(driver_id)
            if not is_banned:
                ban_until = datetime.now() + timedelta(days=7)
                with self.lock:
                    c = self.conn.cursor()
                    c.execute("UPDATE users SET ban_until = ? WHERE user_id = ?", 
                             (ban_until.strftime('%Y-%m-%d %H:%M:%S'), driver_id))
                    self.conn.commit()
                return True, ban_until
        return False, None

    def is_driver_banned(self, driver_id):
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT ban_until FROM users WHERE user_id = ?", (driver_id,))
            result = c.fetchone()
            if result and result[0]:
                ban_until = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
                if datetime.now() < ban_until:
                    return True, ban_until
                else:
                    # Снимаем бан если время истекло
                    c.execute("UPDATE users SET ban_until = NULL WHERE user_id = ?", (driver_id,))
                    self.conn.commit()
            return False, None

    def get_client_order_count(self, client_id):
        """Получить количество заказов клиента"""
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT COUNT(*) FROM orders WHERE client_id = ?", (client_id,))
            return c.fetchone()[0]

    def increment_client_orders(self, client_id):
        """Увеличить счетчик заказов клиента"""
        with self.lock:
            c = self.conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, total_orders) VALUES (?, 0)", (client_id,))
            c.execute("UPDATE users SET total_orders = total_orders + 1 WHERE user_id = ?", (client_id,))
            self.conn.commit()

# === УТИЛИТЫ ===
def get_text(user_id, key, *args):
    """Получить переведенный текст для пользователя"""
    language = db.get_user_language(user_id)
    if language not in TRANSLATIONS:
        language = 'ru'

    text = TRANSLATIONS[language].get(key, TRANSLATIONS['ru'].get(key, key))
    if args:
        try:
            return text.format(*args)
        except:
            return text
    return text

async def get_route_info(from_lat, from_lon, to_lat, to_lon):
    """Получение информации о маршруте через OpenRouteService"""
    url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Content-Type': 'application/json; charset=utf-8'
    }

    coordinates = [[from_lon, from_lat], [to_lon, to_lat]]

    data = {
        "coordinates": coordinates,
        "format": "json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if 'routes' in result and len(result['routes']) > 0:
                        route = result['routes'][0]['summary']
                        distance_km = route['distance'] / 1000
                        duration_min = route['duration'] / 60
                        return distance_km, duration_min
    except Exception as e:
        print(f"Ошибка при получении маршрута: {e}")

    # Если API недоступен, используем примерный расчет по прямой линии
    R = 6371  # Радиус Земли в км
    lat1, lon1 = math.radians(from_lat), math.radians(from_lon)
    lat2, lon2 = math.radians(to_lat), math.radians(to_lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance_km = R * c

    # Примерная скорость 40 км/ч в городе
    duration_min = (distance_km / 40) * 60

    return distance_km, duration_min

async def get_address(lat, lon):
    """Получение адреса по координатам через OpenStreetMap"""
    url = f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={'User-Agent': 'RigaGo_Bot'}) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('display_name', 'Адрес не найден')
            return 'Адрес не найден'

async def geocode_address(address):
    """Получение координат по текстовому адресу"""
    url = f'https://nominatim.openstreetmap.org/search?format=json&q={address}&limit=1'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={'User-Agent': 'RigaGo_Bot'}) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data:
                    return float(data[0]['lat']), float(data[0]['lon'])
            return None, None

def calculate_price(distance_km, duration_minutes=None):
    """Расчет стоимости поездки"""
    min_price = 2.50
    per_km = 0.45
    per_minute = 0.10

    distance_cost = per_km * distance_km

    time_cost = 0
    if duration_minutes:
        time_cost = per_minute * duration_minutes

    total_cost = distance_cost + time_cost
    final_price = max(min_price, total_cost)

    return round(final_price, 2)

async def delete_order_after_delay(order_id, delay_seconds):
    """Удаление заказа через заданное время"""
    await asyncio.sleep(delay_seconds)

    if order_id in active_orders:
        order = active_orders[order_id]
        try:
            # Удаляем сообщение из группы
            await router.bot.delete_message(
                chat_id=DRIVER_GROUP_ID,
                message_id=order['message_id']
            )
            print(f"Сообщение заказа {order_id} удалено из группы")
        except Exception as e:
            print(f"Ошибка удаления сообщения заказа {order_id}: {e}")

        # Удаляем из активных заказов
        del active_orders[order_id]
        print(f"Заказ {order_id} автоматически удален через {delay_seconds} секунд")

async def cleanup_old_orders():
    """Очистка старых заказов при запуске бота"""
    current_time = datetime.now()
    orders_to_remove = []
    
    for order_id, order in active_orders.items():
        # Проверяем возраст заказа
        order_age = current_time - order['created_at']
        
        # Удаляем заказы старше 1 часа для новых или старше 5 минут для принятых
        should_remove = False
        if order['status'] == 'active' and order_age.total_seconds() > 3600:  # 1 час
            should_remove = True
        elif order['status'] == 'accepted' and order_age.total_seconds() > 300:  # 5 минут
            should_remove = True
            
        if should_remove:
            orders_to_remove.append(order_id)
    
    # Удаляем старые заказы
    for order_id in orders_to_remove:
        order = active_orders[order_id]
        try:
            await router.bot.delete_message(
                chat_id=DRIVER_GROUP_ID,
                message_id=order['message_id']
            )
            print(f"Удалено старое сообщение заказа {order_id} из группы")
        except Exception as e:
            print(f"Ошибка удаления старого сообщения заказа {order_id}: {e}")
        
        del active_orders[order_id]
        print(f"Старый заказ {order_id} удален при запуске бота")

async def periodic_cleanup():
    """Периодическая очистка заказов каждые 10 минут"""
    while True:
        await asyncio.sleep(600)  # 10 минут
        await cleanup_old_orders()

# === РОУТЕР И ОБРАБОТЧИКИ ===
router = Router()

# Словарь для хранения активных заказов
active_orders = {}
order_counter = 0

@router.message(F.text == '/admin')
async def admin_command(message: Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.answer(get_text(user_id, 'no_access'))
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'drivers')), KeyboardButton(text=get_text(user_id, 'orders'))],
            [KeyboardButton(text=get_text(user_id, 'back'))]
        ],
        resize_keyboard=True
    )
    await message.answer(get_text(user_id, 'admin_panel'), parse_mode="HTML", reply_markup=keyboard)

@router.message(F.text == '/start')
async def start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = db.get_user(user_id)

    # Если пользователь новый или не выбрал язык
    if not user or not user[7]:  # language field
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="🇱🇻 Latviešu", callback_data="lang_lv")
            ],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
        ])

        await message.answer(
            "🌍 Выберите язык / Izvēlieties valodu / Choose language:",
            reply_markup=keyboard
        )
        await state.set_state(LanguageSelection.waiting_for_language)
    else:
        # Показываем главное меню на выбранном языке
        await show_main_menu(message, user_id)

@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery, state: FSMContext):
    language = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Сохраняем выбранный язык
    db.set_user_language(user_id, language)
    await state.clear()

    await callback.answer()
    await callback.message.delete()

    # Показываем главное меню на выбранном языке
    await show_main_menu_from_callback(callback, user_id)

async def show_main_menu(message: Message, user_id: int):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'order_taxi'))]
        ],
        resize_keyboard=True
    )
    await message.answer(get_text(user_id, 'welcome'), reply_markup=keyboard)

async def show_main_menu_from_callback(callback: CallbackQuery, user_id: int):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'order_taxi'))]
        ],
        resize_keyboard=True
    )
    await callback.message.answer(get_text(user_id, 'welcome'), reply_markup=keyboard)

@router.message(F.text == '/driver')
async def driver_menu(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user or not user[6]:  # is_driver
        # Пользователь не зарегистрирован как водитель
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=get_text(user_id, 'fill_driver_form'))],
                [KeyboardButton(text=get_text(user_id, 'back'))]
            ],
            resize_keyboard=True
        )
        await message.answer(get_text(user_id, 'not_registered_driver'), reply_markup=keyboard)
    else:
        # Показать меню водителя
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=get_text(user_id, 'balance')), KeyboardButton(text=get_text(user_id, 'my_profile'))],
                [KeyboardButton(text=get_text(user_id, 'order_stats')), KeyboardButton(text=get_text(user_id, 'request_balance'))],
                [KeyboardButton(text=get_text(user_id, 'back'))]
            ],
            resize_keyboard=True
        )
        await message.answer(get_text(user_id, 'driver_menu', user[1]), reply_markup=keyboard)

# Обработчик локации
@router.message(F.location)
async def handle_location(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == OrderTaxi.waiting_for_location:
        await process_location(message, state)
    elif current_state == OrderTaxi.waiting_for_address:
        # Обрабатываем локацию как начальный адрес при ручном вводе
        await process_location(message, state)
    elif current_state == OrderTaxi.waiting_for_destination:
        await process_destination_location(message, state)

@router.message(F.text)
async def handle_text_messages(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    current_state = await state.get_state()

    # Получаем переводы для текущего пользователя
    fill_driver_form = get_text(user_id, 'fill_driver_form')
    order_taxi = get_text(user_id, 'order_taxi')
    back = get_text(user_id, 'back')
    balance = get_text(user_id, 'balance')
    my_profile = get_text(user_id, 'my_profile')
    order_stats = get_text(user_id, 'order_stats')
    request_balance = get_text(user_id, 'request_balance')
    save_profile = get_text(user_id, 'save_profile')
    cancel = get_text(user_id, 'cancel')
    send_location_btn = get_text(user_id, 'send_location_btn')
    enter_address_manually = get_text(user_id, 'enter_address_manually')
    enter_destination = get_text(user_id, 'enter_destination')
    confirm_order = get_text(user_id, 'confirm_order')
    drivers = get_text(user_id, 'drivers')
    orders = get_text(user_id, 'orders')
    suggest_price = get_text(user_id, 'suggest_price')

    # Обработка отмены для любого состояния (в первую очередь)
    if text == cancel and current_state is not None:
        await cancel_order(message, state)
        return

    # Обработка состояний FSM
    if current_state == DriverRegistration.waiting_for_name:
        await process_driver_name(message, state)
        return
    elif current_state == DriverRegistration.waiting_for_car_number:
        await process_car_number(message, state)
        return
    elif current_state == DriverRegistration.waiting_for_car_model:
        await process_car_model(message, state)
        return
    elif current_state == DriverRegistration.waiting_for_confirmation:
        if text == save_profile:
            await save_driver_profile(message, state)
        return
    elif current_state == OrderTaxi.waiting_for_location:
        if text == enter_address_manually:
            await input_address_manually(message, state)
        return
    elif current_state == OrderTaxi.waiting_for_address:
        await process_address_text(message, state)
        return
    elif current_state == OrderTaxi.waiting_for_destination:
        if text == enter_destination:
            await input_destination_manually(message, state)
        else:
            await process_destination_text(message, state)
        return
    elif current_state == OrderTaxi.waiting_for_confirmation:
        if text == confirm_order:
            await confirm_order_handler(message, state)
        elif text == suggest_price:
            await suggest_price_handler(message, state)
        return
    elif current_state == OrderTaxi.waiting_for_suggested_price:
        await process_suggested_price(message, state)
        return
    elif current_state == AdminOperations.waiting_for_balance_amount:
        await process_balance_amount(message, state)
        return

    # Обычные команды (только если нет активного состояния FSM)
    if current_state is None:
        if text == fill_driver_form:
            await start_driver_registration(message, state)
        elif text == order_taxi:
            await order_taxi_handler(message, state)
        elif text == back:
            await back_to_main(message, state)
        elif text == balance:
            await show_balance(message)
        elif text == my_profile:
            await show_profile(message)
        elif text == order_stats:
            await show_order_stats(message)
        elif text == request_balance:
            await request_balance_handler(message)
        elif text == drivers and message.from_user.id == ADMIN_ID:
            await admin_drivers_list(message)
        elif text == orders and message.from_user.id == ADMIN_ID:
            await admin_orders_list(message)

async def start_driver_registration(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = db.get_user(user_id)

    if user and user[5]:  # registered
        await message.answer(get_text(user_id, 'already_registered'))
        return

    await message.answer(get_text(user_id, 'enter_name'))
    await state.set_state(DriverRegistration.waiting_for_name)

async def process_driver_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(name=message.text)
    await message.answer(get_text(user_id, 'enter_car_number'))
    await state.set_state(DriverRegistration.waiting_for_car_number)

async def process_car_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(car_number=message.text)
    await message.answer(get_text(user_id, 'enter_car_model'))
    await state.set_state(DriverRegistration.waiting_for_car_model)

async def process_car_model(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    await state.update_data(car_model=message.text)

    # Показываем информацию и кнопку сохранения
    profile_text = get_text(user_id, 'check_data', data['name'], data['car_number'], message.text)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'save_profile'))],
            [KeyboardButton(text=get_text(user_id, 'cancel'))]
        ],
        resize_keyboard=True
    )

    await message.answer(profile_text, parse_mode="HTML", reply_markup=keyboard)
    await state.set_state(DriverRegistration.waiting_for_confirmation)

async def save_driver_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    # Проверяем что все данные есть
    if not all(key in data for key in ['name', 'car_number', 'car_model']):
        await message.answer("❌ Ошибка! Данные анкеты неполные. Начните заново.")
        await state.clear()
        return

    # Сохраняем в базу данных
    db.register_driver(user_id, data['name'], data['car_number'], data['car_model'])

    # Удаляем сообщения регистрации для очистки чата
    try:
        # Удаляем последние 10 сообщений (включая сообщения бота и пользователя)
        for i in range(10):
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id - i
                )
            except:
                continue  # Игнорируем ошибки удаления (сообщение уже удалено или старое)
    except:
        pass  # Игнорируем ошибки удаления

    await state.clear()

    # Показываем меню водителя сразу после сохранения
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'balance')), KeyboardButton(text=get_text(user_id, 'my_profile'))],
            [KeyboardButton(text=get_text(user_id, 'order_stats')), KeyboardButton(text=get_text(user_id, 'request_balance'))],
            [KeyboardButton(text=get_text(user_id, 'back'))]
        ],
        resize_keyboard=True
    )

    await message.answer(
        get_text(user_id, 'profile_saved', data['name']),
        parse_mode="HTML",
        reply_markup=keyboard
    )

    # Уведомление админу
    try:
        await message.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆕 <b>Новый водитель зарегистрировался:</b>\n\n"
                 f"👤 Имя: {data['name']}\n"
                 f"🚗 Номер авто: {data['car_number']}\n"
                 f"🏷 Марка: {data['car_model']}\n"
                 f"🆔 ID: {user_id}\n"
                 f"👤 Username: @{message.from_user.username or 'не указан'}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")

async def show_balance(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user or not user[6]:
        await message.answer(get_text(user_id, 'not_driver'))
        return

    await message.answer(get_text(user_id, 'current_balance', user[4]))

async def show_profile(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user or not user[6]:
        await message.answer(get_text(user_id, 'not_driver'))
        return

    rating, rating_count = db.get_driver_rating(user_id)
    rating_text = get_text(user_id, 'rating_info', rating, rating_count) if rating else get_text(user_id, 'no_rating')

    profile_text = get_text(user_id, 'profile_info', user[1], user[2], user[3], user[4], rating_text)

    await message.answer(profile_text, parse_mode="HTML")

async def show_order_stats(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user or not user[6]:
        await message.answer(get_text(user_id, 'not_driver'))
        return

    stats = db.get_driver_stats(user_id)

    stats_text = get_text(user_id, 'stats_info',
                         stats['day']['orders'], stats['day']['earnings'],
                         stats['week']['orders'], stats['week']['earnings'],
                         stats['month']['orders'], stats['month']['earnings'])

    await message.answer(stats_text, parse_mode="HTML")

async def request_balance_handler(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user or not user[6]:
        await message.answer(get_text(user_id, 'not_driver'))
        return

    await message.answer(get_text(user_id, 'balance_request_sent'))

    # Отправка запроса админу
    try:
        # Проверяем, первый ли это запрос баланса (баланс = 0)
        keyboard_buttons = [
            [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data=f"add_balance_{user_id}")]
        ]
        
        # Если баланс 0, добавляем кнопку для добавления в группу
        if user[4] == 0:
            keyboard_buttons.append([InlineKeyboardButton(text="👥 Добавить в группу", callback_data=f"add_to_group_{user_id}")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await router.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💳 <b>Запрос на пополнение баланса</b>\n\n"
                 f"👤 Водитель: {user[1]}\n"
                 f"🚗 Авто: {user[2]} ({user[3]})\n"
                 f"💰 Текущий баланс: {user[4]:.2f}€\n"
                 f"ID: {user_id}"
                 f"{' (🆕 Новый водитель)' if user[4] == 0 else ''}",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except:
        await message.answer("Ошибка отправки запроса. Попробуйте позже.")

async def back_to_main(message: Message, state: FSMContext = None):
    user_id = message.from_user.id
    if state:
        await state.clear()
    await show_main_menu(message, user_id)

# === АДМИНСКИЕ КОМАНДЫ ===

async def admin_drivers_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return

    drivers = db.get_all_drivers()

    if not drivers:
        await message.answer("👥 Водители не найдены.")
        return

    keyboard_buttons = []
    for driver in drivers:
        user_id, name, balance = driver
        button_text = f"👤 {name} (💰 {balance:.2f}€)"
        keyboard_buttons.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"driver_info_{user_id}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer("👥 <b>Список водителей:</b>\n\nВыберите водителя для управления:", parse_mode="HTML", reply_markup=keyboard)

@router.callback_query(F.data.startswith("driver_info_"))
async def show_driver_info(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа")
        return

    user_id = int(callback.data.split("_")[2])
    user = db.get_user(user_id)

    if not user:
        await callback.answer("❌ Водитель не найден")
        return

    stats = db.get_driver_stats(user_id)
    rating, rating_count = db.get_driver_rating(user_id)
    rating_text = f"⭐ {rating}/5.0 ({rating_count} оценок)" if rating else "⭐ нет оценок"

    is_banned, ban_until = db.is_driver_banned(user_id)
    ban_text = f"\n⚠️ <b>ЗАБЛОКИРОВАН до {ban_until.strftime('%d.%m.%Y %H:%M')}</b>" if is_banned else ""

    driver_info = (
        f"👤 <b>Информация о водителе:</b>\n\n"
        f"Имя: {user[1]}\n"
        f"🚗 Номер авто: {user[2]}\n"
        f"🏷 Марка: {user[3]}\n"
        f"💰 Баланс: {user[4]:.2f}€\n"
        f"{rating_text}{ban_text}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"За день: {stats['day']['orders']} заказов, {stats['day']['earnings']:.2f}€\n"
        f"За неделю: {stats['week']['orders']} заказов, {stats['week']['earnings']:.2f}€\n"
        f"За месяц: {stats['month']['orders']} заказов, {stats['month']['earnings']:.2f}€"
    )

    keyboard_buttons = [
        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data=f"add_balance_{user_id}")],
        [InlineKeyboardButton(text="🗑 Сбросить анкету", callback_data=f"reset_driver_{user_id}")],
    ]

    if is_banned:
        keyboard_buttons.insert(1, [InlineKeyboardButton(text="🔓 Разблокировать", callback_data=f"unban_driver_{user_id}")])

    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_drivers")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(driver_info, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "back_to_drivers")
async def back_to_drivers_list(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа")
        return

    drivers = db.get_all_drivers()

    if not drivers:
        await callback.message.edit_text("👥 Водители не найдены.")
        return

    keyboard_buttons = []
    for driver in drivers:
        user_id, name, balance = driver
        button_text = f"👤 {name} (💰 {balance:.2f}€)"
        keyboard_buttons.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"driver_info_{user_id}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text("👥 <b>Список водителей:</b>\n\nВыберите водителя для управления:", parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("unban_driver_"))
async def unban_driver_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа")
        return

    user_id = int(callback.data.split("_")[2])
    user = db.get_user(user_id)

    if not user:
        await callback.answer("❌ Водитель не найден")
        return

    with db.lock:
        c = db.conn.cursor()
        c.execute("UPDATE users SET ban_until = NULL WHERE user_id = ?", (user_id,))
        db.conn.commit()

    await callback.answer(f"✅ Водитель {user[1]} разблокирован", show_alert=True)

    # Уведомление водителю
    try:
        user_lang = db.get_user_language(user_id)
        await router.bot.send_message(
            chat_id=user_id,
            text="✅ Вы разблокированы администратором. Можете снова принимать заказы."
        )
    except:
        pass

    # Обновляем информацию о водителе
    await show_driver_info(callback)

@router.callback_query(F.data.startswith("reset_driver_"))
async def reset_driver_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа")
        return

    user_id = int(callback.data.split("_")[2])
    user = db.get_user(user_id)

    if not user:
        await callback.answer("❌ Водитель не найден")
        return

    with db.lock:
        c = db.conn.cursor()
        c.execute("UPDATE users SET registered = 0, is_driver = 0 WHERE user_id = ?", (user_id,))
        db.conn.commit()

    await callback.answer(f"✅ Анкета водителя {user[1]} сброшена", show_alert=True)

    # Уведомление водителю
    try:
        await router.bot.send_message(
            chat_id=user_id,
            text="⚠️ Ваша анкета водителя была сброшена администратором.\n"
                 "Для продолжения работы заполните анкету заново."
        )
    except:
        pass

    # Обновляем список водителей
    await back_to_drivers_list(callback)

async def admin_orders_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return

    with db.lock:
        c = db.conn.cursor()
        c.execute("""
            SELECT o.id, o.client_id, o.address, o.region, o.price, o.status, 
                   o.driver_id, o.created_at, u1.name as client_name, u2.name as driver_name,
                   COALESCE(u1.total_orders, 0) as client_orders
            FROM orders o
            LEFT JOIN users u1 ON o.client_id = u1.user_id
            LEFT JOIN users u2 ON o.driver_id = u2.user_id
            ORDER BY o.created_at DESC
            LIMIT 10
        """)
        orders = c.fetchall()

    if not orders:
        await message.answer("📋 Заказы не найдены.")
        return

    orders_text = "📋 <b>Последние заказы:</b>\n\n"

    for order in orders:
        order_id, client_id, address, region, price, status, driver_id, created_at, client_name, driver_name, client_orders = order

        status_emoji = {
            'new': '🆕',
            'accepted': '✅',
            'completed': '✅'
        }.get(status, '❓')

        # Add 💰 emoji if the order has a suggested price
        if status == 'new' and price != calculate_price(order[4]):
            status_emoji = '💰' + status_emoji

        # Получаем рейтинг клиента для админки
        client_rating, client_rating_count = db.get_client_rating(client_id)
        client_warning = ""
        if client_rating and client_rating < 3.0:
            client_warning = " ⚠️ ВНИМАНИЕ ГАНДОН!"

        orders_text += f"{status_emoji} <b>Заказ #{order_id}</b>\n"
        orders_text += f"👤 Клиент: {client_name or 'Неизвестен'}{client_warning}\n"
        orders_text += f"📊 Заказов клиента: {client_orders}\n"
        if client_rating:
            orders_text += f"⭐ Рейтинг клиента: {client_rating}/5.0\n"
        orders_text += f"📍 Адрес: {address}\n"
        orders_text += f"💰 Цена: {price}€\n"

        if driver_name:
            orders_text += f"🚗 Водитель: {driver_name}\n"
        else:
            orders_text += f"🚗 Водитель: не назначен\n"

        orders_text += f"📅 Дата: {created_at}\n"
        orders_text += f"📊 Статус: {status}\n\n"

    await message.answer(orders_text, parse_mode="HTML")

@router.message(F.text.regexp(r'/balance_(\d+)'))
async def admin_add_balance_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    user_id = int(message.text.split('_')[1])
    user = db.get_user(user_id)

    if not user:
        await message.answer("❌ Пользователь не найден.")
        return

    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminOperations.waiting_for_balance_amount)
    await message.answer(f"💰 Введите сумму для пополнения баланса водителя {user[1]}:")

@router.message(AdminOperations.waiting_for_balance_amount)
async def process_balance_amount(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        amount = float(message.text)
        data = await state.get_data()
        user_id = data['target_user_id']

        user = db.get_user(user_id)
        if not user:
            await message.answer("❌ Пользователь не найден.")
            await state.clear()
            return

        db.update_user_balance(user_id, amount, "admin_add", f"Пополнение админом на {amount}€")

        await message.answer(f"✅ Баланс водителя {user[1]} пополнен на {amount}€")

        # Получаем актуальный баланс после пополнения
        updated_user = db.get_user(user_id)
        new_balance = updated_user[4] if updated_user else user[4] + amount

        # Уведомление водителю на его языке
        try:
            await router.bot.send_message(
                chat_id=user_id,
                text=f"💰 {get_text(user_id, 'balance_topped_up', amount, new_balance)}"
            )
        except:
            pass

        await state.clear()

    except ValueError:
        await message.answer("❌ Введите корректную сумму (число).")

@router.message(F.text.regexp(r'/reset_(\d+)'))
async def admin_reset_driver(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    user_id = int(message.text.split('_')[1])
    user = db.get_user(user_id)

    if not user:
        await message.answer("❌ Пользователь не найден.")
        return

    with db.lock:
        c = db.conn.cursor()
        c.execute("UPDATE users SET registered = 0, is_driver = 0 WHERE user_id = ?", (user_id,))
        db.conn.commit()

    await message.answer(f"✅ Анкета водителя {user[1]} сброшена.")

    # Уведомление водителю
    try:
        await router.bot.send_message(
            chat_id=user_id,
            text="⚠️ Ваша анкета водителя была сброшена администратором.\n"
                 "Для продолжения работы заполните анкету заново."
        )
    except:
        pass

@router.callback_query(F.data.startswith("add_balance_"))
async def admin_add_balance_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа")
        return

    user_id = int(callback.data.split("_")[2])
    user = db.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден")
        return

    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminOperations.waiting_for_balance_amount)
    await callback.message.answer(f"💰 Введите сумму для пополнения баланса водителя {user[1]}:")
    await callback.answer()

@router.callback_query(F.data.startswith("add_to_group_"))
async def admin_add_to_group_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа")
        return

    user_id = int(callback.data.split("_")[3])
    user = db.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден")
        return

    try:
        # Генерируем ссылку-приглашение в группу
        chat_info = await router.bot.get_chat(DRIVER_GROUP_ID)
        
        # Создаем ссылку приглашения (если у бота есть права)
        try:
            invite_link = await router.bot.create_chat_invite_link(
                chat_id=DRIVER_GROUP_ID,
                member_limit=1,
                expire_date=None
            )
            invite_url = invite_link.invite_link
        except:
            # Если не получается создать персональную ссылку, используем стандартную
            invite_url = f"https://t.me/{chat_info.username}" if chat_info.username else "Группа водителей"

        # Отправляем водителю ссылку на группу
        await router.bot.send_message(
            chat_id=user_id,
            text=f"🎉 <b>Добро пожаловать в команду!</b>\n\n"
                 f"Администратор добавил вас в группу водителей.\n"
                 f"Присоединяйтесь по ссылке: {invite_url}\n\n"
                 f"В группе вы сможете видеть все заказы и общаться с коллегами.",
            parse_mode="HTML"
        )

        await callback.answer("✅ Ссылка на группу отправлена водителю", show_alert=True)

        # Обновляем сообщение админа
        await callback.message.edit_text(
            f"💳 <b>Запрос на пополнение баланса</b>\n\n"
            f"👤 Водитель: {user[1]}\n"
            f"🚗 Авто: {user[2]} ({user[3]})\n"
            f"💰 Текущий баланс: {user[4]:.2f}€\n"
            f"ID: {user_id}\n\n"
            f"✅ Ссылка на группу отправлена",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data=f"add_balance_{user_id}")]
            ])
        )

    except Exception as e:
        print(f"Ошибка при отправке ссылки на группу: {e}")
        await callback.answer("❌ Ошибка при отправке ссылки", show_alert=True)

# === ЗАКАЗ ВОДИТЕЛЯ ===
async def order_taxi_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Проверяем, нет ли активного заказа у клиента
    for order_id, order in active_orders.items():
        if order['client_id'] == user_id and order['status'] in ['active', 'accepted']:
            await message.answer(get_text(user_id, 'active_order_client'))
            return
    
    location_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'send_location_btn'), request_location=True)],
            [KeyboardButton(text=get_text(user_id, 'enter_address_manually'))],
            [KeyboardButton(text=get_text(user_id, 'cancel'))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(get_text(user_id, 'send_location'), reply_markup=location_keyboard)
    await state.set_state(OrderTaxi.waiting_for_location)

async def cancel_order(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    await show_main_menu(message, user_id)
    await message.answer(get_text(user_id, 'order_cancelled'))

async def process_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lat = message.location.latitude
    lon = message.location.longitude

    print(f"Получена геолокация от пользователя {user_id}: {lat}, {lon}")
    address = await get_address(lat, lon)
    print(f"Адрес определен: {address}")

    await state.update_data(
        from_lat=lat,
        from_lon=lon,
        from_address=address
    )

    location_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'enter_destination'))],
            [KeyboardButton(text=get_text(user_id, 'cancel'))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        get_text(user_id, 'your_location', address),
        reply_markup=location_keyboard
    )
    await state.set_state(OrderTaxi.waiting_for_destination)

async def process_address_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text == get_text(user_id, 'cancel'):
        return await cancel_order(message, state)

    from_address = message.text
    
    # Показываем, что бот обрабатывает адрес
    processing_msg = await message.answer("🔍 Обрабатываю адрес...")
    
    from_lat, from_lon = await geocode_address(from_address)
    
    # Удаляем сообщение о процессе
    try:
        await processing_msg.delete()
    except:
        pass

    if from_lat is None or from_lon is None:
        await message.answer(get_text(user_id, 'address_not_found'))
        return

    await state.update_data(
        from_lat=from_lat,
        from_lon=from_lon,
        from_address=from_address
    )

    location_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'enter_destination'))],
            [KeyboardButton(text=get_text(user_id, 'cancel'))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        get_text(user_id, 'your_location', from_address),
        reply_markup=location_keyboard
    )
    await state.set_state(OrderTaxi.waiting_for_destination)

async def process_destination_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    to_lat = message.location.latitude
    to_lon = message.location.longitude

    to_address = await get_address(to_lat, to_lon)

    data = await state.get_data()
    from_lat = data['from_lat']
    from_lon = data['from_lon']
    from_address = data['from_address']

    distance_km, duration_min = await get_route_info(from_lat, from_lon, to_lat, to_lon)

    price = calculate_price(distance_km, duration_min)

    await state.update_data(
        to_lat=to_lat,
        to_lon=to_lon,
        to_address=to_address,
        price=price,
        distance_km=distance_km,
        duration_min=duration_min
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'confirm_order'))],
            [KeyboardButton(text=get_text(user_id, 'suggest_price'))],
            [KeyboardButton(text=get_text(user_id, 'cancel'))]
        ],
        resize_keyboard=True
    )

    await message.answer(
        get_text(user_id, 'order_details', from_address, to_address, distance_km, duration_min, price),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(OrderTaxi.waiting_for_confirmation)

async def input_destination_manually(message: Message, state: FSMContext):
    user_id = message.from_user.id
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text(user_id, 'cancel'))]],
        resize_keyboard=True
    )
    await message.answer(
        get_text(user_id, 'enter_destination_text'),
        reply_markup=keyboard
    )

async def process_destination_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text in [get_text(user_id, 'cancel')]:
        return await cancel_order(message, state)

    to_address = message.text
    data = await state.get_data()
    from_address = data['from_address']
    from_lat = data['from_lat']
    from_lon = data['from_lon']

    # Показываем, что бот обрабатывает адрес и маршрут
    processing_msg = await message.answer("🔍 Обрабатываю адрес и рассчитываю маршрут...")

    to_lat, to_lon = await geocode_address(to_address)

    if to_lat is None or to_lon is None:
        try:
            await processing_msg.delete()
        except:
            pass
        await message.answer(get_text(user_id, 'address_not_found'))
        return

    distance_km, duration_min = await get_route_info(from_lat, from_lon, to_lat, to_lon)
    
    # Удаляем сообщение о процессе
    try:
        await processing_msg.delete()
    except:
        pass

    price = calculate_price(distance_km, duration_min)

    await state.update_data(
        to_lat=to_lat,
        to_lon=to_lon,
        to_address=to_address,
        price=price,
        distance_km=distance_km,
        duration_min=duration_min
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(user_id, 'confirm_order'))],
            [KeyboardButton(text=get_text(user_id, 'suggest_price'))],
            [KeyboardButton(text=get_text(user_id, 'cancel'))]
        ],
        resize_keyboard=True
    )

    await message.answer(
        get_text(user_id, 'order_details', from_address, to_address, distance_km, duration_min, price),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(OrderTaxi.waiting_for_confirmation)

async def confirm_order_handler(message: Message, state: FSMContext):
    global order_counter
    user_id = message.from_user.id

    data = await state.get_data()

    client = message.from_user
    from_address = data['from_address']
    to_address = data['to_address']
    price = data['price']
    distance_km = data['distance_km']
    duration_min = data['duration_min']

    # Проверяем, предложил ли клиент свою цену
    calculated_price = calculate_price(distance_km, duration_min)
    is_suggested_price = abs(price - calculated_price) > 0.01

    waze_url = "https://waze.com/ul"
    if 'from_lat' in data and 'from_lon' in data:
        waze_url = f"https://waze.com/ul?ll={data['from_lat']},{data['from_lon']}&navigate=yes"

    order_counter += 1
    order_id = order_counter

    username_display = "не указан"
    if client.username:
        username = client.username
        if len(username) > 4:
            username_display = f"@{username[:2]}***{username[-2:]}"
        else:
            username_display = f"@{username[0]}***"

    # Увеличиваем счетчик заказов клиента
    db.increment_client_orders(client.id)

    # Получаем рейтинг и количество заказов клиента
    client_rating, client_rating_count = db.get_client_rating(client.id)
    client_orders_count = db.get_client_order_count(client.id)

    client_rating_text = ""
    if client_rating:
        if client_rating < 3.0:
            client_rating_text = f"⚠️ ВНИМАНИЕ ГАНДОН! ⭐ {client_rating}/5.0 ({client_rating_count}) 📊 Заказов: {client_orders_count}\n"
        else:
            client_rating_text = f"⭐ Рейтинг клиента: {client_rating}/5.0 ({client_rating_count}) 📊 Заказов: {client_orders_count}\n"
    else:
        client_rating_text = f"⭐ Рейтинг клиента: новый клиент 📊 Заказов: {client_orders_count}\n"

    # Добавляем эмодзи 💰 для заказов с предложенной ценой
    order_emoji = "💰🚖" if is_suggested_price else "🚖"

    order_text = (
        f"{order_emoji} <b>НОВЫЙ ЗАКАЗ! #{order_id}</b>\n\n"
        f"👤 Клиент: {client.full_name or client.first_name}\n"
        f"📱 Username: {username_display}\n"
        f"{client_rating_text}\n"
        f"📍 <b>Откуда:</b> {from_address}\n"
        f"🎯 <b>Куда:</b> {to_address}\n"
        f"📏 Расстояние: {distance_km:.1f} км\n"
        f"⏱ Время: {duration_min:.0f} мин\n"
        f"💰 <b>Цена:</b> {price}€"
    )

    if is_suggested_price:
        order_text += f" (предложенная клиентом, расчетная: {calculated_price}€)"

    order_text += "\n\n"

    accept_button = InlineKeyboardButton(
        text="✅ Принять заказ",
        callback_data=f"accept_order_{order_id}"
    )
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[accept_button]])

    active_orders[order_id] = {
        'order_id': order_id,
        'client_id': client.id,
        'client_name': client.full_name or client.first_name,
        'client_username': client.username,
        'from_address': from_address,
        'to_address': to_address,
        'price': price,
        'distance_km': distance_km,
        'duration_min': duration_min,
        'waze_url': waze_url,
        'status': 'active',
        'driver_id': None,
        'driver_name': None,
        'driver_username': None,
        'is_suggested_price': is_suggested_price,
        'created_at': datetime.now()
    }

    try:
        print(f"Отправляем заказ #{order_id} в группу {DRIVER_GROUP_ID}")
        message_to_edit = await router.bot.send_message(
            chat_id=DRIVER_GROUP_ID,
            text=order_text,
            parse_mode="HTML",
            disable_web_page_preview=False,
            reply_markup=inline_keyboard
        )

        active_orders[order_id]['message_id'] = message_to_edit.message_id
        print(f"Заказ #{order_id} успешно отправлен, message_id: {message_to_edit.message_id}")

        # Запускаем таймер для удаления неприня́того заказа через час (3600 секунд)
        asyncio.create_task(delete_order_after_delay(order_id, 3600))  # 1 час = 3600 секунд
        print(f"Запущен таймер удаления заказа {order_id} через 1 час")

        await show_main_menu(message, user_id)
        await message.answer(get_text(user_id, 'order_placed'))

    except Exception as e:
        await show_main_menu(message, user_id)
        await message.answer(get_text(user_id, 'order_error'))
        print(f"Ошибка отправки в группу {DRIVER_GROUP_ID}: {e}")
        print(f"Детали заказа: {order_text[:200]}...")

    await state.clear()

async def suggest_price_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await message.answer("Пожалуйста, введите вашу предложенную цену (минимальная цена 3€):")
    await state.set_state(OrderTaxi.waiting_for_suggested_price)

async def process_suggested_price(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if message.text == get_text(user_id, 'cancel'):
        await cancel_order(message, state)
        return

    try:
        suggested_price = float(message.text.replace(',', '.'))  # Поддержка запятой как разделителя
        if suggested_price < 3:
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=get_text(user_id, 'cancel'))]],
                resize_keyboard=True
            )
            await message.answer(
                get_text(user_id, 'minimum_price_error', '3'),
                reply_markup=keyboard
            )
            return

        data = await state.get_data()
        from_address = data['from_address']
        to_address = data['to_address'] 
        distance_km = data['distance_km']
        duration_min = data['duration_min']

        await state.update_data(price=suggested_price)

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=get_text(user_id, 'confirm_order'))],
                [KeyboardButton(text=get_text(user_id, 'cancel'))]
            ],
            resize_keyboard=True
        )

        await message.answer(
            get_text(user_id, 'order_details', from_address, to_address, distance_km, duration_min, suggested_price),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.set_state(OrderTaxi.waiting_for_confirmation)

    except (ValueError, TypeError):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=get_text(user_id, 'cancel'))]],
            resize_keyboard=True
        )
        await message.answer(
            get_text(user_id, 'enter_valid_price'),
            reply_markup=keyboard
        )

@router.callback_query(F.data.startswith("accept_order_"))
async def accept_order_callback(callback: CallbackQuery):
    """Обработчик принятия заказа водителем"""
    order_id = int(callback.data.split("_")[2])
    driver = callback.from_user

    print(f"Водитель {driver.id} пытается принять заказ #{order_id}")
    print(f"Активные заказы: {list(active_orders.keys())}")

    if order_id not in active_orders:
        print(f"Заказ #{order_id} не найден в активных заказах")
        await callback.answer(get_text(driver.id, 'order_not_found'), show_alert=True)
        return

    order = active_orders[order_id]
    if order['status'] != 'active':
        await callback.answer(get_text(driver.id, 'order_already_taken'), show_alert=True)
        return

    # Проверяем, зарегистрирован ли водитель и достаточно ли у него баланса
    driver_data = db.get_user(driver.id)
    if not driver_data or not driver_data[6]:  # is_driver
        await callback.answer(get_text(driver.id, 'not_registered'), show_alert=True)
        return

    # Проверяем бан
    is_banned, ban_until = db.is_driver_banned(driver.id)
    if is_banned:
        await callback.answer(get_text(driver.id, 'driver_banned', ban_until.strftime('%d.%m.%Y %H:%M')), show_alert=True)
        return

    # Дополнительно проверяем текущий рейтинг
    rating, rating_count = db.get_driver_rating(driver.id)
    if rating and rating_count >= 5 and rating < 4.1:
        # Если рейтинг низкий, но водитель еще не заблокирован - блокируем
        ban_until = datetime.now() + timedelta(days=7)
        with db.lock:
            c = db.conn.cursor()
            c.execute("UPDATE users SET ban_until = ? WHERE user_id = ?", 
                     (ban_until.strftime('%Y-%m-%d %H:%M:%S'), driver.id))
            db.conn.commit()

        await callback.answer(get_text(driver.id, 'driver_banned', ban_until.strftime('%d.%m.%Y %H:%M')), show_alert=True)
        return

    if driver_data[4] < 0.50:  # balance
        await callback.answer(get_text(driver.id, 'low_balance'), show_alert=True)
        return

    # Проверяем, нет ли у водителя активных заказов
    for active_order_id, active_order in active_orders.items():
        if active_order['driver_id'] == driver.id and active_order['status'] == 'accepted':
            await callback.answer(get_text(driver.id, 'active_order_exists'), show_alert=True)
            return

    # Списываем 0.50€ с баланса водителя
    db.update_user_balance(driver.id, -0.50, "order_fee", f"Списание за принятие заказа #{order_id}")

    # Создаем заказ в базе данных
    db_order_id = db.create_order(
        client_id=order['client_id'],
        address=f"{order['from_address']} → {order['to_address']}",
        price=order['price'],
        region="Рига"
    )

    # Обновляем заказ в базе - принимаем его
    with db.lock:
        c = db.conn.cursor()
        c.execute("UPDATE orders SET status = 'accepted', driver_id = ? WHERE id = ?", (driver.id, db_order_id))
        db.conn.commit()

    order['status'] = 'accepted'
    order['driver_id'] = driver.id
    order['driver_name'] = driver.full_name or driver.first_name
    order['driver_username'] = driver.username
    order['db_order_id'] = db_order_id

    # Получаем рейтинг водителя
    rating, rating_count = db.get_driver_rating(driver.id)
    rating_text = f"⭐ {rating}/5.0 ({rating_count})" if rating else "⭐ новый водитель"

    accepted_text = (
        f"✅ <b>ЗАКАЗ #{order_id} ПРИНЯТ</b>\n\n"
        f"🚗 Водитель: {driver.full_name or driver.first_name}\n"
        f"📱 Username: @{driver.username or 'не указан'}\n"
        f"{rating_text}\n\n"
        f"👤 Клиент: {order['client_name']}\n"
        f"📍 <b>Откуда:</b> {order['from_address']}\n"
        f"🎯 <b>Куда:</b> {order['to_address']}\n"
        f"📏 Расстояние: {order['distance_km']:.1f} км\n"
        f"⏱ Время: {order['duration_min']:.0f} мин\n"
        f"💰 <b>Цена:</b> {order['price']}€"
    )

    try:
        await router.bot.edit_message_text(
            chat_id=DRIVER_GROUP_ID,
            message_id=order['message_id'],
            text=accepted_text,
            parse_mode="HTML",
            disable_web_page_preview=False,
            reply_markup=None
        )

        new_balance = driver_data[4] - 0.50
        await callback.answer(f"✅ Вы приняли заказ! С баланса списано 0.50€. Остаток: {new_balance:.2f}€", show_alert=True)

        # Уведомление клиенту на его языке
        client_lang = db.get_user_language(order['client_id'])
        client_message = get_text(order['client_id'], 'order_taken_by_driver', 
                                 driver.full_name or driver.first_name, 
                                 driver.username or 'не указан',
                                 rating_text,
                                 driver.id)

        await router.bot.send_message(
            chat_id=order['client_id'],
            text=client_message,
            parse_mode="HTML"
        )

        driver_message = (
            f"📋 <b>Детали заказа #{order_id}</b>\n\n"
            f"👤 Клиент: {order['client_name']}\n"
            f"📱 Username: @{order['client_username'] or 'не указан'}\n"
            f"📞 Контакт: <a href='tg://user?id={order['client_id']}'>Написать клиенту</a>\n\n"
            f"📍 <b>Откуда:</b> {order['from_address']}\n"
            f"🎯 <b>Куда:</b> {order['to_address']}\n"
            f"📏 Расстояние: {order['distance_km']:.1f} км\n"
            f"⏱ Время: {order['duration_min']:.0f} мин\n"
            f"💰 <b>Цена:</b> {order['price']}€\n\n"
            f"🧭 <a href=\"{order['waze_url']}\">Открыть маршрут в Waze</a>\n\n"
            f"Свяжитесь с клиентом для координации!"
        )

        # Добавляем кнопку для завершения заказа в личное сообщение
        complete_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(driver.id, 'complete_order'), callback_data=f"complete_order_{order_id}")]
        ])

        await router.bot.send_message(
            chat_id=driver.id,
            text=driver_message,
            parse_mode="HTML",
            reply_markup=complete_keyboard
        )

        # Запускаем таймер для удаления принятого заказа через 5 минут (300 секунд)
        asyncio.create_task(delete_order_after_delay(order_id, 300))  # 5 минут = 300 секунд
        print(f"Запущен таймер удаления принятого заказа {order_id} через 5 минут")

    except Exception as e:
        print(f"Ошибка при принятии заказа: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("rate_") & ~F.data.startswith("rate_client_"))
async def rate_driver_callback(callback: CallbackQuery):
    """Обработчик оценки водителя"""
    parts = callback.data.split("_")
    order_id = int(parts[1])
    driver_id = int(parts[2])
    rating = int(parts[3])
    client_id = callback.from_user.id

    # Найдем db_order_id для данного внутреннего order_id
    db_order_id = None
    for active_order_id, order in active_orders.items():
        if active_order_id == order_id and 'db_order_id' in order:
            db_order_id = order['db_order_id']
            break
    
    # Если заказ не найден в активных, ищем по водителю и клиенту в последних заказах
    if db_order_id is None:
        with db.lock:
            c = db.conn.cursor()
            c.execute("""
                SELECT id FROM orders 
                WHERE driver_id = ? AND client_id = ? 
                ORDER BY created_at DESC LIMIT 1
            """, (driver_id, client_id))
            result = c.fetchone()
            if result:
                db_order_id = result[0]

    if db_order_id is None:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return

    # Проверяем, не оценивал ли уже клиент этот заказ
    with db.lock:
        c = db.conn.cursor()
        c.execute("SELECT id FROM ratings WHERE order_id = ? AND client_id = ? AND rating_type = 'driver'", (db_order_id, client_id))
        existing_rating = c.fetchone()

    if existing_rating:
        await callback.answer(get_text(client_id, 'already_rated'), show_alert=True)
        return

    # Добавляем оценку
    db.add_rating(db_order_id, driver_id, client_id, rating, 'driver')

    # Проверяем, нужно ли забанить водителя
    is_banned, ban_until = db.check_and_ban_driver(driver_id)

    stars = "⭐" * rating
    await callback.answer(get_text(client_id, 'thanks_for_rating', stars), show_alert=True)

    # Обновляем сообщение на языке клиента
    client_lang = db.get_user_language(client_id)
    await callback.message.edit_text(
        get_text(client_id, 'rate_trip', order_id, stars),
        parse_mode="HTML"
    )

    # Уведомляем водителя об оценке
    driver = db.get_user(driver_id)
    new_rating, total_ratings = db.get_driver_rating(driver_id)
    rating_text = f"⭐ {new_rating}/5.0 ({total_ratings} оценок)" if new_rating else "⭐ новый водитель"

    if is_banned:
        await router.bot.send_message(
            chat_id=driver_id,
            text=get_text(driver_id, 'rating_ban_warning', stars, rating_text, ban_until.strftime('%d.%m.%Y %H:%M')),
            parse_mode="HTML"
        )
    else:
        await router.bot.send_message(
            chat_id=driver_id,
            text=get_text(driver_id, 'new_rating_received', stars, rating_text),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("rate_client_"))
async def rate_client_callback(callback: CallbackQuery):
    """Обработчик оценки клиента водителем"""
    parts = callback.data.split("_")
    order_id = int(parts[2])
    client_id = int(parts[3])
    rating = int(parts[4])
    driver_id = callback.from_user.id

    # Найдем db_order_id для данного внутреннего order_id
    db_order_id = None
    for active_order_id, order in active_orders.items():
        if active_order_id == order_id and 'db_order_id' in order:
            db_order_id = order['db_order_id']
            break
    
    # Если заказ не найден в активных, ищем по водителю и клиенту в последних заказах
    if db_order_id is None:
        with db.lock:
            c = db.conn.cursor()
            c.execute("""
                SELECT id FROM orders 
                WHERE driver_id = ? AND client_id = ? 
                ORDER BY created_at DESC LIMIT 1
            """, (driver_id, client_id))
            result = c.fetchone()
            if result:
                db_order_id = result[0]

    if db_order_id is None:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return

    # Проверяем, не оценивал ли уже водитель этого клиента
    with db.lock:
        c = db.conn.cursor()
        c.execute("SELECT id FROM ratings WHERE order_id = ? AND driver_id = ? AND rating_type = 'client'", (db_order_id, driver_id))
        existing_rating = c.fetchone()

    if existing_rating:
        await callback.answer(get_text(driver_id, 'already_rated'), show_alert=True)
        return

    # Добавляем оценку клиента
    db.add_rating(db_order_id, driver_id, client_id, rating, 'client')

    stars = "⭐" * rating
    await callback.answer(get_text(driver_id, 'client_rated', stars), show_alert=True)

    # Обновляем сообщение
    await callback.message.edit_text(
        get_text(driver_id, 'order_completed_driver'),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("complete_order_"))
async def complete_order_callback(callback: CallbackQuery):
    """Обработчик завершения заказа"""
    order_id = int(callback.data.split("_")[2])
    driver = callback.from_user

    if order_id not in active_orders:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return

    order = active_orders[order_id]

    # Проверяем, что заказ принят этим водителем
    if order['driver_id'] != driver.id:
        await callback.answer("❌ Вы не можете завершить этот заказ", show_alert=True)
        return

    if order['status'] != 'accepted':
        await callback.answer("❌ Заказ уже завершен или отменен", show_alert=True)
        return

    # Завершаем заказ в базе данных
    if 'db_order_id' in order:
        db.complete_order(order['db_order_id'])

    # Обновляем статус заказа
    order['status'] = 'completed'

    try:
        await callback.answer("✅ Заказ завершен!", show_alert=True)

        # Запрос оценки от клиента на его языке
        client_lang = db.get_user_language(order['client_id'])
        rating_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐", callback_data=f"rate_{order_id}_{driver.id}_1"),
                InlineKeyboardButton(text="⭐⭐", callback_data=f"rate_{order_id}_{driver.id}_2"),
                InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rate_{order_id}_{driver.id}_3"),
            ],
            [
                InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rate_{order_id}_{driver.id}_4"),
                InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rate_{order_id}_{driver.id}_5"),
            ]
        ])

        await router.bot.send_message(
            chat_id=order['client_id'],
            text=get_text(order['client_id'], 'order_completed', order_id, driver.full_name or driver.first_name),
            parse_mode="HTML",
            reply_markup=rating_keyboard
        )

        # Запрос оценки клиента от водителя
        client_rating_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐", callback_data=f"rate_client_{order_id}_{order['client_id']}_1"),
                InlineKeyboardButton(text="⭐⭐", callback_data=f"rate_client_{order_id}_{order['client_id']}_2"),
                InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rate_client_{order_id}_{order['client_id']}_3"),
            ],
            [
                InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rate_client_{order_id}_{order['client_id']}_4"),
                InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rate_client_{order_id}_{order['client_id']}_5"),
            ]
        ])

        await router.bot.send_message(
            chat_id=driver.id,
            text=get_text(driver.id, 'rate_client', order_id, order['client_name']),
            parse_mode="HTML",
            reply_markup=client_rating_keyboard
        )

        # Информация об оплате водителю
        await router.bot.send_message(
            chat_id=driver.id,
            text=get_text(driver.id, 'order_payment_info', order_id, order['price']),
            parse_mode="HTML"
        )

        # Удаляем сообщение о заказе из группы
        try:
            await router.bot.delete_message(
                chat_id=DRIVER_GROUP_ID,
                message_id=order['message_id']
            )
        except Exception as e:
            print(f"Ошибка удаления сообщения завершенного заказа {order_id}: {e}")

        # Удаляем заказ из активных
        del active_orders[order_id]

    except Exception as e:
        print(f"Ошибка при завершении заказа: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# Добавим обработчик для ввода адреса вручную
async def input_address_manually(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await message.answer(get_text(user_id, 'enter_current_address'))
    await state.set_state(OrderTaxi.waiting_for_address)

# === ИНИЦИАЛИЗАЦИЯ ===
bot = Bot(
    token=API_TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

# Инициализация базы данных
db = Database()

async def main():
    """Основная функция запуска бота"""
    dp.include_router(router)

    router.bot = bot
    router.driver_group_id = DRIVER_GROUP_ID

    # Запускаем очистку старых заказов при старте
    await cleanup_old_orders()
    
    # Запускаем периодическую очистку в фоне
    asyncio.create_task(periodic_cleanup())
    
    print("Бот запущен, очистка старых заказов выполнена")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
