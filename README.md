# SELF STORAGE PROJECT

Telegram bot with warehouse rental.


## Project navigation
* Folders

`documents/` - a folder with files that are sent to the user, for example, a user agreement in pdf format.

`json_files/` - a folder with json files, warehouse data is stored there, and a database will be formed there.

* Files

`bot.py` - The main executable file through which the bot is launched, and all bot handlers are stored in this file.

`config.ini` - Configuration file with your settings.

`general_functions.py` - A file with general functions for the bot to work with.

`messages.py` - File with messages for users.

`Procfile` - File for bot deployment on hosting.

`requirements.txt` - File with used project libraries.

`validate_exceptions.py` - Custom errors for validation.

### Description of the bot

The bot will have 3 main branches - registration, order and personal account. Each branch has its own functionality:

1. Registration - The user must accept the data processing agreement and then fill in the required data -
Full name and phone number, then click on the registration button and if it was successful, it is recorded in the database.
2. Order - When you click on the order button, 5 warehouses with limits are issued -> The user has selected a warehouse ->
Indicates the order quantity -> Whether specific items need to be stored -> A list of matching boxes is displayed ->
For how long is storage -> The user selects a box -> Refine the information if everything is correct -> Payment
3. Personal account - a list of orders is displayed and the "Open box" button -> when pressed, it throws out a QR code to receive a box

### Implemented project features

- [x] Database
- [x] Registration
- [x] Order
- [x] Personal account
- [x] order QR codes
- [x] Find the nearest warehouse to the user
- [x] Order payment

## Setting up the project for yourself
You can use this bot for your needs. To do this, below are
bot setup steps:


#### 1. Install required libraries

The bot is written using the [python-telegram-bot](https://pypi.org/project/python-telegram-bot/) v13.2 library. For installation
all the necessary libraries, write the command:
```
pip install -r requirements.txt
```

#### 2. Create a `.env` file.
This file will store your secret data, fill in the file as follows:

```
TELEGRAM_TOKEN={TOKEN} | Your bot token in TG
PAYMENT_TOKEN={PAYMENT_TOKEN} | Your acquiring token, you can also get it in @BotFather in the payments tab
```

#### 3. Set up the config file.
The project repository has a `config.ini` file - it stores your project settings, namely the paths to the DB and User Agreement files.
Now the config file is full, you can familiarize yourself with it and leave it as it is or change it according to the example if you need it.

#### 4. Fill in the information about your warehouses.
The file `json_files/warehouses.json` contains information about your warehouses, fill it in like an existing file.
Please do not change the structure of the file, the currently existing file is an example.

#### 5. Run your bot.
After you have gone through all your steps - run your bot with the command:

```
python3 bot.py
```

## The authors
* [Alexander Zharyuk](https://github.com/AlexanderZharyuk/)
* [Elena LeenyTheBear](https://github.com/leenythebear)
* [Kirill Rudenko](https://github.com/rudenko-ks)
