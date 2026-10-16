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
    ref: str
    name: str
    advanced: bool
    minimum: float
    maximum: float
    step: float
    precision: int
    mode: str
    unit: str | None = None
    manual: str = ""

    @property
    def title(self) -> str:
        """English manual name, then the Russian name from the same manual."""
        return f"{self.ref} {self.name} — {RU[self.index][0]}"

    @property
    def name_ru(self) -> str:
        return RU[self.index][0]

    @property
    def manual_ru(self) -> str:
        return RU[self.index][1]

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
    ref: str
    name: str
    advanced: bool
    options: dict[int, str]
    manual: str = ""

    @property
    def title(self) -> str:
        """English manual name, then the Russian name from the same manual."""
        return f"{self.ref} {self.name} — {RU[self.index][0]}"

    @property
    def name_ru(self) -> str:
        return RU[self.index][0]

    @property
    def manual_ru(self) -> str:
        return RU[self.index][1]


NUMBERS: tuple[NumberParam, ...] = (
    NumberParam(
        0, "pmax", "0.0", "Pmax (set-point)", False, 0, 10, 0.1, 1, "div10", "bar",
        "Sets the working point: the constant pressure held in the system. After start, motor speed is regulated so the pressure stays as close as possible to Pmax. The smallest difference between Pmax and the start pressure is 0.3 bar; 0.5 bar or more is recommended. If Pmax is set above the pump's maximum head, the motor stops whenever the valves close, because Sirio stops the pump when flow falls below the minimum, regardless of pressure.",
    ),
    NumberParam(
        1, "delta_start", "0.1", "Delta pressure for pump start", False, 0, 5, 0.1, 1, "div10", "bar",
        "How far the pressure must fall below Pmax before the pump starts. If a tap opens, the pump waits until system pressure drops by this delta. The manual sets the minimum gap between Pmax and the start pressure at 0.3 bar and recommends at least 0.5 bar.",
    ),
    NumberParam(
        2, "dry_run_pressure", "0.2", "Dry running pressure", False, 0, 5, 0.1, 1, "div10", "bar",
        "Pressure threshold of the dry-running protection. When the flow switch is off, this value and the stop frequency (1.3) are what stop the pump if there is no water. On a long suction line, also increase the dry-run delay (4.1).",
    ),
    NumberParam(
        3, "pressure_limit", "0.3", "Pressure limit", False, 0, 10, 0.1, 1, "div10", "bar",
        "Maximum pressure threshold. Above it, alarm E9 (pressure limit) trips and the system stops. If E9 keeps coming back, check this setting.",
    ),
    NumberParam(
        4, "pmax2", "0.4", "Pmax 2 (set-point 2)", False, 0, 10, 0.1, 1, "div10", "bar",
        "Second working point. Sirio regulates to Pmax 2 instead of Pmax when the auxiliary contact, or the I/O board input, is set to 3 X2 and that contact is closed.",
    ),
    NumberParam(
        5, "delta_stop", "0.5", "Delta pressure for pump stop", False, 0, 5, 0.1, 1, "div10", "bar",
        "Pressure delta used to stop the pump. Together with the stop delay (2.5) it decides when regulation ends after demand falls.",
    ),
    NumberParam(
        10, "imax", "1.0", "Imax", False, 0.5, 20, 0.1, 1, "div10", "A",
        "Maximum current the motor may draw in normal running. Above it the motor is stopped: alarm E6, overload. A small overload is allowed for longer; a heavy overload trips immediately. If the current measured while running stays below 0.5 A, Sirio treats the motor as disconnected and stops. On first power-up, if Imax is still 0.5 A, the controller waits on this page until a real value is entered. The older user booklet limits the setting to 0.5–9.7 A; this Universal goes higher.",
    ),
    NumberParam(
        12, "freq_min", "1.2", "Minimum frequency", False, 0, 70, 1, 0, "raw", "Hz",
        "Minimum frequency at which the pump starts and runs. Service manual: about 25 Hz for a three-phase pump and 30 Hz for a single-phase pump. Check the pump manufacturer's data for the lowest frequency at which this motor still runs properly. The user booklet also gives it as a percentage of maximum frequency: 50% for a surface pump, 60% for a pump 8–10 m down, 70% deeper than 10 m. Raise it if start is too slow and pressure falls hard during start.",
    ),
    NumberParam(
        13, "freq_stop", "1.3", "Stop frequency", False, 0, 70, 1, 0, "raw", "Hz",
        "Used when the flow switch is off. Frequency below which the motor is stopped. During regulation, if Pmax is reached and the motor frequency is still below this value, the inverter stops the pump. If every tap is closed and pressure is steady, the pump stops in the normal way. If it does not stop, increase this value. If it restarts too often, decrease it.",
    ),
    NumberParam(
        14, "freq_nominal", "1.4", "Nominal motor frequency", False, 45, 70, 1, 0, "raw", "Hz",
        "Nominal output frequency of the inverter, 50 or 60 Hz, taken from the pump nameplate. A wrong choice can damage the pump.",
    ),
    NumberParam(
        15, "freq_switching", "1.5", "Switching frequency", False, 3, 10, 1, 0, "raw", "kHz",
        "PWM switching frequency of the inverter. The manual allows 3, 5 or 10 kHz. A higher frequency is quieter and smoother, but the board runs hotter, electromagnetic interference rises, and a long motor cable can be harmed. Use a lower frequency for medium and large pumps, when Sirio is far from the pump, or when the ambient temperature is high.",
    ),
    NumberParam(
        16, "freq_correction", "1.6", "Frequency correction", False, -5, 5, 1, 0, "sub10", "Hz",
        "Offset of the maximum frequency from the nominal value, from -5 Hz to +5 Hz. A negative offset limits pump power and helps avoid overload; lowering the frequency needs no extra precautions. A positive offset can raise performance a little and has to be checked with the pump manufacturer, within the inverter's maximum current.",
    ),
    NumberParam(
        25, "stop_delay", "2.5", "Delay on stop", False, 0, 60, 0.1, 1, "div10", "s",
        "How many seconds after all taps are closed the pump stops. If it cycles on a small flow, increase the delay so running is smoother. A longer delay also reduces dry-run trips, especially with borehole pumps and pumps that are slow to prime. Factory setting is 10 s.",
    ),
    NumberParam(
        26, "autoreset_interval", "2.6", "Autoreset interval", False, 1, 240, 1, 0, "raw", "min",
        "If the pump loses water on the suction side, Sirio cuts the motor to protect it. This is the wait, in minutes, before Sirio tests whether water is back. A successful test clears the fault and the system runs again; a failed test is repeated after the same interval. Maximum on this software is 240 minutes. The manual recommends 60. The older user booklet allows up to 300 minutes.",
    ),
    NumberParam(
        27, "autoreset_tests", "2.7", "No. autoreset tests", False, 0, 20, 1, 0, "raw", None,
        "How many times Sirio tries to restart after a dry-run stop. When the count is used up, the system stays off until someone resets it. 0 disables automatic restart. Maximum is 20. The user booklet counts only short starts that never reach about 2.5 l/min, and on that older software the maximum is 10.",
    ),
    NumberParam(
        40, "vboost", "4.0", "Vboost", True, 0, 30, 1, 0, "raw", "%",
        "Voltage boost at 0 Hz. Percentage added to the voltage at 0 Hz to compensate for stator losses. Raising it increases the voltage supplied to the motor as the frequency falls.",
    ),
    NumberParam(
        41, "dry_run_delay", "4.1", "Dry run", True, 0, 240, 1, 0, "raw", "s",
        "Delay before dry-running protection trips. Increase it if the suction pipes are very long or the pump takes a long time to prime.",
    ),
    NumberParam(
        44, "pwm_dead_time", "4.4", "Dead time PWM", True, 0, 100, 1, 0, "raw", "x125ns",
        "Dead time between two switching events of the IGBTs on the same branch. It may need changing to correct the average output voltage after the switching frequency (1.5) is changed. The manual says to ask the manufacturer before choosing a value.",
    ),
    NumberParam(
        45, "ki", "4.5", "Ki", True, 0, 50, 1, 0, "raw", None,
        "Integral constant of the PID that holds constant pressure. A higher value pulls the output pressure closer to the set-point. Too high and the regulation becomes unstable: the pressure keeps oscillating. The user booklet describes the same control as one PID value, factory 25, maximum 50: low values are slow but smooth, high values react faster.",
    ),
    NumberParam(
        46, "kp", "4.6", "Kp", True, 0, 50, 1, 0, "raw", None,
        "Proportional constant of the PID that holds constant pressure. A higher value makes the system react faster to pressure changes. Too high and it overshoots or brakes hard, and the pressure oscillates.",
    ),
    NumberParam(
        47, "boost_time", "4.7", "Boost time", True, 0, 5000, 10, 0, "mul10", "ms",
        "How long the pump runs at maximum frequency before PID regulation starts, used when soft-start (1.7) is off. Increase it if the pump struggles to start, especially a single-phase pump. Decrease it if that run-up raises the system pressure more than you want.",
    ),
    NumberParam(
        50, "ta_max", "5.0", "Ta max", True, 40, 100, 1, 0, "raw", "°C",
        "Maximum ambient temperature inside the inverter before thermal cut-out. The manual allows a change only with the manufacturer's authorisation, because it affects safe operation. Frequency reduction (5.2) starts when the temperature is within 5 °C of this limit.",
    ),
    NumberParam(
        51, "tm_max", "5.1", "Tm max", True, 40, 100, 1, 0, "raw", "°C",
        "Maximum IGBT module temperature before thermal cut-out. The manual allows a change only with the manufacturer's authorisation, because it affects safe operation. Frequency reduction (5.3) starts when the module temperature is within 5 °C of this limit.",
    ),
    NumberParam(
        52, "ta_reduction", "5.2", "Ta reduction index", True, 0, 20, 1, 0, "raw", "Hz/°C",
        "How much the maximum motor frequency is reduced, per degree, as the ambient temperature approaches Ta max (5.0). Reduction starts when the temperature is less than 5 °C below that limit. Past the threshold, maximum frequency falls by this many hertz for every further degree.",
    ),
    NumberParam(
        53, "tm_reduction", "5.3", "Tm reduction index", True, 0, 20, 1, 0, "raw", "Hz/°C",
        "How much the maximum motor frequency is reduced, per degree, as the IGBT module temperature approaches Tm max (5.1). Reduction starts when the module is less than 5 °C below that limit. Past the threshold, maximum frequency falls by this many hertz for every further degree.",
    ),
    NumberParam(
        54, "min_flow", "5.4", "Minimum flow", True, 0, 50, 1, 0, "raw", "L/min",
        "Flow below which the pump is stopped once every outlet is closed. Lower it to let the pump keep running at a very small flow. Raise it if the pump does not stop when delivery is fully closed. The user booklet quotes a typical stop threshold of about 2 l/min.",
    ),
    NumberParam(
        55, "ipm", "5.5", "IPM mod.", True, 0, 20, 1, 0, "raw", "Hz/s",
        "On Sirio Universal and Universal XP this is the frequency ramp: how fast the motor accelerates when the drive leaves stand-by. On Sirio IPM the same number is reserved for motor selection; see the IPM documentation. The panel label is IPM mod.",
    ),
    NumberParam(
        56, "voltage_min", "5.6", "Minimum voltage", True, 100, 280, 1, 0, "voltage", "V",
        "Minimum mains voltage. Below it the undervoltage protection trips (alarm E0, low voltage).",
    ),
    NumberParam(
        57, "voltage_max", "5.7", "Maximum voltage", True, 100, 280, 1, 0, "voltage", "V",
        "Maximum mains voltage. Above it the overvoltage protection trips (alarm E1, high voltage). From this setting the inverter also derives a level about 30 V lower, above which the pump slows down in a controlled way so the DC bus does not surge.",
    ),
    NumberParam(
        59, "debug", "5.9", "Debug Variable", True, 0, 255, 1, 0, "raw", None,
        "Selects an internal process variable and shows it, so its trend can be watched while the unit is running. Service use.",
    ),
)

