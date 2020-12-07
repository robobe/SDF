import os
import re

from xml.dom import minidom

def try_convert_to_number(value):
    try:
        return float(value)
    except:
        return value

class converter():
    def __init__(self, input_file):
        self.__doc = None
        self.__properties = {}
        self.__load(input_file)

    def __load(self, file_name):
        self.__doc = minidom.parse(file_name).documentElement
        self.__parse_properties()
        
        self.__save()
        # print(dir(self.__doc))

    def __parse_properties(self):
        elements = self.__doc.getElementsByTagNameNS("http://dd", "property")
        for node in elements:
            name = node.getAttribute("name")
            value = node.getAttribute("value")
            self.__properties[name] = try_convert_to_number(value)
            parent = node.parentNode
            parent.removeChild(node)

        self.__subsitute()

    def __sub_txt(self, obj):
        key = obj.group(1)
        data = eval(key, self.__properties)
        return str(data)
        

    def __eval_text(self, value):
        pattern = re.compile(r'[$][{](.*?)[}]', re.S)
        new_value = re.sub(pattern, self.__sub_txt, value)
        return new_value!=value, new_value

    def __recursively(self, node):
        for e in node.childNodes:
            if e.nodeType == minidom.Node.ELEMENT_NODE:
                for k, v in e.attributes.items():
                    replace , value = self.__eval_text(v)
                    if replace:
                        e.setAttribute(k, value)

            self.__recursively(e)

    def __subsitute(self):
        self.__recursively(self.__doc)


    def __save(self):
        dir = os.path.dirname(__file__)
        file_name = os.path.join(dir, "../dest_sdf")
        file_name = os.path.join(file_name, "property.sdf")
        with (open(file_name, "w")) as f:
            self.__doc.writexml(f)

def main():
    dir = os.path.dirname(__file__)
    file_name = os.path.join(dir, "../source_example")
    file_name = os.path.join(file_name, "property.xacro")
    con = converter(file_name)

if __name__ == "__main__":
    main()