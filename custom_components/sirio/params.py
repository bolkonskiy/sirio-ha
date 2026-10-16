"""Sirio base and advanced parameters.

The panel only steps a register up or down. Display units below match
management.js. A missing impedance-style gap does not apply here: every
index listed in the panel is a real register.
"""

from __future__ import annotations

from dataclasses import dataclass


def _voltage_display(raw: int) -> float:
    return round((((raw + 255) * 8) / 14) - 4)


def _voltage_raw(value: float) -> int:
    return min(range(256), key=lambda raw: abs(_voltage_display(raw) - value))


@dataclass(frozen=True, slots=True)
class NumberParam:
    """A numeric register."""

    index: int
    key: str
    name: str
    advanced: bool
    minimum: float
    maximum: float
    step: float
    precision: int
    mode: str
    unit: str | None = None
    note: str = ""

    def display(self, raw: int) -> float:
        """Convert a raw register to the panel value."""
        if self.mode == "div10":
            return raw / 10
        if self.mode == "sub10":
            return raw - 10
        if self.mode == "mul10":
            return raw * 10
        if self.mode == "voltage":
            return _voltage_display(raw)
        return float(raw)

    def encode(self, value: float) -> int:
        """Convert a panel value back to the raw register."""
        if self.mode == "div10":
            return int(round(value * 10))
        if self.mode == "sub10":
            return int(round(value + 10))
        if self.mode == "mul10":
            return int(round(value / 10))
        if self.mode == "voltage":
            return _voltage_raw(value)
        return int(round(value))


@dataclass(frozen=True, slots=True)
class SelectParam:
    """A register whose raw values are named choices."""

    index: int
    key: str
    name: str
    advanced: bool
    options: dict[int, str]
    note: str = ""


