from pyrogram import Client, filters, types, enums
import requests
import json

# Загрузка констант
from constants import API_ID, API_HASH, TOKEN

TOKENS_FILE = 'user_tokens.json'

def read_user_data():
    try:
        with open(TOKENS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_user_data(user_id, data):
    users_data = read_user_data()
    users_data[user_id] = data
    with open(TOKENS_FILE, 'w') as file:
        json.dump(users_data, file)

app = Client('my_bot', api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

@app.on_message(filters.command('start'))
def start(client, message):
    buttons = [
        ['Указать Ngrok Token', 'Указать SSH данные', 'Получить SSH команду']
    ]
    reply_markup = types.ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    message.reply_text('Выберите опцию:', reply_markup=reply_markup)

@app.on_message(filters.text)
def handle_message(client, message):
    user_id = str(message.from_user.id)
    users_data = read_user_data()

    if message.text.startswith('/'):
        return

    if user_id in users_data and 'ssh_step' in users_data[user_id]:
        handle_ssh_input(client, message, users_data)
        return

    if message.text == 'Указать Ngrok Token':
        client.send_message(user_id, 'Введите ваш Ngrok API Token:')
    elif message.text == 'Указать SSH данные':
        start_ssh_setup(client, message, users_data, user_id)
    elif message.text == 'Получить SSH команду':
        generate_ssh_command(client, message, users_data)
    else:
        users_data[user_id] = {'ngrok_token': message.text}
        save_user_data(user_id, users_data[user_id])
        message.reply_text('Ngrok API Token сохранен.')

def start_ssh_setup(client, message, users_data, user_id):
    client.send_message(user_id, 'Введите имя пользователя SSH:')
    users_data[user_id]['ssh_step'] = 'username'
    save_user_data(user_id, users_data[user_id])

def handle_ssh_input(client, message, users_data):
    user_id = str(message.from_user.id)
    if users_data[user_id]['ssh_step'] == 'username':
        users_data[user_id]['ssh_username'] = message.text
        users_data[user_id]['ssh_step'] = 'keyfile'
        client.send_message(user_id, 'Введите имя файла ключа (или пропустите этот шаг, отправив /skip):')
        save_user_data(user_id, users_data[user_id])
    elif users_data[user_id]['ssh_step'] == 'keyfile':
        if message.text != '/skip':
            users_data[user_id]['ssh_keyfile'] = message.text
        else:
            users_data[user_id].pop('ssh_keyfile', None)
        client.send_message(user_id, 'SSH данные сохранены.')
        users_data[user_id].pop('ssh_step', None)
        save_user_data(user_id, users_data[user_id])

def generate_ssh_command(client, message, users_data):
    user_id = str(message.from_user.id)
    if user_id not in users_data or 'ngrok_token' not in users_data[user_id]:
        client.send_message(user_id, 'Ngrok Token не установлен.')
        return

    try:
        headers = {'Authorization': 'Bearer ' + users_data[user_id]['ngrok_token'], 'Ngrok-Version': '2'}
        response = requests.get('https://api.ngrok.com/tunnels', headers=headers)
        if response.status_code == 200:
            tunnels = response.json().get('tunnels', [])
            if tunnels:
                public_url = tunnels[0]['public_url']
                host, port = public_url.replace('tcp://', '').split(':')
                ssh_command = f'ssh {users_data[user_id].get("ssh_username", "user")}@{host} -p {port}'
                if 'ssh_keyfile' in users_data[user_id]:
                    ssh_command += f' -i {users_data[user_id]["ssh_keyfile"]}'
                client.send_message(user_id, f'```bash\n{ssh_command}\n```', parse_mode=enums.ParseMode.MARKDOWN)
            else:
                client.send_message(user_id, 'Ngrok туннели не найдены.')
        else:
            client.send_message(user_id, f'Ошибка запроса: {response.status_code}')
    except Exception as e:
        client.send_message(user_id, f'Ошибка: {e}')

app.run()
