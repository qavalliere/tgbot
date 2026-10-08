require('dotenv').config();
const { Telegraf, Markup, session } = require('telegraf');

// Валидация переменных окружения
const BOT_TOKEN = process.env.BOT_TOKEN;
const ADMIN_ID = process.env.ADMIN_ID;

if (!BOT_TOKEN) {
  console.error('❌ Ошибка: Переменная BOT_TOKEN не найдена в файле .env');
  process.exit(1);
}

if (!ADMIN_ID) {
  console.error('❌ Ошибка: Переменная ADMIN_ID не найдена в файле .env');
  process.exit(1);
}

// Настройки бизнеса
const BUSINESS_ADDRESS = process.env.BUSINESS_ADDRESS || 'г. Киев, ул. Центральная, 10';
const BUSINESS_PHONE = process.env.BUSINESS_PHONE || '+380 99 123 45 67';
const BUSINESS_SCHEDULE = process.env.BUSINESS_SCHEDULE || 'Пн-Сб: 09:00 - 20:00, Вс: 10:00 - 18:00';

// Хранилище заявок в памяти
const leads = new Map();
let leadCounter = 1000;

const bot = new Telegraf(BOT_TOKEN);

// Подключаем сессии для сохранения шагов FSM
bot.use(session());

// Клавиатуры (Reply)
const mainKeyboard = Markup.keyboard([
  ['📋 Оставить заявку'],
  ['💰 Услуги', '📍 Контакты'],
]).resize();

const servicesKeyboard = Markup.keyboard([
  ['📋 Оставить заявку'],
  ['◀️ В главное меню'],
]).resize();

const cancelKeyboard = Markup.keyboard([
  ['❌ Отменить'],
]).resize();

const phoneKeyboard = Markup.keyboard([
  [Markup.button.contactRequest('📱 Поделиться контактом')],
  ['❌ Отменить'],
]).resize();

const servicesChoiceKeyboard = Markup.keyboard([
  ['💇 Стрижка', '💅 Маникюр'],
  ['💄 Макияж', 'Другая услуга'],
  ['❌ Отменить'],
]).resize();

const confirmationKeyboard = Markup.keyboard([
  ['✅ Отправить', '❌ Отменить'],
]).resize();

// 1. Команда /start и кнопка возврата в меню
bot.start(async (ctx) => {
  ctx.session = null;
  const greeting =
    '👋 Добро пожаловать!\n' +
    'Мы готовы помочь вам.\n' +
    'Выберите действие:';
  return ctx.reply(greeting, mainKeyboard);
});

bot.hears('◀️ В главное меню', async (ctx) => {
  ctx.session = null;
  const greeting =
    '👋 Добро пожаловать!\n' +
    'Мы готовы помочь вам.\n' +
    'Выберите действие:';
  return ctx.reply(greeting, mainKeyboard);
});

// 2. Раздел "💰 Услуги"
bot.hears('💰 Услуги', async (ctx) => {
  const text =
    '💇 Стрижка — 500 грн\n' +
    '💅 Маникюр — 700 грн\n' +
    '💄 Макияж — 1000 грн';
  return ctx.reply(text, servicesKeyboard);
});

// 3. Раздел "📍 Контакты"
bot.hears('📍 Контакты', async (ctx) => {
  const text =
    '📍 Контакты:\n\n' +
    `🏢 Адрес: ${BUSINESS_ADDRESS}\n` +
    `📞 Телефон: ${BUSINESS_PHONE}\n` +
    `🕐 График работы: ${BUSINESS_SCHEDULE}`;
  return ctx.reply(text, mainKeyboard);
});

// 4. Отмена заявки
bot.command('cancel', async (ctx) => {
  ctx.session = null;
  return ctx.reply('❌ Оформление заявки отменено.\nВозвращаю вас в главное меню.', mainKeyboard);
});

bot.hears('❌ Отменить', async (ctx) => {
  ctx.session = null;
  return ctx.reply('❌ Оформление заявки отменено.\nВозвращаю вас в главное меню.', mainKeyboard);
});

// 5. Старт оформления заявки
bot.hears(['📋 Оставить заявку', '/apply'], async (ctx) => {
  ctx.session = { step: 'name', data: {} };
  return ctx.reply('Как вас зовут?', cancelKeyboard);
});

