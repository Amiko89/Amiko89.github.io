import sys
import telebot
import requests
from bs4 import BeautifulSoup
import time
import mysql.connector
from mysql.connector import errorcode

bot = telebot.TeleBot('1656087115:AAHUMv9M4uKcnrdH2up6nHPGTNKKePTAYtg')

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="5890741Vlad!ik",
        port="3306",
        database="users"
)
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
        sys.exit()
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
        sys.exit()
    else:
        print(err)
        sys.exit()

cursor = db.cursor()

# cursor.execute("CREATE DATABASE users")

# cursor.execute("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, first_name VARCHAR(255), last_name VARCHAR(255),"
#                " user_id INT UNIQUE)")

# cursor.execute("ALTER TABLE users ADD COLUMN ex_rate INT")

user_data = {}  # сюди будемо тимчасово вставляти дані


class User:
    def __init__(self, first_name):
        self.first_name = first_name
        self.last_name = ''
        self.ex_rate = ''


class Currency:
    BTC_USD = 'https://coinmarketcap.com/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'}

    current_converted_price = 0

    def __init__(self):
        self.current_converted_price = float(self.get_currency_price())

    def get_currency_price(self):
        full_page = requests.get(self.BTC_USD, headers=self.headers)
        soup = BeautifulSoup(full_page.content, 'html.parser')
        convert = soup.findAll("a", {"class": "cmc-link", "href": "/currencies/bitcoin/markets/"})
        # print(convert[0].text)
        return convert[0].text.replace(",", "").replace("$", "")


currency = Currency()


@bot.message_handler(commands=['start'])
def start(message):
    send_mess = f"Hi!\n" \
                f"I'm Notifiex, your personal exchange rate notifier!\n" \
                f"I'll send you exchange rate for BTC/USD pair whenever it has grown since the last check.\n" \
                f"Actual rate: <b>1 BTC = {currency.get_currency_price()}</b> USD"
    bot.send_message(message.chat.id, send_mess, parse_mode='html')
    try:
        user_id = message.from_user.id
        user = User(message.from_user.first_name)
        user.last_name = message.from_user.last_name
        user.ex_rate = float(currency.get_currency_price())

        sql = "INSERT INTO users (first_name, last_name, user_id, ex_rate) VALUES (%s, %s, %s, %s)"
        val = (user.first_name, user.last_name, user_id, user.ex_rate)
        cursor.execute(sql, val)
        db.commit()  # Since by default Connector/Python does not autocommit, it is important to call this method after
        # every transaction that modifies data for tables that use transactional storage engines.

        while True:
            actual_price = float(currency.get_currency_price())
            user_id = message.from_user.id

            sql = "SELECT ex_rate FROM users WHERE user_id = %s"
            val = (user_id, )
            cursor.execute(sql, val)
            result = cursor.fetchone()
            print(result)

            if actual_price > result[0]:
                print('Actual price: {0}, price in db: {0}'.format(actual_price, result[0]))
                rate_up = f"Hey, rate has grown up!\nNow, 1 BTC costs {actual_price} USD"
                print(rate_up)
                bot.send_message(message.from_user.id, rate_up, parse_mode='html')

                sql = "UPDATE users SET ex_rate = %s WHERE user_id = %s"
                val = (actual_price, user_id)
                cursor.execute(sql, val)
                db.commit()

            elif actual_price < result[0]:
                print('Actual price: {0}, price in db: {0}'.format(actual_price, result[0]))
                rate_down = f"Hey, rate has decreased!\nNow, 1 BTC costs {actual_price} USD"
                print(rate_down)
                bot.send_message(message.from_user.id, rate_down, parse_mode='html')

                sql = "UPDATE users SET ex_rate = %s WHERE user_id = %s"
                val = (actual_price, user_id)
                cursor.execute(sql, val)
                db.commit()

            # else:
            #     print('Actual price: {:.4f}, price in db: {:.4f}'.format(actual_price, result[0]))
            #     print("Nothing changed")
            time.sleep(20)
    except Exception as e:
        bot.reply_to(message, 'oops_2')


@bot.message_handler(content_types=['text'])
def mess(message):
    if 'rate' in message.text:
        actual_price = currency.get_currency_price()
        send_mess = f"Actual rate: 1 BTC = {actual_price} USD"
        bot.send_message(message.chat.id, send_mess, parse_mode='html')
        while True:
            actual_price = float(currency.get_currency_price())
            user_id = message.from_user.id

            # Don't forget to prevent sql injection
            cursor.execute("SELECT ex_rate FROM users WHERE user_id = {0}".format(user_id))
            result = cursor.fetchone()

            if actual_price > result[0]:
                rate_up = f"Hey, rate has grown up!\nNow, 1 BTC costs {actual_price} USD"
                print(rate_up)
                bot.send_message(message.from_user.id, rate_up, parse_mode='html')

                cursor.execute(f"UPDATE users SET ex_rate = {actual_price} WHERE user_id = {user_id}")
                db.commit()

            elif actual_price < result[0]:
                rate_down = f"Hey, rate has decreased!\nNow, 1 BTC costs {actual_price} USD"
                print(rate_down)
                bot.send_message(message.from_user.id, rate_down, parse_mode='html')

                cursor.execute(f"UPDATE users SET ex_rate = {actual_price} WHERE user_id = {user_id}")
                db.commit()

            else:
                print("Nothing changed")
            time.sleep(20)
    else:
        sorry_mess = f"Sorry, I can't understand you"
        bot.send_message(message.chat.id, sorry_mess, parse_mode='html')
        while True:
            actual_price = float(currency.get_currency_price())
            user_id = message.from_user.id

            # Don't forget to prevent sql injection
            cursor.execute("SELECT ex_rate FROM users WHERE user_id = {0}".format(user_id))
            result = cursor.fetchone()

            if actual_price > result[0]:
                rate_up = f"Hey, rate has grown up!\nNow, 1 BTC costs {actual_price} USD"
                print(rate_up)
                bot.send_message(message.from_user.id, rate_up, parse_mode='html')

                cursor.execute(f"UPDATE users SET ex_rate = {actual_price} WHERE user_id = {user_id}")
                db.commit()

            elif actual_price < result[0]:
                rate_down = f"Hey, rate has decreased!\nNow, 1 BTC costs {actual_price} USD"
                print(rate_down)
                bot.send_message(message.from_user.id, rate_down, parse_mode='html')

                cursor.execute(f"UPDATE users SET ex_rate = {actual_price} WHERE user_id = {user_id}")
                db.commit()

            else:
                print("Nothing changed")
            time.sleep(20)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)