SELECTS: tuple[SelectParam, ...] = (
    SelectParam(
        6, "unit", "0.6", "Unit of measurement", False, {9: "BAR", 10: "PSI"},
        "Unit used for pressure on the panel and for the pressure parameters: BAR or PSI.",
    ),
    SelectParam(
        11, "rotation", "1.1", "Rotation direction", False, {21: "-->", 22: "<--"},
        "Reverses motor rotation without changing the wiring. The arrow shown here is only a guide. It is not the real direction of rotation, which the installer still has to check on the pump.",
    ),
    SelectParam(
        17, "soft_start_mode", "1.7", "Soft-start", False, {7: "ON", 8: "OFF"},
        "ON: the pump ramps up gradually. OFF: for the boost time (4.7) the pump runs at maximum frequency, and only then does speed regulation start.",
    ),
    SelectParam(
        20, "flow_switch", "2.0", "Flow switch activation", False, {7: "ON", 8: "OFF"},
        "Built-in flow sensor. Factory setting is ON: the pump stops when the taps close and Sirio sees that flow has ended. The same sensor is part of the dry-running protection. Dirty water can make the sensor misread, so the pump no longer stops correctly. It can then be switched OFF, and Sirio works from pressure and frequency only. Stop frequency (1.3) and dry-running pressure (0.2) must be set carefully, and a pressure tank has to be fitted immediately after Sirio. Check that tank's pre-charge from time to time.",
    ),
    SelectParam(
        21, "command_source", "2.1", "Command source", False, {18: "MAN", 19: "0-10V", 20: "PRESS"},
        "PRESS: automatic control from system pressure. MAN: start, stop and speed from the buttons. In manual mode the dry-running protection and the pressure limits are off. The manual allows that only briefly, with a qualified person watching. 0-10V: external analogue command.",
    ),
    SelectParam(
        22, "aux_contact", "2.2", "Auxiliary contact function", False, {23: "1<->", 24: "2<--", 25: "3 X2"},
        "1<-> : stand-alone Sirio, or two Sirio units linked as a twin booster set. This is the factory setting. 2<-- : the auxiliary contact is a remote start/stop. 3 X2 : the auxiliary contact selects the second pressure set-point, Pmax 2.",
    ),
    SelectParam(
        23, "io_input", "2.3", "I/O board input function", False, {24: "2<--", 25: "3 X2", 26: "ERR", 27: "OFF"},
        "Function of the digital input on the optional I/O board. OFF: input disabled. ERR: a closed input stops the pump at once and shows External error. 2<-- : remote start/stop; if the auxiliary contact is also 2<--, both contacts must be closed to run (logical AND). 3 X2 : selects Pmax 2; if the auxiliary contact is also 3 X2, either contact selects the second set-point (logical OR).",
    ),
    SelectParam(
        24, "io_output", "2.4", "I/O board output function", False, {3: "OFF", 4: "ERR", 5: "P.ON", 6: "AUX"},
        "Function of the digital output on the optional I/O board. OFF: output disabled. ERR: the contact closes while Sirio is in fault. P.ON: the contact closes while the pump is running. AUX: runs an auxiliary pump at a fixed speed when the Sirio pump cannot meet demand. The contact closes when frequency is at the maximum and pressure has fallen below the start pressure. Do not put more than 0.3 A on the output relay.",
    ),
    SelectParam(
        28, "total_autoreset", "2.8", "Total automatic reset", False, {7: "ON", 8: "OFF"},
        "ON: automatic restart applies to every fault the system reports, not only dry running. The manual warns that an unsupervised restart after some faults, overload in particular, can damage the installation and the Sirio. Use it carefully.",
    ),
    SelectParam(
        42, "starts_per_hour", "4.2", "Protection starts per hour", True, {11: "OFF", 12: "10", 13: "20", 14: "30", 15: "40", 16: "50", 17: "60"},
        "Maximum pump starts in one hour, used as a leak check. OFF disables the protection. Above the limit, alarm E11 (maximum starts per hour) trips. The user booklet calls the same alarm Serious leakage and says to raise the limit if it trips without a real leak. Only short starts are counted, those that never reach about 2.5 l/min.",
    ),
    SelectParam(
        43, "antiblock", "4.3", "Anti-blockage protection", True, {7: "ON", 8: "OFF"},
        "24-hour anti-seize. If enabled, and nothing has asked the pump to run, Sirio starts it once every 24 hours so the mechanical seal does not seize.",
    ),
    SelectParam(
        48, "relay_mode", "4.8", "Relay N.O. - N.C. mode", True, {1: "N.O.", 2: "N.C."},
        "Output relay of the I/O board: normally open or normally closed. If the panel shows ---, the register is in neither position. It is not stepped from there, because reaching N.O. or N.C. would take hundreds of steps and the relay would change on the way.",
    ),
)