// 6. Обработка шагов диалога
bot.on('message', async (ctx) => {
  if (!ctx.session || !ctx.session.step) {
    return ctx.reply('Пожалуйста, выберите действие из меню:', mainKeyboard);
  }

  const { step, data } = ctx.session;

  // Шаг 1: Имя
  if (step === 'name') {
    if (!ctx.message.text) {
      return ctx.reply('Пожалуйста, введите ваше имя:');
    }
    data.name = ctx.message.text.trim();
    ctx.session.step = 'phone';
    return ctx.reply('Введите номер телефона.', phoneKeyboard);
  }

  // Шаг 2: Телефон
  if (step === 'phone') {
    let phone = '';
    if (ctx.message.contact) {
      phone = ctx.message.contact.phone_number;
    } else if (ctx.message.text) {
      phone = ctx.message.text.trim();
      if (phone.length < 5) {
        return ctx.reply(
          'Номер телефона слишком короткий. Пожалуйста, введите корректный номер или воспользуйтесь кнопкой «📱 Поделиться контактом».',
          phoneKeyboard
        );
      }
    } else {
      return ctx.reply(
        'Пожалуйста, введите номер телефона сообщением или нажмите кнопку «📱 Поделиться контактом».',
        phoneKeyboard
      );
    }

    data.phone = phone;
    ctx.session.step = 'service';
    return ctx.reply('Какая услуга вас интересует?', servicesChoiceKeyboard);
  }

  // Шаг 3: Услуга
  if (step === 'service') {
    if (!ctx.message.text) {
      return ctx.reply(
        'Пожалуйста, выберите услугу из предложенных кнопок или напишите её текстом.',
        servicesChoiceKeyboard
      );
    }
    data.service = ctx.message.text.trim();
    ctx.session.step = 'time';
    return ctx.reply('Когда вам удобно прийти?', cancelKeyboard);
  }

  // Шаг 4: Время
  if (step === 'time') {
    if (!ctx.message.text) {
      return ctx.reply(
        'Пожалуйста, укажите желаемую дату/время текстом (например: завтра в 14:00):',
        cancelKeyboard
      );
    }
    data.time = ctx.message.text.trim();
    ctx.session.step = 'confirmation';

    const summary =
      'Проверьте данные:\n\n' +
      `👤 Имя: ${data.name}\n` +
      `📞 Телефон: ${data.phone}\n` +
      `💇 Услуга: ${data.service}\n` +
      `🕐 Время: ${data.time}\n\n` +
      'Всё верно?';

    return ctx.reply(summary, confirmationKeyboard);
  }

  // Шаг 5: Подтверждение клиентом
  if (step === 'confirmation') {
    if (ctx.message.text === '✅ Отправить') {
      const { name, phone, service, time } = data;

      // Генерируем уникальный номер заявки
      leadCounter += 1;
      const leadId = String(leadCounter);
      const clientChatId = ctx.chat.id;

      // Сохраняем заявку для последующей обработки админом
      leads.set(leadId, {
        leadId,
        clientChatId,
        clientUsername: ctx.from.username ? `@${ctx.from.username}` : 'нет',
        name,
        phone,
        service,
        time,
        status: 'pending',
      });

      // Сообщение владельцу бизнеса с INLINE-кнопками для подтверждения/отклонения
      const adminNotification =
        `🔔 НОВАЯ ЗАЯВКА #${leadId}\n\n` +
        `👤 Имя: ${name}\n` +
        `📞 Телефон: ${phone}\n` +
        `💇 Услуга: ${service}\n` +
        `🕐 Желаемое время: ${time}\n` +
        `💬 Никнейм: ${ctx.from.username ? `@${ctx.from.username}` : 'скрыт'}\n\n` +
        `Источник: Telegram`;

      const adminInlineKeyboard = Markup.inlineKeyboard([
        [
          Markup.button.callback('✅ Подтвердить', `approve_${leadId}`),
          Markup.button.callback('❌ Отклонить', `reject_${leadId}`),
        ],
      ]);

      try {
        await ctx.telegram.sendMessage(ADMIN_ID, adminNotification, adminInlineKeyboard);
        console.log(`[INFO] Заявка #${leadId} отправлена админу ${ADMIN_ID}`);
      } catch (err) {
        console.error(`[ERROR] Не удалось отправить сообщение администратору (${ADMIN_ID}):`, err.message);
      }

      ctx.session = null;
      return ctx.reply(
        '✅ Спасибо! Ваша заявка принята.\nВладелец свяжется с вами или подтвердит время прямо здесь.',
        mainKeyboard
      );
    } else {
      return ctx.reply(
        'Пожалуйста, подтвердите заявку кнопкой «✅ Отправить» или нажмите «❌ Отменить».',
        confirmationKeyboard
      );
    }
  }
});

