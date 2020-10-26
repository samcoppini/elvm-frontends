#!/usr/bin/env python3

from elvm import *

import argparse
import sys


def generateBottles(module: Module) -> Label:
    lines = []

    for i in range(99, 1, -1):
        lines.append(f"{i} bottles of beer on the wall, {i} bottles of beer")
        lines.append(
            f"Take one down, pass it around, {i - 1} bottle{'s' if i > 2 else ''} of beer on the wall\n"
        )

    lines.append("1 bottle of beer on the wall, 1 bottle of beer.")
    lines.append(
        "Take one down and pass it around, no more bottles of beer on the wall.\n"
    )
    lines.append("No more bottles of beer on the wall, no more bottles of beer.")
    lines.append("Go to the store and buy some more, 99 bottles of beer on the wall.\n")

    return module.addData("\n".join(lines))


def generatePrint(module: Module) -> Label:
    firstInst = module.addInstruction(Op.LOAD, Register.D, Register.B)
    module.addInstruction(Op.JEQ, Register.D, 0, Register.C)
    module.addInstruction(Op.PUTC, src=Register.D)
    module.addInstruction(Op.ADD, Register.B, 1)
    module.addInstruction(Op.JMP, jmp=firstInst.getLabel(module))
    return firstInst.getLabel(module)


def compileToEir(code: str) -> str:
    module = Module()

    jmpToMain = module.addInstruction(Op.JMP)

    printLabel = generatePrint(module)
    helloLabel = module.addData("Hello, World!\n")
    quineLabel = module.addData(code)
    beerLabel = generateBottles(module)

    jmpToMain.jmp = Value(module.addInstruction(Op.DUMP).getLabel(module))

    for c in code:
        if c == "H":
            module.addInstruction(Op.MOV, Register.B, helloLabel)
            retInst = module.addInstruction(Op.MOV, Register.C)
            module.addInstruction(Op.JMP, jmp=printLabel)
            nop = module.addInstruction(Op.DUMP)
            retInst.src = Value(nop.getLabel(module))
        elif c == "Q":
            module.addInstruction(Op.MOV, Register.B, quineLabel)
            retInst = module.addInstruction(Op.MOV, Register.C)
            module.addInstruction(Op.JMP, jmp=printLabel)
            nop = module.addInstruction(Op.DUMP)
            retInst.src = Value(nop.getLabel(module))
        elif c == "9":
            module.addInstruction(Op.MOV, Register.B, beerLabel)
            retInst = module.addInstruction(Op.MOV, Register.C)
            module.addInstruction(Op.JMP, jmp=printLabel)
            nop = module.addInstruction(Op.DUMP)
            retInst.src = Value(nop.getLabel(module))
        elif c == "+":
            module.addInstruction(Op.ADD, Register.A, 1)

    module.addInstruction(Op.EXIT)

    return module.compile()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compiles HQ9+ to ELVM EIR")
    parser.add_argument(
        "inFile",
        nargs="?",
        type=str,
        help="The HQ9+ file to compile. Will use stdin instead if not provided",
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
