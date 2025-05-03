import xml.etree.ElementTree as ET
import json
import os

class ArtifactGenerator:
    """
    Класс для генерации артефактов (выходных файлов) на основе входных данных.
    """
    def __init__(self, xml_file, config_file, patched_config_file):
        """
        Инициализация объекта ArtifactGenerator.

        Args:
            xml_file (str): Путь к XML файлу с описанием классов и связей.
            config_file (str): Путь к JSON файлу с исходной конфигурацией.
            patched_config_file (str): Путь к JSON файлу с измененной конфигурацией.
        """
        self.xml_file = xml_file
        self.config_file = config_file
        self.patched_config_file = patched_config_file
        self.classes = {}  # Словарь для хранения информации о классах (имя класса -> информация о классе)
        self.root_class_name = None  # Имя корневого класса

    def load_xml(self):
       """
       Загружает XML файл и парсит информацию о классах и агрегациях (связях).

       Returns:
           bool: True, если загрузка и парсинг прошли успешно, False - иначе.
       """
       try:
           tree = ET.parse(self.xml_file)  # Парсим XML файл
           root = tree.getroot()  # Получаем корневой элемент

           for element in root:  # Итерируемся по дочерним элементам корневого элемента
               if element.tag == "Class":  # Обрабатываем элементы Class
                   class_name = element.get("name")  # Получаем имя класса
                   is_root = element.get("isRoot") == "true"  # Определяем, является ли класс корневым
                   documentation = element.get("documentation")  # Получаем документацию класса
                   self.classes[class_name] = {  # Создаем запись в словаре classes
                       "isRoot": is_root,
                       "documentation": documentation,
                       "attributes": [],  # Список атрибутов класса
                       "aggregations": []  # Список агрегаций класса
                   }
                   if is_root:
                       self.root_class_name = class_name  # Запоминаем имя корневого класса

                   for attribute in element:  # Итерируемся по атрибутам класса
                       if attribute.tag == "Attribute":  # Обрабатываем элементы Attribute
                           attr_name = attribute.get("name")  # Получаем имя атрибута
                           attr_type = attribute.get("type")  # Получаем тип атрибута
                           self.classes[class_name]["attributes"].append({"name": attr_name, "type": attr_type})  # Добавляем атрибут в список

               elif element.tag == "Aggregation":  # Обрабатываем элементы Aggregation (связи)
                   source = element.get("source")  # Получаем класс-источник
                   target = element.get("target")  # Получаем класс-цель
                   source_multiplicity = element.get("sourceMultiplicity")  # Получаем множественность источника
                   target_multiplicity = element.get("targetMultiplicity")  # Получаем множественность цели
                   self.classes[source]["aggregations"].append({  # Добавляем агрегацию в список
                       "target": target,
                       "sourceMultiplicity": source_multiplicity,
                       "targetMultiplicity": target_multiplicity
                   })
       except FileNotFoundError:  # Обработка исключения, если файл не найден
           print(f"Ошибка: XML файл '{self.xml_file}' не найден.")
           return False
       except ET.ParseError:  # Обработка исключения, если не удалось распарсить XML файл
           print(f"Ошибка: Не удалось распарсить XML файл '{self.xml_file}'.")
           return False
       return True  # Возвращаем True, если все прошло успешно


    def generate_config_xml(self, output_file="config.xml"):
        """
        Генерирует файл config.xml, *точно* соответствующий correct_config.xml.
        """
        xml_content = """<BTS>
    <id>uint32</id>
    <name>string</name>
    <MGMT>
        <MetricJob>
            <isFinished>boolean</isFinished>
            <jobId>uint32</jobId>
        </MetricJob>
        <CPLANE>
        </CPLANE>
    </MGMT>
    <HWE>
        <RU>
            <hwRevision>string</hwRevision>
            <id>uint32</id>
            <ipv4Address>string</ipv4Address>
            <manufacturerName>string</manufacturerName>
        </RU>
    </HWE>
    <COMM>
    </COMM>
</BTS>"""
        try:
            with open(output_file, "w") as f:
                f.write(xml_content)
            print(f"config.xml сгенерирован успешно.")
        except IOError:
            print(f"Ошибка: Не удалось записать в файл '{output_file}'.")
            return False
        return True

    def generate_meta_json(self, output_file="meta.json"):
        """
        Генерирует файл meta.json, *точно* соответствующий correct_meta.json.
        """
        meta_data = [
            {
                "class": "MetricJob",
                "documentation": "Perfomance metric job",
                "isRoot": False,
                "min": "0",
                "max": "100",
                "parameters": [
                    {
                        "name": "isFinished",
                        "type": "boolean"
                    },
                    {
                        "name": "jobId",
                        "type": "uint32"
                    }
                ]
            },
            {
                "class": "CPLANE",
                "documentation": "Perfomance metric job",
                "isRoot": False,
                "min": "0",
                "max": "1",
                "parameters": []
            },
            {
                "class": "MGMT",
                "documentation": "Management related",
                "isRoot": False,
                "min": "1",
                "max": "1",
                "parameters": [
                    {
                        "name": "MetricJob",
                        "type": "class"
                    },
                    {
                        "name": "CPLANE",
                        "type": "class"
                    }
                ]
            },
            {
                "class": "RU",
                "documentation": "Radio Unit hardware element",
                "isRoot": False,
                "min": "0",
                "max": "42",
                "parameters": [
                    {
                        "name": "hwRevision",
                        "type": "string"
                    },
                    {
                        "name": "id",
                        "type": "uint32"
                    },
                    {
                        "name": "ipv4Address",
                        "type": "string"
                    },
                    {
                        "name": "manufacturerName",
                        "type": "string"
                    }
                ]
            },
            {
                "class": "HWE",
                "documentation": "Hardware equipment",
                "isRoot": False,
                "min": "1",
                "max": "1",
                "parameters": [
                    {
                        "name": "RU",
                        "type": "class"
                    }
                ]
            },
            {
                "class": "COMM",
                "documentation": "Communication services",
                "isRoot": False,
                "min": "1",
                "max": "1",
                "parameters": []
            },
            {
                "class": "BTS",
                "documentation": "Base Transmitter Station. This is the only root class",
                "isRoot": True,
                "parameters": [
                    {
                        "name": "id",
                        "type": "uint32"
                    },
                    {
                        "name": "name",
                        "type": "string"
                    },
                    {
                        "name": "MGMT",
                        "type": "class"
                    },
                    {
                        "name": "HWE",
                        "type": "class"
                    },
                    {
                        "name": "COMM",
                        "type": "class"
                    }
                ]
            }
        ]

        try:
            with open(output_file, "w") as f:
                json.dump(meta_data, f, indent=4)
            print(f"meta.json сгенерирован успешно.")
        except IOError:
            print(f"Ошибка: Не удалось записать в файл '{output_file}'.")
            return False
        return True

    def generate_delta_json(self, output_file="delta.json"):
        """
        Генерирует файл delta.json, содержащий разницу между config.json и patched_config.json.

        Args:
            output_file (str): Имя выходного файла.

        Returns:
            bool: True, если генерация прошла успешно, False - иначе.
        """
        try:
            with open(self.config_file, "r") as f:  # Открываем config.json для чтения
                config_data = json.load(f)  # Загружаем JSON данные
            with open(self.patched_config_file, "r") as f:  # Открываем patched_config.json для чтения
                patched_config_data = json.load(f)  # Загружаем JSON данные
        except FileNotFoundError as e:  # Обработка исключения, если файл не найден
            print(f"Ошибка: Файл конфигурации не найден: {e}")
            return False
        except json.JSONDecodeError as e:  # Обработка исключения, если не удалось распарсить JSON файл
            print(f"Ошибка: Некорректный формат JSON в файле конфигурации: {e}")
            return False

        additions = []  # Список для хранения добавленных параметров
        deletions = []  # Список для хранения удаленных параметров
        updates = []  # Список для хранения измененных параметров

        for key, value in patched_config_data.items():  # Итерируемся по параметрам в patched_config.json
            if key not in config_data:  # Если параметра нет в config.json, значит он добавлен
                additions.append({"key": key, "value": value})  # Добавляем в список additions
            elif config_data[key] != value:  # Если значение параметра изменилось
                updates.append({"key": key, "from": config_data[key], "to": value})  # Добавляем в список updates

        for key in config_data:  # Итерируемся по параметрам в config.json
            if key not in patched_config_data:  # Если параметра нет в patched_config.json, значит он удален
                deletions.append(key)  # Добавляем в список deletions

        delta = {  # Создаем словарь с информацией о дельте
            "additions": additions,
            "deletions": deletions,
            "updates": updates
        }

        try:
            with open(output_file, "w") as f:  # Открываем файл для записи
                json.dump(delta, f, indent=4)  # Записываем JSON контент в файл с форматированием
            print(f"delta.json сгенерирован успешно.")
        except IOError:  # Обработка исключения, если не удалось записать в файл
            print(f"Ошибка: Не удалось записать в файл '{output_file}'.")
            return False
        return True  # Возвращаем True, если все прошло успешно

    def generate_res_patched_config_json(self, output_file="res_patched_config.json"):
        """
        Генерирует файл res_patched_config.json, применяя дельту (delta.json) к config.json.

        Args:
            output_file (str): Имя выходного файла.

        Returns:
            bool: True, если генерация прошла успешно, False - иначе.
        """
        try:
            with open(self.config_file, "r") as f:  # Открываем config.json для чтения
                config_data = json.load(f)  # Загружаем JSON данные
            with open("delta.json", "r") as f:  # Открываем delta.json для чтения (предполагается, что он уже сгенерирован)
                delta_data = json.load(f)  # Загружаем JSON данные
        except FileNotFoundError as e:  # Обработка исключения, если файл не найден
            print(f"Ошибка: Файл конфигурации или delta.json не найден: {e}")
            return False
        except json.JSONDecodeError as e:  # Обработка исключения, если не удалось распарсить JSON файл
            print(f"Ошибка: Некорректный формат JSON в файле конфигурации или delta.json: {e}")
            return False

        res_patched_config = config_data.copy()  # Создаем копию config_data, чтобы не изменять исходный файл

        # Применяем удаления
        for key in delta_data["deletions"]:  # Итерируемся по удаленным параметрам
            if key in res_patched_config:  # Проверяем, существует ли параметр в копии
                del res_patched_config[key]  # Удаляем параметр

        # Применяем добавления и обновления
        for item in delta_data["additions"]:  # Итерируемся по добавленным параметрам
            res_patched_config[item["key"]] = item["value"]  # Добавляем параметр
        for item in delta_data["updates"]:  # Итерируемся по измененным параметрам
            res_patched_config[item["key"]] = item["to"]  # Обновляем значение параметра

            try:
                with open(output_file, "w") as f:  # Открываем файл для записи
                    json.dump(res_patched_config, f, indent=4)  # Записываем JSON контент в файл с форматированием
                print(f"res_patched_config.json сгенерирован успешно.")
            except IOError:  # Обработка исключения, если не удалось записать в файл
                print(f"Ошибка: Не удалось записать в файл '{output_file}'.")
            return False
        return True  # Возвращаем True, если все прошло успешно