NUMBERS: tuple[NumberParam, ...] = (
    NumberParam(0, "pmax", "Pmax", False, 0, 10, 0.1, 1, "div10", "bar", "Рабочая точка, постоянное давление. Сервисный мануал: базовая настройка."),
    NumberParam(1, "delta_start", "Дельта пуска", False, 0, 5, 0.1, 1, "div10", "bar", "На сколько давление должно упасть от Pmax, чтобы насос включился. Разница с Pmax не меньше 0,3 бар, лучше от 0,5."),
    NumberParam(2, "dry_run_pressure", "Давление сухого хода", False, 0, 5, 0.1, 1, "div10", "bar", "Порог давления для защиты от сухого хода."),
    NumberParam(3, "pressure_limit", "Предел давления", False, 0, 10, 0.1, 1, "div10", "bar", "Выше этого порога авария E9, предел давления."),
    NumberParam(4, "pmax2", "Pmax 2", False, 0, 10, 0.1, 1, "div10", "bar", "Вторая рабочая точка, когда контакт AUX или вход I/O стоит в 3 X2."),
    NumberParam(5, "delta_stop", "Дельта стопа", False, 0, 5, 0.1, 1, "div10", "bar", "Дельта давления для останова насоса."),
    NumberParam(10, "imax", "Imax", False, 0.5, 20, 0.1, 1, "div10", "A", "Максимальный ток двигателя. Выше него авария E6, перегрузка. На этом контроллере шкала до десятков ампер, не до 9,7 как в старой книжке."),
    NumberParam(12, "freq_min", "Минимальная частота", False, 0, 70, 1, 0, "raw", "Hz", "П. 1.2. Минимум для пуска и работы. Для трехфазного насоса мануал советует 25 Гц, для однофазного 30 Гц."),
    NumberParam(13, "freq_stop", "Частота стопа", False, 0, 70, 1, 0, "raw", "Hz", "П. 1.3. Ниже этой частоты насос останавливается, если флюсостат выключен. Частые пуски — уменьшить, не останавливается — увеличить."),
    NumberParam(14, "freq_nominal", "Номинальная частота", False, 45, 70, 1, 0, "raw", "Hz", "П. 1.4. Мануал: 50 или 60 Гц, строго по шильдику насоса."),
    NumberParam(15, "freq_switching", "Частота переключения", False, 3, 10, 1, 0, "raw", "kHz", "П. 1.5. Мануал: 3, 5 или 10 кГц. Выше — тише и ровнее, но горячее плата и больше помех на длинном кабеле."),
    NumberParam(16, "freq_correction", "Коррекция частоты", False, -5, 5, 1, 0, "sub10", "Hz", "П. 1.6. Сдвиг максимума от номинала, от -5 до +5 Гц. Минус ограничивает мощность, плюс — только после сверки с производителем насоса."),
    NumberParam(25, "stop_delay", "Задержка стопа", False, 0, 60, 0.1, 1, "div10", "s", "П. 2.5. Секунды после закрытия кранов. Заводское 10 с. Увеличить, если на слабом потоке насос дергается или ловит сухой ход."),
    NumberParam(26, "autoreset_interval", "Интервал автосброса", False, 1, 240, 1, 0, "raw", "min", "П. 2.6. Пауза между проверками, появилась ли вода. Максимум 240 мин, мануал советует 60."),
    NumberParam(27, "autoreset_tests", "Число тестов автосброса", False, 0, 20, 1, 0, "raw", "П. 2.7. Сколько попыток выйти из сухого хода. 0 отключает автосброс, максимум 20."),
    NumberParam(40, "vboost", "Vboost", True, 0, 30, 1, 0, "raw", "%", "П. 4.0. Добавка напряжения на 0 Гц, компенсация потерь в обмотке. Больше — выше напряжение на моторе при низкой частоте."),
    NumberParam(41, "dry_run_delay", "Задержка сухого хода", True, 0, 240, 1, 0, "raw", "s", "П. 4.1. Задержка перед защитой от сухого хода. Увеличить на длинной всасывающей линии и при долгом заполнении."),
    NumberParam(44, "pwm_dead_time", "Dead time PWM", True, 0, 100, 1, 0, "raw", "x125ns", "П. 4.4. Пауза между переключениями IGBT одной стойки. Мануал: менять только вместе с производителем."),
    NumberParam(45, "ki", "Ki", True, 0, 50, 1, 0, "raw", "П. 4.5. Интеграл ПИД. Больше — давление ближе к уставке, слишком много — качает давление."),
    NumberParam(46, "kp", "Kp", True, 0, 50, 1, 0, "raw", "П. 4.6. Пропорция ПИД. Больше — быстрее реакция, слишком много — броски давления."),
    NumberParam(47, "boost_time", "Время boost", True, 0, 5000, 10, 0, "mul10", "ms", "П. 4.7. Сколько держать максимальную частоту на старте, если плавный пуск выключен."),
    NumberParam(50, "ta_max", "Ta max", True, 40, 100, 1, 0, "raw", "°C", "П. 5.0. Максимум температуры платы до тепловой аварии. Мануал: менять только с разрешения производителя."),
    NumberParam(51, "tm_max", "Tm max", True, 40, 100, 1, 0, "raw", "°C", "П. 5.1. Максимум температуры модуля IGBT. Мануал: менять только с разрешения производителя."),
    NumberParam(52, "ta_reduction", "Индекс снижения Ta", True, 0, 20, 1, 0, "raw", "Hz/°C", "П. 5.2. На сколько Гц резать частоту за каждый градус, когда до Ta max осталось меньше 5 °C."),
    NumberParam(53, "tm_reduction", "Индекс снижения Tm", True, 0, 20, 1, 0, "raw", "Hz/°C", "П. 5.3. То же для температуры модуля IGBT."),
    NumberParam(54, "min_flow", "Минимальный поток", True, 0, 50, 1, 0, "raw", "L/min", "П. 5.4. Ниже этого потока при закрытых кранах насос останавливается. Меньше — можно держать совсем слабый разбор."),
    NumberParam(55, "ipm", "Разгон", True, 0, 20, 1, 0, "raw", "Hz/s", "П. 5.5. Скорость рампы разгона из ожидания. На Sirio IPM это выбор мотора, на Universal — рампы."),
    NumberParam(56, "voltage_min", "Минимальное напряжение", True, 100, 280, 1, 0, "voltage", "V", "П. 5.6. Ниже этого порога авария низкого напряжения."),
    NumberParam(57, "voltage_max", "Максимальное напряжение", True, 100, 280, 1, 0, "voltage", "V", "П. 5.7. Выше этого порога авария высокого напряжения. Примерно на 30 В ниже насос уже начинает плавно сбрасывать обороты."),
    NumberParam(59, "debug", "Переменная отладки", True, 0, 255, 1, 0, "raw", "П. 5.9. Какую внутреннюю переменную показывать для отладки."),
)

