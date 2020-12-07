import os
import re
from types import FunctionType

from xml.dom import minidom

def try_convert_to_number(value):
    try:
        return float(value)
    except:
        return value

class converter():
    def __init__(self):
        self.__root_doc = None
        self.__doc = None
        self.__properties = {}
        self.__macros = {}
        self.__file_dir = ""

    def run(self, input_file):
        self.__file_dir = os.path.dirname(input_file)
        self.__load(input_file, root=True)
        
        self.__save()

    def __load(self, file_name, root=False):
        doc = minidom.parse(file_name).documentElement
        if root:
            self.__root_doc = doc
        self.__load_includes(doc)
        self.__run(doc)
        

    def __run(self, node):
        for e in node.childNodes:
            if e.nodeType == minidom.Node.ELEMENT_NODE:
                if "xacro:" in e.tagName:
                    cmd = e.tagName[6:]
                    if cmd == "macro":
                        self.__load_macros(e)
                    elif cmd == "property":
                        self.__load_properties(e)
                    else:
                        self.__run_macro(e, cmd)
                else:
                    for k, v in e.attributes.items():
                        replace , value = self.__eval_text(v)
                        if replace:
                            e.setAttribute(k, value)
            if e.nodeType == minidom.Node.TEXT_NODE:
                if len(e.nodeValue.strip()) > 0:
                    replace , value = self.__eval_text(e.nodeValue)
                    e.nodeValue = value

            if e.nodeType == minidom.Node.ELEMENT_NODE:
                if "xacro:" not in e.tagName:
                    self.__run(e)

    def __run_macro(self, node, cmd):
        kwargs = {}
        for k,v in node.attributes.items():
            kwargs[k] = v
        data = self.__macros[cmd](**kwargs)
        _, data = self.__eval_text(data, kwargs)
        parent = node.parentNode
        parent.removeChild(node)
        inner = minidom.parseString(data).documentElement
        parent.appendChild(inner)

    def __load_macros(self, node):
        name = node.getAttribute("name")
        params = node.getAttribute("params")
        for e in node.childNodes:
            if e.nodeType == minidom.Node.ELEMENT_NODE:
                break
        params_list = (",".join(params.strip().split()))
        f_body = e.toxml()
        f_func_string = f'def {name}({params_list}): return """{f_body}"""'
        f_code = compile(f_func_string, "<string>", "exec")
        f_func = FunctionType(f_code.co_consts[0], globals(), name)
        self.__macros[name] = f_func
        parent = node.parentNode
        parent.removeChild(node)

    def __load_includes(self, node):
        elements = node.getElementsByTagNameNS("http://dd", "include")
        for node in elements:
            if not node.hasAttribute("uri"):
                raise Exception("include uri not declare")
            pattern = re.compile(r'file://(.*?)', re.S)
            new_value = re.sub(pattern, lambda x: x.group(1), node.getAttribute("uri"))
            
            file_name = os.path.join(self.__file_dir, new_value)
            parent = node.parentNode
            parent.removeChild(node)
            self.__load(file_name)

    def __load_properties(self, node):
        name = node.getAttribute("name")
        value = node.getAttribute("value")
        self.__properties[name] = try_convert_to_number(value)
        parent = node.parentNode
        parent.removeChild(node)
        
    def __eval_text(self, value, kwargs={}):
        subsitute = lambda o: str(eval(o.group(1), self.__properties, kwargs))
        pattern = re.compile(r'[$][{](.*?)[}]', re.S)
        new_value = re.sub(pattern, subsitute, value)
        return new_value!=value, new_value

    def __save(self):
        dir_name = os.path.dirname(__file__)
        file_name = os.path.join(dir_name, "../dest_sdf")
        file_name = os.path.join(file_name, "property.sdf")
        with (open(file_name, "w")) as f:
            data = self.__root_doc.toxml()
            f.writelines(data)

def main():
    dir_name = os.path.dirname(__file__)
    file_name = os.path.join(dir_name, "../source_example")
    file_name = os.path.join(file_name, "macro.xacro")
    con = converter()
    con.run(file_name)

if __name__ == "__main__":
    main()