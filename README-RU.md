<div align="center">
  <img src="fragment.svg" alt="Fragment Logo" width="120" height="120" style="border-radius: 24px;">

  <h1 style="margin-top: 24px;">💎 Fragment API от @bohd4nx</h1>

  <p style="font-size: 18px; margin-bottom: 24px;">
    <b>Автоматизация пополнений TON, покупки Telegram Premium и Stars через Fragment.com</b>
  </p>

[Сообщить об ошибке](https://github.com/bohd4nx/fragmentapi/issues) · [Запросить функцию](https://github.com/bohd4nx/fragmentapi/issues) · [**Донат TON**](https://app.tonkeeper.com/transfer/UQBUAa7KCx1ifmoEy6lF7j-822Dm_cE1j9SR7UWteu3jzukV)

</div>

---

## ✨ Возможности

- 💰 **Пополнение TON для рекламы** - Отправка TON для рекламных кампаний и покупки подарков (1-1,000,000,000 TON)
- 👑 **Подарки Telegram Premium** - Покупка Premium подписок(3, 6 или 12 месяцев)
- ⭐ **Покупка Telegram Stars** - Покупка Stars для пользователей (50-1,000,000 Stars)

## 🚀 Быстрый старт

### 1. Установка

```bash
git clone https://github.com/bohd4nx/FragmentAPI.git
cd FragmentAPI
pip install -r requirements.txt
```

### 2. Настройка

Скопируйте пример конфигурации и отредактируйте:

```bash
cp .env.example .env
```

Отредактируйте файл `.env`:

```env
COOKIES = your_fragment_cookies_here

SEED = word1 word2 word3 ... word24

HASH = your_fragment_hash_here

API_KEY = your_ton_api_key_here
```

### 3. Получение необходимых данных

#### 🍪 Куки Fragment.com

**Предварительные требования**: Войдите в свой аккаунт Telegram и подключите TON кошелёк, который хотите использовать для платежей.

1. **Установите расширение Cookie Editor**:

   - Скачайте из [Chrome Web Store](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
   - Добавьте расширение в ваш браузер

2. **Извлечение куки**:
   - Откройте [Fragment.com](https://fragment.com) и убедитесь, что вы вошли в систему
   - Полностью обновите страницу
   - Нажмите на иконку расширения Cookie Editor
   - Нажмите кнопку **"Export"**
   - Выберите формат **"Header String"**
   - Скопируйте результат → вставьте в `COOKIES` в вашем `.env` файле
   - **Важно**: Заключите значение в кавычки, чтобы точки с запятой не интерпретировались как комментарии

**Ожидаемый формат**:

```env
COOKIES = "stel_token=<TOKEN>;stel_dt=<STEL_DT>;stel_ssid=<SSID>;stel_ton_token=<TON_TOKEN>"
```

#### 🔐 Seed-фраза TON кошелька

**Если у вас ещё нет TON кошелька**:

1. **Скачайте Tonkeeper**:

   - iOS: [App Store](https://apps.apple.com/app/tonkeeper/id1587742107)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=com.ton_keeper)

2. **Создайте новый кошелёк**:

   - Откройте приложение Tonkeeper
   - Нажмите **"Создать новый кошелёк"**
   - **ВАЖНО**: Запишите вашу 24-словную seed-фразу на бумаге
   - Храните её в безопасном месте - никогда не делитесь ей ни с кем!
   - Завершите настройку кошелька

3. **Получите вашу seed-фразу**:
   - Если у вас уже есть кошелёк, перейдите в Настройки → Резервное копирование
   - Введите ваш пароль
   - Скопируйте 24 слова → вставьте в `SEED` в вашем `.env` файле

**Формат**: `слово1 слово2 слово3 ... слово24`

#### 🔗 Хеш Fragment

**Предварительные требования**: Сначала завершите настройку куки выше.

1. **Подключите кошелёк к Fragment**:

   - Перейдите на [Fragment.com](https://fragment.com)
   - Убедитесь, что ваш TON кошелёк подключён
   - Войдите с вашим аккаунтом Telegram

2. **Извлечение хеша**:
   - Откройте **Инструменты разработчика** (F12)
   - Нажмите на вкладку **"Сеть"**
   - Перейдите к [покупке Stars](https://fragment.com/stars/buy)
   - Выберите получателя как **"Buy for myself"**
   - Обновите страницу (Ctrl+R / Cmd+R)
   - Найдите сетевые запросы, содержащие `?hash=`
   - Найдите значение хеша и скопируйте его → вставьте в `HASH` в вашем `.env` файле

**Ожидаемый формат**: `?hash=<ваш_хеш_здесь>`

#### 🔑 API ключ TON

1. **Получите API ключ**:
   - Посетите [TON Console](https://tonconsole.com)
   - Создайте аккаунт и войдите
   - Сгенерируйте новый API ключ
   - Скопируйте ключ → вставьте в `API_KEY` в вашем `.env` файле

**Альтернатива**: Вы также можете использовать [TON API](https://tonapi.io) для получения API ключа.

### 4. Использование

#### Запуск примеров

```bash
python main.py
```

#### Программное использование

```python
from app.methods import FragmentTon, FragmentPremium, FragmentStars

# Пополнение TON для рекламы
ton_client = FragmentTon()
result = await ton_client.topup_ton("@username", 5)

# Покупка Premium
premium_client = FragmentPremium()
result = await premium_client.buy_premium("@username", 6)

# Покупка Stars
stars_client = FragmentStars()
result = await stars_client.buy_stars("@username", 50)
```

### Поддерживаемые операции

| Операция            | Метод                           | Параметры                          | Ограничения         |
| ------------------- | ------------------------------- | ---------------------------------- | ------------------- |
| **Пополнение TON**  | `topup_ton(username, amount)`   | Имя пользователя, количество TON   | 1-1,000,000,000 TON |
| **Подарок Premium** | `buy_premium(username, months)` | Имя пользователя, длительность     | 3, 6 или 12 месяцев |
| **Покупка Stars**   | `buy_stars(username, amount)`   | Имя пользователя, количество Stars | 50-1,000,000 Stars  |

### Форматы имён пользователей

Все методы принимают различные форматы имён пользователей:

- `@username` (с @)
- `username` (без @)

<div align="center">

### Made with ❤️ by [@bohd4nx](https://t.me/bohd4nx)

**Поставьте ⭐ этому репозиторию, если он оказался полезным!**

</div>
