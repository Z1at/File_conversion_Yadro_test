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
            tree = ET.parse(self.xml_file)
            root = tree.getroot()

            for element in root:
                if element.tag == "Class": # Обрабатываем элементы Class
                    class_name = element.get("name")
                    is_root = element.get("isRoot") == "true"
                    documentation = element.get("documentation")
                    self.classes[class_name] = {
                        "isRoot": is_root,
                        "documentation": documentation,
                        "attributes": [],
                        "aggregations": []
                    }
                    if is_root:
                        self.root_class_name = class_name

                    for attribute in element:
                        if attribute.tag == "Attribute":  # Обрабатываем элементы Attribute
                            attr_name = attribute.get("name")
                            attr_type = attribute.get("type")
                            self.classes[class_name]["attributes"].append({"name": attr_name, "type": attr_type})

                elif element.tag == "Aggregation":  # Обрабатываем элементы Aggregation (связи)
                    source = element.get("source")
                    target = element.get("target")
                    source_multiplicity = element.get("sourceMultiplicity")
                    target_multiplicity = element.get("targetMultiplicity")
                    self.classes[source]["aggregations"].append({
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
        Генерирует файл config.xml на основе загруженной модели.

        Args:
            output_file (str): Имя выходного файла.

        Returns:
            bool: True, если генерация прошла успешно, False - иначе.
        """

        if not self.classes or not self.root_class_name:
            print("Ошибка: XML данные не загружены. Сначала вызовите load_xml().")
            return False

        def create_element(class_name, indent=1):
            """
            Рекурсивная функция для создания XML элемента для класса.

            Args:
                class_name (str): Имя класса.
                indent (int): Уровень отступа.

            Returns:
                str: XML строка, представляющая элемент.
            """

            indent_str = "    " * indent
            element_str = f"{indent_str}<{class_name}>\n"  # Открывающий тег элемента
            class_data = self.classes[class_name]  # Получаем данные класса
            for attribute in class_data["attributes"]:
                element_str += f"{indent_str}    <{attribute['name']}>{attribute['type']}</{attribute['name']}>\n"

            for aggregation in class_data["aggregations"]:
                target_class = aggregation["target"]
                element_str += create_element(target_class, indent + 1)

            element_str += f"{indent_str}</{class_name}>\n"  # Закрывающий тег элемента
            return element_str

        xml_content = "<BTS>\n"  # начинаем с <BTS> - корневой элемент
        root_class_data = self.classes[self.root_class_name]  # Получаем данные корневого класса

        for attribute in root_class_data["attributes"]:  # Добавляем атрибуты корневого класса
            xml_content += f"    <{attribute['name']}>{attribute['type']}</{attribute['name']}>\n"

        for aggregation in root_class_data["aggregations"]:
            target_class = aggregation["target"]
            xml_content += create_element(target_class, 1)

        xml_content += "</BTS>\n"  # заканчиваем с </BTS>

        try:
            with open(output_file, "w") as f:
                f.write(xml_content)
            print(f"config.xml сгенерирован успешно.")
        except IOError:  # Обработка исключения, если не удалось записать в файл
            print(f"Ошибка: Не удалось записать в файл '{output_file}'.")
            return False

        return True  # Возвращаем True, если все прошло успешно

    def generate_meta_json(self, output_file="meta.json"):
        """
        Генерирует файл meta.json на основе загруженной модели.

        Args:
            output_file (str): Имя выходного файла.

        Returns:
            bool: True, если генерация прошла успешно, False - иначе.
        """

        if not self.classes:
            print("Ошибка: XML данные не загружены. Сначала вызовите load_xml().")
            return False

        meta_data = []  # Список для хранения мета-информации о классах
        for class_name, class_data in self.classes.items():
            class_info = {
                "class": class_name,
                "documentation": class_data["documentation"],
                "isRoot": class_data["isRoot"],
                "parameters": []
            }

            min_multiplicity = None
            max_multiplicity = None

            for agg_data in self.classes[class_name]["aggregations"]:
                multiplicity = agg_data["sourceMultiplicity"]
                if ".." in multiplicity:
                    min_multiplicity, max_multiplicity = multiplicity.split("..")
                else:
                    min_multiplicity = max_multiplicity = multiplicity
                break

            class_info["min"] = min_multiplicity if min_multiplicity else "1"
            class_info["max"] = max_multiplicity if max_multiplicity else "1"

            for attribute in class_data["attributes"]:
                class_info["parameters"].append({"name": attribute["name"], "type": attribute["type"]})

            for aggregation in class_data["aggregations"]:
                target_class = aggregation["target"]
                class_info["parameters"].append({"name": target_class, "type": "class"})
            meta_data.append(class_info)

        try:
            with open(output_file, "w") as f:
                json.dump(meta_data, f, indent=4)
            print(f"meta.json сгенерирован успешно.")
        except IOError:  # Обработка исключения, если не удалось записать в файл
            print(f"Ошибка: Не удалось записать в файл '{output_file}'.")
            return False

        return True  # Возвращаем True, если все прошло успешно

    def generate_delta_json(self, output_file="delta.json"):
        """
        Генерирует файл delta.json, содержащий разницу между config.json и patched_config.json.

        Args:
            output_file (str): Имя выходного файла.

        Returns:
            bool: True, если генерация прошла успешно, False - иначе.
        """

        try:
            with open(self.config_file, "r") as f:
                config_data = json.load(f)
            with open(self.patched_config_file, "r") as f:
                patched_config_data = json.load(f)
        except FileNotFoundError as e:  # Обработка исключения, если файл не найден
            print(f"Ошибка: Файл конфигурации не найден: {e}")
            return False
        except json.JSONDecodeError as e:  # Обработка исключения, если не удалось распарсить JSON файл
            print(f"Ошибка: Некорректный формат JSON в файле конфигурации: {e}")
            return False

        additions = []  # Список для хранения добавленных параметров
        deletions = []  # Список для хранения удаленных параметров
        updates = []  # Список для хранения измененных параметров

        for key, value in patched_config_data.items():
            if key not in config_data:
                additions.append({"key": key, "value": value})
            elif config_data[key] != value:
                updates.append({"key": key, "from": config_data[key], "to": value})

        for key in config_data:
            if key not in patched_config_data:
                deletions.append(key)

        delta = {  # Создаем словарь с информацией о дельте
            "additions": additions,
            "deletions": deletions,
            "updates": updates
        }

        try:
            with open(output_file, "w") as f:
                json.dump(delta, f, indent=4)
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
            with open(self.config_file, "r") as f:
                config_data = json.load(f)
            with open("delta.json", "r") as f:
                delta_data = json.load(f)
        except FileNotFoundError as e:  # Обработка исключения, если файл не найде
            print(f"Ошибка: Файл конфигурации или delta.json не найден: {e}")
            return False
        except json.JSONDecodeError as e:  # Обработка исключения, если не удалось распарсить JSON файл
            print(f"Ошибка: Некорректный формат JSON в файле конфигурации или delta.json: {e}")
            return False

        res_patched_config = config_data.copy()  # Создаем копию config_data, чтобы не изменять исходный файл

        for key in delta_data["deletions"]:
            if key in res_patched_config:
                del res_patched_config[key]

        for item in delta_data["additions"]:
            res_patched_config[item["key"]] = item["value"]
        for item in delta_data["updates"]:
            res_patched_config[item["key"]] = item["to"]

        try:
            with open(output_file, "w") as f:
                json.dump(res_patched_config, f, indent=4)
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
    default_xml_file = "impulse_test_input.xml"
    default_config_file = "config.json"
    default_patched_config_file = "patched_config.json"

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
    main()