// 7. Обработка нажатий админа: "✅ Подтвердить"
bot.action(/^approve_(\d+)$/, async (ctx) => {
  // Проверка прав: только владелец (ADMIN_ID) может нажимать
  if (String(ctx.from.id) !== String(ADMIN_ID)) {
    return ctx.answerCbQuery('⛔ У вас нет прав администратора', { show_alert: true });
  }

  const leadId = ctx.match[1];
  const lead = leads.get(leadId);

  if (!lead) {
    return ctx.answerCbQuery('⚠️ Данные заявки не найдены (возможно, бот перезапускался).', { show_alert: true });
  }

  if (lead.status !== 'pending') {
    return ctx.answerCbQuery(`Заявка #${leadId} уже обработана (статус: ${lead.status}).`, { show_alert: true });
  }

  lead.status = 'approved';

  // Обновляем сообщение у админа: убираем кнопки и показываем статус
  const updatedAdminText =
    `🔔 ЗАЯВКА #${leadId} — ✅ ПОДТВЕРЖДЕНА\n\n` +
    `👤 Имя: ${lead.name}\n` +
    `📞 Телефон: ${lead.phone}\n` +
    `💇 Услуга: ${lead.service}\n` +
    `🕐 Время: ${lead.time}\n\n` +
    `Статус: ✅ Подтверждена администратором`;

  await ctx.editMessageText(updatedAdminText);
  await ctx.answerCbQuery(`Заявка #${leadId} подтверждена! Клиент уведомлен.`);

  // Мгновенно уведомляем клиента в его личном чате
  try {
    const clientMessage =
      `🎉 Отличные новости! Ваша заявка #${leadId} подтверждена администратором!\n\n` +
      `💇 Услуга: ${lead.service}\n` +
      `🕐 Ждём вас: ${lead.time}\n` +
      `🏢 Адрес: ${BUSINESS_ADDRESS}\n` +
      `📞 Телефон для связи: ${BUSINESS_PHONE}`;

    await ctx.telegram.sendMessage(lead.clientChatId, clientMessage);
    console.log(`[INFO] Клиент ${lead.clientChatId} получил подтверждение заявки #${leadId}`);
  } catch (err) {
    console.error(`[ERROR] Не удалось отправить уведомление клиенту ${lead.clientChatId}:`, err.message);
  }
});

// 8. Обработка нажатий админа: "❌ Отклонить"
bot.action(/^reject_(\d+)$/, async (ctx) => {
  if (String(ctx.from.id) !== String(ADMIN_ID)) {
    return ctx.answerCbQuery('⛔ У вас нет прав администратора', { show_alert: true });
  }

  const leadId = ctx.match[1];
  const lead = leads.get(leadId);

  if (!lead) {
    return ctx.answerCbQuery('⚠️ Данные заявки не найдены.', { show_alert: true });
  }

  if (lead.status !== 'pending') {
    return ctx.answerCbQuery(`Заявка #${leadId} уже обработана.`, { show_alert: true });
  }

  lead.status = 'rejected';

  // Обновляем сообщение у админа
  const updatedAdminText =
    `🔔 ЗАЯВКА #${leadId} — ❌ ОТКЛОНЕНА\n\n` +
    `👤 Имя: ${lead.name}\n` +
    `📞 Телефон: ${lead.phone}\n` +
    `💇 Услуга: ${lead.service}\n` +
    `🕐 Время: ${lead.time}\n\n` +
    `Статус: ❌ Отклонена администратором`;

  await ctx.editMessageText(updatedAdminText);
  await ctx.answerCbQuery(`Заявка #${leadId} отклонена. Клиент уведомлен.`);

  // Уведомляем клиента
  try {
    const clientMessage =
      `Здравствуйте! К сожалению, мы не можем подтвердить вашу заявку #${leadId} на ${lead.time} (время занято либо мастер недоступен).\n\n` +
      `Пожалуйста, выберите другое удобное время в меню «📋 Оставить заявку» или свяжитесь с нами: ${BUSINESS_PHONE}.`;

    await ctx.telegram.sendMessage(lead.clientChatId, clientMessage);
    console.log(`[INFO] Клиент ${lead.clientChatId} получил уведомление об отклонении заявки #${leadId}`);
  } catch (err) {
    console.error(`[ERROR] Не удалось отправить уведомление клиенту ${lead.clientChatId}:`, err.message);
  }
});

// Глобальная обработка ошибок
bot.catch((err, ctx) => {
  console.error(`[ERROR] Ошибка при обработке обновления для ${ctx.updateType}:`, err);
});

// Запуск бота
console.log('Подключение к серверам Telegram...');
bot.telegram.getMe()
  .then((botInfo) => {
    console.log(`✅ Бот @${botInfo.username} успешно подключен и ожидает сообщений в Telegram!`);
    return bot.launch({ dropPendingUpdates: true });
  })
  .catch((err) => {
    console.error('❌ Ошибка запуска бота:', err);
  });

// Корректное завершение при остановке
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
