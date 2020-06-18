from PdfConverter import PdfConverter


class Variable:
    token_range = ["-", "TO"]
    token_dp = ["±"]
    has_range = has_dp = False
    acceptable_types = first_value = dp_first_value = second_value = dp_second_value = metric = None

    def origen_string(self, string):
        self.string_pdf = string

    def __init__(self, type_value):
        self.acceptable_types = type_value

    def get_acceptable_type(self):
        return self.acceptable_types

    def set_value(self, value):
        if self.first_value is None:
            if not isinstance(value, str):
                self.first_value = value
                return True
            else:
                return False

        if value in self.token_dp:
            self.has_dp = True
            return True

        if value in self.token_range:
            self.has_range = True
            return True

        if value in self.acceptable_types:
            self.metric = value
            return True

        if self.has_range:
            if not isinstance(value, str):
                self.second_value = value
                return True
            else:
                return False

        if self.has_dp:
            if self.second_value is None:
                if not isinstance(value, str):
                    self.dp_first_value = value
                    return True
                else:
                    return False
            else:
                if not isinstance(value, str):
                    self.dp_second_value = value
                    return True
                else:
                    return False

        return False

    def is_complete(self):
        return self.metric is not None

    def __str__(self):
        str_value = ""
        if self.has_range:
            if self.has_dp:
                str_value = str(self.first_value) + "±" + str(self.dp_first_value) + " TO " + str(self.second_value) +\
                            "±" + str(self.dp_second_value) + " " + self.metric
            else:
                str_value = str(self.first_value) + " TO " + str(self.second_value) + " " + self.metric
        else:
            if self.has_dp:
                str_value = str(self.first_value) + "±" + str(self.dp_first_value) + " " + self.metric
            else:
                str_value = str(self.first_value) + " " + self.metric

        return str_value


class MinerArticle:

    pdf = ""
    hardness = friability = desintegration = {}

    def __init__(self, str_file):
        self.pdf = self.__read_pdf(str_file)

        self.hardness = self.__get_variable_from_pdf("HARDNESS", ["N", "KGF", "KG/CM²", "KG/CM", "KG/CM2"])
        self.friability = self.__get_variable_from_pdf("FRIABILITY", ["%"])
        self.desintegration = self.__get_variable_from_pdf("DISINTEGRATION", ["MIN", "S", "SEC", "SECONDS"])

    def __str__(self):
        str_print = "Propriedade Farmacêuticas: Hardness \n"
        str_print += self.__print_possible_variable(self.hardness)
        # str_print.append(self.hardness)
        str_print += "\n Propriedade Farmacêuticas: Friability \n"
        str_print += self.__print_possible_variable(self.friability)
        # str_print.append(self.friability)
        str_print += "\n Propriedade Farmacêuticas: Disintegration \n"
        str_print += self.__print_possible_variable(self.desintegration)
        # str_print.append(self.desintegration)
        return str_print

    @staticmethod
    def __print_possible_variable(variable):
        str_result = ""
        lista_resul = []
        for valor in variable["valores"]:
            lista_resul.append(str(valor))

        lista_resul.sort(key=lambda tup: tup[1])
        for values in lista_resul:
            str_result += str(values) + "\n"

        if str_result == "":
            return "Variable not found."

        return str_result

    # ler pdf
    @staticmethod
    def __read_pdf(str_file):
        pdf_converter = PdfConverter(file_path=str_file)
        pdf_converter.extract_text()
        string_pdf = str(pdf_converter.convert_pdf_to_txt().upper())

        return string_pdf

    def __get_variable_from_pdf(self, variable, token):
        detalhes_pagina = {}
        detalhes_pagina["posicoes_token"] = self.__substring_indexes(variable)
        detalhes_pagina["substrings"] = self.__get_substring_end_line(detalhes_pagina["posicoes_token"])
        detalhes_pagina["valores"] = self.__get_number_from_string(detalhes_pagina["substrings"], token)
        return detalhes_pagina

    def __substring_indexes(self, substring):
        position = []

        last_found = -1  # Begin at -1 so the next position to search from is 0
        while True:
            # Find next index of substring, by starting after its last known position
            # teste = string.find(substring)
            last_found = self.pdf.find(substring, last_found + 1)

            if last_found == -1:
                break  # All occurrences have been found
            else:
                position.append(last_found)

        return position

    def __get_substring_end_line(self, posicoes):
        substrings = []
        last_position = 0
        for i in posicoes:
            position = self.pdf.find(". ", i + 1)
            position2 = self.pdf.find(".\n", i + 1)

            if position != -1 and position2 != -1:
                position = min(position, position2)
            elif position == -1 and position2 != -1:
                position = position2
            elif position != -1 and position2 == -1:
                position = position
            else:
                position = None

            if position is None:
                continue

            str_value = self.pdf[i:position]
            if i < last_position:
                continue
            else:
                substrings.append(str_value)
                last_position = position

        return substrings

    @staticmethod
    def replace_multiple(main_string, to_be_replaces):
        # Iterate over the strings to be replaced
        for elem in main_string:
            # Check if string is in the main string
            if elem in to_be_replaces:
                # Replace the string
                main_string = main_string.replace(elem, " " + elem)

        return main_string

    def replace_spacial_cases(self, string, type_value):
        dicionario = {',': '', '(': '', ')': '', '–': ' – ', 'TO': ' TO ', '±': ' ± '}
        for chave, substituto in dicionario.items():
            string = string.replace(chave, substituto)
        return string

    @staticmethod
    def get_value(string):
        valor = None
        try:
            valor = int(string)
        except ValueError:
            try:
                valor = float(string)
            except ValueError:
                valor = None
        return valor

    def __get_number_from_string(self, substrings, token_key):
        valores = []
        for string in substrings:
            str_text = string.upper().split()
            variable = Variable(token_key)

            for value in str_text:
                val = self.get_value(value)

                if val is not None:
                    variable.set_value(val)
                else:
                    new_string = self.replace_spacial_cases(value, variable.get_acceptable_type()).split()

                    for new_value in new_string:
                        number = self.get_value(new_value)

                        if number is None:
                            number = new_value

                        if not variable.set_value(number):
                            variable = Variable(token_key)

                if variable.is_complete():
                    variable.origen_string(string)
                    valores.append(variable)
                    variable = Variable(token_key)
        return valores
