-- Миграция для добавления настроек православного календаря
-- Выполните этот скрипт для добавления календарных настроек

-- Добавляем настройки календаря в ai_settings
INSERT INTO ai_settings (setting_key, setting_value, setting_type, description) VALUES
('calendar_enabled', 'true', 'boolean', 'Включена ли функция православного календаря'),
('calendar_default_header', 'true', 'boolean', 'Показывать заголовок календаря по умолчанию'),
('calendar_default_lives', 'true', 'boolean', 'Показывать жития святых по умолчанию'),
('calendar_default_tropars', 'true', 'boolean', 'Показывать тропари по умолчанию'),
('calendar_default_scripture', 'true', 'boolean', 'Показывать Евангельские чтения по умолчанию'),
('calendar_default_date_format', 'true', 'boolean', 'Показывать дату в григорианском/юлианском формате по умолчанию')
ON CONFLICT (setting_key) DO NOTHING;

-- Проверяем результат
SELECT setting_key, setting_value, setting_type, description 
FROM ai_settings 
WHERE setting_key LIKE 'calendar_%';