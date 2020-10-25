#!/usr/bin/env python3

from elvm import *

import argparse
import sys
from typing import Tuple

NEGATIVE_ONE = (2 ** 24) - 1


def createCheckFunc(module: Module) -> Tuple[Label, Label]:
    checkNeg = module.addInstruction(Op.JEQ, Register.A, NEGATIVE_ONE)
    check256 = module.addInstruction(Op.JNE, Register.A, 256, Register.B)
    setInst = module.addInstruction(Op.MOV, Register.A, 0)
    module.addInstruction(Op.JMP, jmp=Register.B)
    checkNeg.jmp = Value(setInst.getLabel(module))
    return checkNeg.getLabel(module), check256.getLabel(module)


def createSquareFunc(module: Module, check256: Label) -> Label:
    squareStart = module.addInstruction(Op.JEQ, Register.A, 0, Register.B)
    module.addInstruction(Op.MOV, Register.C, Register.A)
    module.addInstruction(Op.MOV, Register.D, Register.A)
    module.addInstruction(Op.MOV, Register.A, 0)
    loopStart = module.addInstruction(Op.ADD, Register.A, Register.C)
    module.addInstruction(Op.SUB, Register.D, 1)
    module.addInstruction(Op.JNE, Register.D, 0, loopStart.getLabel(module))
    module.addInstruction(Op.JMP, jmp=check256)
    return squareStart.getLabel(module)


def createOutputFunc(module: Module) -> Label:
    outputStart = module.addInstruction(Op.MOV, Register.SP, 1)
    module.addInstruction(Op.MOV, Register.C, 1)
    module.addInstruction(Op.STORE, Register.C, Register.SP)
    loopBegin = module.addInstruction(Op.JGT, Register.C, Register.A)
    digitLoop = module.addInstruction(Op.ADD, Register.C, Register.C)
    module.addInstruction(Op.MOV, Register.D, Register.C)
    module.addInstruction(Op.ADD, Register.C, Register.C)
    module.addInstruction(Op.ADD, Register.C, Register.C)
    module.addInstruction(Op.ADD, Register.C, Register.D)
    innerCheck = module.addInstruction(Op.JGT, Register.C, Register.A)
    module.addInstruction(Op.ADD, Register.SP, 1)
    module.addInstruction(Op.STORE, Register.SP, Register.C)
    module.addInstruction(Op.JMP, jmp=digitLoop.getLabel(module))
    digitEnd = module.addInstruction(Op.MOV, Register.C, Register.A)
    loopBegin.jmp = Value(digitEnd.getLabel(module))
    innerCheck.jmp = Value(digitEnd.getLabel(module))
    printLoop = module.addInstruction(Op.LOAD, Register.D, Register.SP)
    module.addInstruction(Op.MOV, Register.BP, 48)
    printCheck = module.addInstruction(Op.JLT, Register.C, Register.D)
    digitAdd = module.addInstruction(Op.ADD, Register.BP, 1)
    module.addInstruction(Op.SUB, Register.C, Register.D)
    module.addInstruction(Op.JGE, Register.C, Register.D, digitAdd.getLabel(module))
    gotDigit = module.addInstruction(Op.PUTC, Register.BP)
    printCheck.jmp = Value(gotDigit.getLabel(module))
    module.addInstruction(Op.SUB, Register.SP, 1)
    module.addInstruction(Op.JNE, Register.SP, 0, printLoop.getLabel(module))
    module.addInstruction(Op.PUTC, 10)
    module.addInstruction(Op.JMP, Register.B)
    return outputStart.getLabel(module)


def compileToEir(code: str) -> str:
    module = Module()

    jmpToMain = module.addInstruction(Op.JMP)
    checkBoth, check256 = createCheckFunc(module)
    squareFunc = createSquareFunc(module, check256)
    outputFunc = createOutputFunc(module)

    main = module.addInstruction(Op.DUMP)
    jmpToMain.jmp = Value(main.getLabel(module))

    for c in code:
        if c == "i":
            module.addInstruction(Op.ADD, Register.A, 1)
            ret = module.addInstruction(Op.MOV, Register.B)
            module.addInstruction(Op.JMP, jmp=check256)
            ret.src = Value(module.addInstruction(Op.DUMP).getLabel(module))
        elif c == "d":
            module.addInstruction(Op.SUB, Register.A, 1)
            ret = module.addInstruction(Op.MOV, Register.B)
            module.addInstruction(Op.JMP, jmp=checkBoth)
            ret.src = Value(module.addInstruction(Op.DUMP).getLabel(module))
        elif c == "s":
            ret = module.addInstruction(Op.MOV, Register.B)
            module.addInstruction(Op.JMP, jmp=squareFunc)
            ret.src = Value(module.addInstruction(Op.DUMP).getLabel(module))
        elif c == "o":
            ret = module.addInstruction(Op.MOV, Register.B)
            module.addInstruction(Op.JMP, jmp=outputFunc)
            ret.src = Value(module.addInstruction(Op.DUMP).getLabel(module))

    module.addInstruction(Op.EXIT)

    return module.compile()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compiles deadfish to ELVM EIR")
    parser.add_argument(
        "inFile",
        nargs="?",
        type=str,
        help="The deadfish file to compile. Will use stdin instead if not provided",
    )
    parser.add_argument(
        "-o,--output",
        dest="outFile",
        type=str,
        help="The file to write the compiled EIR to",
    )

    args = parser.parse_args()

    inFile = open(args.inFile, "r") if args.inFile else sys.stdin
    outFile = open(args.outFile, "w") if args.outFile else sys.stdout

    outFile.write(compileToEir(inFile.read()))


if __name__ == "__main__":
    main()
