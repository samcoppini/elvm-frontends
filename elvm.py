#!/usr/bin/env python3

from enum import Enum
import json
from typing import Dict, List, Union


class Register(Enum):
    A = 1
    B = 2
    C = 3
    D = 4
    SP = 5
    BP = 6


class Op(Enum):
    MOV = 0
    ADD = 1
    SUB = 2
    LOAD = 3
    STORE = 4
    PUTC = 5
    GETC = 6
    EXIT = 7
    JEQ = 8
    JNE = 9
    JLT = 10
    JGT = 11
    JLE = 12
    JGE = 13
    JMP = 14
    EQ = 15
    NE = 16
    LT = 17
    GT = 18
    LE = 19
    GE = 20
    DUMP = 21


ValueType = Union["Label", Register, int]


class Value:
    def __init__(self, data: ValueType) -> None:
        self.data = data

    def compile(self) -> str:
        if type(self.data) is Register:
            return self.data.name
        elif type(self.data) is Label:
            return f".L{self.data.num}"
        else:
            return str(self.data)


class Instruction:
    def __init__(
        self, op: Op, dst: Value = None, src: Value = None, jmp: Value = None
    ) -> None:
        self.op = op
        self.dst = dst
        self.src = src
        self.jmp = jmp
        self.label: "Label" = None

    def getLabel(self, module: "Module") -> "Label":
        if self.label is None:
            self.label = module.makeLabel(self)
        return self.label

    def compile(self) -> str:
        s = [self.op.name.lower()]

        # STORE is a special case, because it has a swapped dst/src order
        if self.op == Op.STORE:
            s.append(self.src.compile())
            s.append(self.dst.compile())
        else:
            if self.jmp is not None:
                s.append(self.jmp.compile())
            if self.dst is not None:
                s.append(self.dst.compile())
            if self.src is not None:
                s.append(self.src.compile())

        return f'{self.label.compile() if self.label else ""}{s[0]} {", ".join(s[1:])}'


class Label:
    def __init__(self, labelled: Union[int, str, Instruction], num: int) -> None:
        self.labelled = labelled
        self.num = num

    def compile(self) -> str:
        if type(self.labelled) == int:
            return f".L{self.num}: .long {self.labelled}"
        elif type(self.labelled) == str:
            return f'.L{self.num}: .string "{json.dumps(self.labelled)}"'
        else:
            return f".L{self.num}: "


class Module:
    def __init__(self) -> None:
        self.insts: List[Instruction] = []
        self.data: List[Label] = []
        self.curLabel = 0

    def addInstruction(
        self,
        op: Op,
        dst: ValueType = None,
        src: ValueType = None,
        jmp: ValueType = None,
    ) -> Instruction:
        dst = Value(dst) if dst is not None else dst
        src = Value(src) if src is not None else src
        jmp = Value(jmp) if jmp is not None else jmp
        self.insts.append(Instruction(op, dst, src, jmp))
        return self.insts[-1]

    def makeLabel(self, inst: Instruction) -> Label:
        if inst.label is not None:
            return inst.label

        labelNum = self.curLabel
        self.curLabel += 1
        inst.label = Label(inst, labelNum)
        return inst.label

    def addData(self, data: Union[int, str]) -> Label:
        label = self.curLabel
        self.curLabel += 1
        self.data.append(Label(data, label))
        return self.data[label]

    def compile(self) -> str:
        lines: List[str] = []
        lines.append(".data")

        for data in self.data:
            lines.append(f" {data.compile()}")

        lines.append(".text")
        for inst in self.insts:
            lines.append(f" {inst.compile()}")

        return "\n".join(lines) + "\n"
