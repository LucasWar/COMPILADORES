from Error import Error
import abc
from TValue import *
from Consts import Consts
from Memory import MemoryManager

class Visitor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def visit(self, operator): operator.fail(Error(f"{Error.runTimeError}: Nenhum metodo visit para a classe '{Error.classNameOf(self)}' foi definido!"))

    def __repr__(self): (f"TODO: implements __repr__ of '{Error.classNameOf(self)}' class")

class NoNumber(Visitor):
    def __init__(self, tok):
        self.tok = tok

    def visit(self, operator):
        return operator.success(TNumber(self.tok.value).setMemory(operator))

    def __repr__(self):
        return f'{self.tok}'

class NoOpUnaria(Visitor):
    def __init__(self, opTok, node):
        self.opTok = opTok
        self.node = node

    def visit(self, operator):
        num = operator.registry(self.node.visit(operator))
        if operator.error: return operator
        error = None
        if self.opTok.type == Consts.MINUS:
            num, error = num.mult(TNumber(-1))
        if error:
            return operator.fail(error)
        else:
            return operator.success(num)

    def __repr__(self):
        return f'({self.opTok}, {self.node})'

class NoOpBinaria(Visitor):
    def __init__(self, leftNode, opTok, rightNode):
        self.noEsq = leftNode
        self.opTok = opTok
        self.noDir = rightNode

    def __repr__(self):
        return f'({self.noEsq}, {self.opTok}, {self.noDir})'

    @staticmethod
    def Perform(GVar1, ops, GVar2=None):
        if GVar2==None: GVar2 = GVar1
        ast = GVar1.GetParserManager()
        op_bin_ou_esq = ast.registry(GVar1.Rule())
        if ast.error: return ast
        while GVar1.CurrentToken().type in ops:
            token_operador = GVar1.CurrentToken()
            GVar1.NextToken()
            lado_direito = ast.registry(GVar2.Rule())
            if ast.error: return ast
            op_bin_ou_esq = NoOpBinaria(op_bin_ou_esq, token_operador, lado_direito)
        return ast.success(op_bin_ou_esq)

    def visit(self, operator):
        esq = operator.registry(self.noEsq.visit(operator))
        if operator.error: return operator
        dir = operator.registry(self.noDir.visit(operator))
        if operator.error: return operator

        if self.opTok.type == Consts.PLUS:
            result, error = esq.add(dir)
        elif self.opTok.type == Consts.MINUS:
            result, error = esq.sub(dir)
        elif self.opTok.type == Consts.MUL:
            result, error = esq.mult(dir)
        elif self.opTok.type == Consts.DIV:
            result, error = esq.div(dir)
        elif self.opTok.type == Consts.POW:
            result, error = esq.pow(dir)

        if error:
            return operator.fail(error)
        else:
            return operator.success(result)

class NoVarAssign(Visitor):
    def __init__(self, varNameTok, valueNode):
        self.varNameTok = varNameTok
        self.valueNode = valueNode

    def visit(self, operator):
        varName = self.varNameTok.value
        value = operator.registry(self.valueNode.visit(operator))
        if operator.error: return operator

        operator.symbolTable.set(varName, value)
        return operator.success(value)

    def __repr__(self):
        return f'({self.varNameTok}, {self.valueNode})'

class NoVarAccess(Visitor):
    def __init__(self, varNameTok):
        self.varNameTok = varNameTok

    def visit(self, operator):
        varName = self.varNameTok.value
        value = operator.symbolTable.get(varName)

        if not value: return operator.fail(Error(f"{Error.runTimeError}: '{varName}' nao esta definido"))

        value = value.copy()
        return operator.success(value)

    def __repr__(self):
        return f'({self.varNameTok})'

class NoString(Visitor):
    def __init__(self, tok):
        self.tok = tok

    def visit(self, operator):
        return operator.success(TString(self.tok.value).setMemory(operator))

    def __repr__(self):
        return f'{self.tok}'

class NoList(Visitor):
    def __init__(self, elements):
        self.elements = elements

    def visit(self, operator):
        lValue = [operator.registry(element_node.visit(operator)) for element_node in self.elements]
        return operator.success(TList(lValue).setMemory(operator))

    def __repr__(self):
        return f'{self.elements}'

class NoTupla(Visitor):
    def __init__(self, elements):
        self.elements = elements

    def visit(self, operator):
        tupleValues = [operator.registry(element_node.visit(operator)) for element_node in self.elements]
        return operator.success(TTuple(tupleValues).setMemory(operator))

    def __repr__(self):
        return f'({", ".join(map(str, self.elements))})'

class NoDict(Visitor):
    def __init__(self, key_value_pairs):
        self.key_value_pairs = key_value_pairs  # Lista de pares (chave, valor)

    def visit(self, operator):
        dict_value = {}
        for key_node, value_node in self.key_value_pairs:
            key = operator.registry(key_node.visit(operator))
            if operator.error: return operator
            value = operator.registry(value_node.visit(operator))
            if operator.error: return operator
            dict_value[key] = value
        return operator.success(TDict(dict_value).setMemory(operator))

    def __repr__(self):
        return f"NoDict({self.key_value_pairs})"


class NoMethodCall(Visitor):
    def __init__(self, object_node, method_name, params, value = None):
        self.object_node = object_node
        self.method_name = method_name
        self.params = params
        self.value = value
    def visit(self, operator):
        obj = operator.registry(self.object_node.visit(operator))
        if operator.error: return operator

        if isinstance(obj, TList) or isinstance(obj, TTuple) or isinstance(obj, TDict):
            if self.method_name == "append" and isinstance(obj, TList):
                if len(self.params) != 1:
                    return operator.fail(Error("Metodo 'append' recebe exatamente 1 argumento"))
                value = operator.registry(self.params[0].visit(operator))
                if operator.error: return operator
                obj.appendItem(value)
                return operator.success(obj)
                
            if self.method_name == "get":
                chave = operator.registry(self.params.visit(operator))
                if operator.error: return operator
                valor = obj.getItem(chave)
                return operator.success(valor)
            
            if self.method_name == "addIndex":
                chave = operator.registry(self.params.visit(operator))
                if operator.error: return operator
                valor = obj.addIndex(chave,self.value)
                return operator.success(valor)
            
        return operator.fail(Error(f"Metodo '{self.method_name}' nao encontrado para o tipo {type(obj).__name__}"))

    def __repr__(self):
        return f"MethodCall({self.method_name}, {self.params})"