ALL_PARAMS: tuple[NumberParam | SelectParam, ...] = NUMBERS + SELECTS
PARAM_INDEXES: tuple[int, ...] = tuple(item.index for item in ALL_PARAMS)
PARAMS_BY_INDEX: dict[int, NumberParam | SelectParam] = {item.index: item for item in ALL_PARAMS}

# Русские названия и текст из сервисного руководства и книжки пользователя.
# У 4.8, 5.4 и 5.5 в русской главе нет своих абзацев, текст перенесен из английской главы того же мануала.
RU: dict[int, tuple[str, str]] = {
    0: (
        "Значение Pmax",
        "Параметр задает рабочую точку устройства: постоянное давление, которое пользователь устанавливает для системы (максимальное давление). После пуска скорость двигателя регулируется так, чтобы давление было как можно ближе к Pmax. Минимальная разница между Pmax и Pmin составляет 0,3 бара, рекомендуется не меньше 0,5 бара. Если Pmax выше максимального напора насоса, двигатель останавливается при закрытых вентилях: Sirio отключает насос, когда поток падает ниже минимального заданного значения (примерно 2 л/мин), независимо от давления.",
    ),
    1: (
        "Значение Pmin",
        "Давление включения насоса. Если открывается разбор, насос не пускается, пока давление в системе не упадет ниже Pmin. На панели Universal этот регистр называется дельтой пуска относительно Pmax. Минимальная разница между Pmax и Pmin составляет 0,3 бара, рекомендуется не меньше 0,5 бара.",
    ),
    2: (
        "Давление срабатывания защиты от сухого хода",
        "Порог давления для защиты от сухого хода. Если датчик потока отключен, вместе с частотой останова (1.3) этот параметр останавливает насос при отсутствии воды. При длинном всасывании увеличивают и задержку сухого хода (4.1).",
    ),
    3: (
        "Предельное значение давления",
        "Порог максимального давления. Когда он превышен, появляется E9 «Предельное значение давления» и система останавливается. Если сигнал повторяется, проверьте настройку P limit и другие причины высокого давления, например частичное замерзание жидкости.",
    ),
    4: (
        "Значение Pmax2",
        "Вторая рабочая точка. Страница используется, когда вспомогательный контакт или вход платы ввода-вывода стоит в «3 X2». При замыкании этого контакта Sirio регулирует насос по Pmax2, а не по Pmax.",
    ),
    5: (
        "Дельта давления для останова насоса",
        "Дельта давления, по которой насос останавливается. Вместе с задержкой останова (2.5) определяет момент окончания регулирования, когда разбор падает.",
    ),
    6: (
        "Единица измерения",
        "Единица давления на панели и в параметрах давления: BAR или PSI.",
    ),
    10: (
        "Значение Imax",
        "Максимальный ток двигателя в обычной работе. Выше него двигатель останавливается: авария E6, перегрузка. Небольшая перегрузка держится дольше, сильная обрывает работу сразу. Если ток во время работы ниже 0,5 А, Sirio считает двигатель отключенным и останавливает его. Если при включении Imax еще 0,5 А, контроллер остается на этой странице, пока не будет задано рабочее значение. В книжке предел 0,5–9,7 А; на этом Universal шкала выше.",
    ),
    11: (
        "Направление вращения",
        "Меняет направление вращения двигателя без перекладки проводов. Стрелка на панели только ориентир и не показывает фактическое направление. Его проверяет установщик.",
    ),
    12: (
        "Минимальная частота",
        "Минимальная частота, при которой пускается и работает насос. Для трехфазного насоса рекомендуется 25 Гц, для однофазного 30 Гц. Сверьте с данными производителя насоса, при какой минимальной частоте подключенный двигатель еще работает штатно. В книжке то же задается в процентах от максимума: 50% для поверхностного насоса, 60% при погружении 8–10 м, 70% глубже 10 м. Увеличьте, если пуск слишком медленный и на нем сильно падает давление.",
    ),
    13: (
        "Частота останова",
        "Только если датчик потока не включен. Частота, ниже которой двигатель останавливается. Если при регулировании достигнут Pmax, а частота двигателя меньше этого значения, инвертор останавливает насос. При закрытых кранах и постоянном давлении останов идет обычным путем. Если насос не выключается, увеличьте параметр. Если он часто перезапускается, уменьшите.",
    ),
    14: (
        "Номинальная частота двигателя насоса",
        "Номинальная выходная частота инвертора, 50 или 60 Гц, по шильдику насоса. Ошибочный выбор может привести к поломке насоса.",
    ),
    15: (
        "Частота переключения",
        "Частота ШИМ инвертора. Можно выбрать 3, 5 или 10 кГц. Большее значение тише и ровнее ведет двигатель, но греет плату, дает электромагнитные помехи и может повредить двигатель, особенно на длинном кабеле. Невысокие значения рекомендуются для насосов большой и средней мощности, когда Sirio далеко от насоса, и при высокой температуре окружающей среды.",
    ),
    16: (
        "Частотная коррекция",
        "Положительное или отрицательное отклонение максимальной частоты от номинала, от −5 Гц до +5 Гц. Минус ограничивает мощность насоса и помогает избежать перегрузки; снижать частоту можно без дополнительных мер. Плюс немного поднимает производительность, его принимают только после консультации с производителем насоса и с учетом максимального тока инвертора.",
    ),
    17: (
        "Плавный пуск",
        "Включает или выключает плавный пуск. Когда функция включена, насос разгоняется постепенно. Когда выключена, в течение времени 4.7 пуск идет на максимальных оборотах, и только потом начинается регулирование.",
    ),
    20: (
        "Активация датчика потока",
        "Встроенный датчик потока. Заводская настройка — включен: насос останавливается, когда краны закрыты и Sirio видит, что поток через инвертор кончился. Тот же датчик участвует в защите от сухого хода. На грязной воде датчик может врать, и насос перестает останавливаться правильно. Тогда его отключают, и Sirio работает только по давлению и частоте. Нужно точно выставить частоту останова и давление сухого хода, а сразу после Sirio поставить гидроаккумулятор. Давление предварительной закачки бака проверяют периодически.",
    ),
    21: (
        "Режим управления",
        "PRESS: автоматическая работа по давлению в системе. MAN: пуск, останов и скорость с кнопок. В ручном режиме защита от сухого хода и ограничения давления не действуют. Мануал разрешает этот режим только ненадолго и под присмотром квалифицированного персонала. 0-10V: внешняя аналоговая команда.",
    ),
    22: (
        "Функция вспомогательного контакта",
        "1<-> : Sirio как отдельная система или два Sirio в сдвоенной станции. Это заводская настройка. 2<-- : дистанционный пуск и останов. 3 X2 : вторая точка давления, Pmax2.",
    ),
    23: (
        "Функция ввода платы ввода-вывода",
        "Цифровой вход дополнительной платы. OFF: ввод отключен. ERR: при замыкании насос сразу останавливается и на экране «External error». 2<-- : дистанционный пуск и останов; если вспомогательный контакт тоже 2<--, для пуска нужно замкнуть оба контакта (логическое И). 3 X2 : вторая уставка Pmax2; если вспомогательный контакт тоже 3 X2, достаточно замкнуть любой из двух (логическое ИЛИ).",
    ),
    24: (
        "Функция вывода платы ввода-вывода",
        "Цифровой выход дополнительной платы. OFF: вывод отключен. ERR: контакт замыкается при сбое Sirio. P.ON: контакт замыкается, когда насос работает. AUX: дополнительный насос на заданной скорости, когда насос Sirio не покрывает разбор. Контакт замыкается, когда частота на максимуме, а давление упало ниже давления включения. На выходное реле нельзя вешать нагрузку больше 0,3 А.",
    ),
    25: (
        "Задержка останова",
        "Сколько секунд после закрытия всех кранов насос еще работает. Если на слабом потоке он часто перезапускается, увеличьте задержку. Это же уменьшает остановки по сухому ходу, особенно у скважинных насосов и насосов с долгим заполнением. Заводская настройка 10 с.",
    ),
    26: (
        "Интервал автоматического перезапуска",
        "Если на всасывании временно нет воды, Sirio снимает питание с насоса. Здесь задают паузу в минутах до проверки, вернулась ли вода. Успешная проверка снимает ошибку и система снова работает; неуспешная повторяется через тот же интервал. Максимум на этой прошивке 240 минут, рекомендуется 60. В книжке указано до 300 минут.",
    ),
    27: (
        "Число попыток автоматического перезапуска",
        "Сколько раз Sirio пытается пустить насос после остановки по сухому ходу. Когда попытки кончились, система остается выключенной, пока ее не сбросит человек. 0 отключает автоматический перезапуск. Максимум 20. В книжке считаются только короткие пуски, которые не набирают около 2,5 л/мин, и максимум там 10.",
    ),
    28: (
        "Общий автоматический перезапуск",
        "ON: автоматический перезапуск действует на любую ошибку, не только на сухой ход. Неконтролируемый перезапуск после части ошибок, например перегрузки, со временем повреждает систему и сам Sirio. Пользоваться осторожно.",
    ),
    40: (
        "Повышение напряжения",
        "Повышение напряжения при 0 Гц, в процентах, для компенсации потерь в статоре. Если параметр увеличить, при падении частоты напряжение на двигателе растет.",
    ),
    41: (
        "Сухой ход",
        "Задержка перед срабатыванием защиты от сухого хода. Увеличьте ее, если длинный трубопровод на всасывании или у насоса долгое заполнение.",
    ),
    42: (
        "Количество запусков в час",
        "Максимальное число пусков насоса в час, проверка на утечку. Чтобы отключить защиту, удерживайте «−», пока не появится OFF. Выше лимита появляется E11. В книжке тот же сигнал называется «Сильная утечка воды»: если он возникает без реальной утечки, лимит увеличивают. Считаются короткие пуски, которые не набирают около 2,5 л/мин.",
    ),
    43: (
        "Защита от заклинивания",
        "Защита от заклинивания при долгом простое. Если она включена и вода не запрашивается, насос пускается раз в 24 часа, чтобы не закисли механические уплотнения.",
    ),
    44: (
        "Настройка мертвого времени",
        "Пауза между переключениями IGBT одного плеча. Параметр может понадобиться, чтобы поправить среднее выходное напряжение после смены частоты переключения (1.5). Мануал просит подбирать значение вместе с производителем.",
    ),
    45: (
        "Интегральная константа Ki",
        "Интеграл ПИД, который держит постоянное давление. Больше значение — выходное давление ближе к уставке. Слишком большое дает нестабильность: давление постоянно колеблется. В книжке тот же контур описан одним PID: заводское 25, максимум 50. Низкие значения медленнее и плавнее, высокие быстрее.",
    ),
    46: (
        "Пропорциональная константа Kp",
        "Пропорциональная часть ПИД. Больше значение — система чувствительнее к изменению давления. Слишком большое дает избыточное давление или резкий сброс оборотов, и давление колеблется.",
    ),
    47: (
        "Время повышения",
        "Сколько насос работает на максимальной частоте до включения ПИД, если плавный пуск (1.7) выключен. Увеличьте, если насос плохо стартует, особенно однофазный. Уменьшите, если этот разгон нежелательно поднимает давление.",
    ),
    48: (
        "Режим реле N.O. - N.C.",
        "Режим выходного реле платы ввода-вывода: нормально открытое или нормально закрытое. В русской главе отдельного абзаца нет, формулировка из английской главы того же мануала. Если панель показывает ---, регистр не в этих двух положениях. Шагать его оттуда нельзя: до N.O. или N.C. сотни шагов, и реле по пути переключится.",
    ),
    50: (
        "Максимальная температура",
        "Максимальная температура окружающей среды внутри инвертора, при которой срабатывает тепловая защита. Менять только с разрешения производителя: от этого зависит безопасная работа. Снижение частоты (5.2) начинается, когда до этого порога остается меньше 5 °C.",
    ),
    51: (
        "Максимальная температура модуля",
        "Максимальная температура модуля IGBT, при которой срабатывает тепловая защита. Менять только с разрешения производителя. Снижение частоты (5.3) начинается, когда до этого порога остается меньше 5 °C.",
    ),
    52: (
        "Коэффициент снижения частоты по температуре",
        "На сколько снижается максимальная частота насоса на каждый градус, когда температура окружающей среды подходит к пределу 5.0. Снижение включается, когда до порога меньше 5 °C. После порога частота падает на это значение за каждый следующий градус.",
    ),
    53: (
        "Коэффициент снижения частоты по температуре модуля",
        "То же для температуры модуля IGBT и предела 5.1. Снижение включается, когда до порога меньше 5 °C, и дальше частота падает на это значение за каждый градус.",
    ),
    54: (
        "Минимальный поток",
        "В русской главе отдельного абзаца нет, формулировка из английской главы. Порог потока, ниже которого насос останавливается, когда все точки разбора закрыты. Уменьшите, чтобы насос мог работать на совсем малом расходе. Увеличьте, если он не останавливается при полностью закрытой подаче. В книжке типичный порог около 2 л/мин.",
    ),
    55: (
        "Частотная рампа",
        "В русской главе отдельного абзаца нет. На Sirio Universal и Universal XP это скорость разгона при выходе из ожидания в работу. На панели пункт подписан IPM mod.: на Sirio IPM тот же номер зарезервирован под выбор мотора.",
    ),
    56: (
        "Минимальное напряжение",
        "Минимальное напряжение сети. Ниже него срабатывает защита от пониженного напряжения, авария E0.",
    ),
    57: (
        "Максимальное напряжение",
        "Максимальное напряжение сети. Выше него срабатывает защита от повышенного напряжения, авария E1. От этого значения считается уровень примерно на 30 В ниже: выше него насос плавно сбрасывает обороты, чтобы не было броска на шине постоянного тока.",
    ),
    59: (
        "Отладка параметров",
        "Выбирает внутреннюю переменную и показывает ее, чтобы смотреть, как она меняется во время работы. Для обслуживания.",
    ),
}