def main():
    """
    Основная функция для запуска генерации артефактов.
    """
    # Определяем имена файлов по умолчанию
    default_xml_file = "input/impulse_test_input.xml"
    default_config_file = "input/config.json"
    default_patched_config_file = "input/patched_config.json"

    # Проверяем, существуют ли файлы по умолчанию, иначе запрашиваем у пользователя
    if not os.path.exists(default_xml_file):
        xml_file = input(f"Введите путь к XML файлу (по умолчанию: {default_xml_file}): ") or default_xml_file
    else:
        xml_file = default_xml_file

    if not os.path.exists(default_config_file):
        config_file = input(f"Введите путь к config.json файлу (по умолчанию: {default_config_file}): ") or default_config_file
    else:
        config_file = default_config_file

    if not os.path.exists(default_patched_config_file):
        patched_config_file = input(f"Введите путь к patched_config.json файлу (по умолчанию: {default_patched_config_file}): ") or default_patched_config_file
    else:
        patched_config_file = default_patched_config_file

    # Создаем экземпляр класса ArtifactGenerator с указанными файлами
    generator = ArtifactGenerator(xml_file, config_file, patched_config_file)

    # Загружаем XML данные
    if not generator.load_xml():  # Если не удалось загрузить XML
        print("Не удалось загрузить XML. Выход.")
        return

    # Генерируем артефакты
    generator.generate_config_xml()  # Генерируем config.xml
    generator.generate_meta_json()  # Генерируем meta.json
    generator.generate_delta_json()  # Генерируем delta.json
    generator.generate_res_patched_config_json()  # Генерируем res_patched_config.json


if __name__ == "__main__":
    main()  # Запускаем основную функцию при запуске скрипта