SELECTS: tuple[SelectParam, ...] = (
    SelectParam(6, "unit", "Единица измерения", False, {9: "BAR", 10: "PSI"}, "BAR или PSI для давления на панели."),
    SelectParam(11, "rotation", "Направление вращения", False, {21: "-->", 22: "<--"}, "Стрелка на панели не гарантирует сторону вращения. Проверять по насосу."),
    SelectParam(17, "soft_start_mode", "Плавный пуск", False, {7: "ON", 8: "OFF"}, "П. 1.7. ON — набор оборотов плавно. OFF — сначала максимум на время boost, п. 4.7."),
    SelectParam(20, "flow_switch", "Флюсостат", False, {7: "ON", 8: "OFF"}, "П. 2.0. Заводское ON. OFF только если датчик потока врет: тогда обязательны частота стопа, давление сухого хода и гидроаккумулятор сразу после Sirio."),
    SelectParam(21, "command_source", "Источник команды", False, {18: "MAN", 19: "0-10V", 20: "PRESS"}, "П. 2.1. PRESS — по давлению. MAN — ручной, без сухого хода и предела давления, только ненадолго и под присмотром."),
    SelectParam(22, "aux_contact", "Контакт AUX", False, {23: "1<->", 24: "2<--", 25: "3 X2"}, "П. 2.2. 1<-> пара Sirio, 2<-- дистанционный пуск, 3 X2 вторая уставка Pmax2."),
    SelectParam(23, "io_input", "Вход платы I/O", False, {24: "2<--", 25: "3 X2", 26: "ERR", 27: "OFF"}, "П. 2.3. OFF выключен, ERR внешняя авария, 2<-- пуск по И с AUX, 3 X2 вторая уставка по ИЛИ с AUX."),
    SelectParam(24, "io_output", "Выход платы I/O", False, {3: "OFF", 4: "ERR", 5: "P.ON", 6: "AUX"}, "П. 2.4. OFF, ERR авария, P.ON насос работает, AUX второй насос. Нагрузка реле не больше 0,3 А."),
    SelectParam(28, "total_autoreset", "Полный автосброс", False, {7: "ON", 8: "OFF"}, "П. 2.8. ON сбрасывает любую аварию, не только сухой ход. Мануал предупреждает: для перегрузки это опасно."),
    SelectParam(42, "starts_per_hour", "Защита пусков в час", True, {11: "OFF", 12: "10", 13: "20", 14: "30", 15: "40", 16: "50", 17: "60"}, "П. 4.2. Лимит пусков в час, проверка утечки. OFF отключает. Превышение — авария E11."),
    SelectParam(43, "antiblock", "Антиблокировка", True, {7: "ON", 8: "OFF"}, "П. 4.3. Если сутки не было запроса, раз в 24 часа короткий пуск, чтобы не закис сальник."),
    SelectParam(48, "relay_mode", "Реле N.O. / N.C.", True, {1: "N.O.", 2: "N.C."}, "П. 4.8. Нормально открытое или закрытое реле платы I/O. Если панель показывает ---, регистр не в этих двух положениях, и шагать его нельзя."),
)

ALL_PARAMS: tuple[NumberParam | SelectParam, ...] = NUMBERS + SELECTS
PARAM_INDEXES: tuple[int, ...] = tuple(item.index for item in ALL_PARAMS)
PARAMS_BY_INDEX: dict[int, NumberParam | SelectParam] = {item.index: item for item in ALL_PARAMS}
