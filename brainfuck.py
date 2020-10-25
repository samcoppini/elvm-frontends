#!/usr/bin/env python3

from elvm import *

import argparse
from collections import defaultdict
import sys
from typing import List


def compileToEir(code: str) -> str:
    module = Module()

    module.addInstruction(Op.MOV, Register.A, 1)

    changes: Dict[int, int] = defaultdict(int)
    curMove = 0
    loopStarts: List[Instruction] = []

    def pushChanges():
        lastMove = 0
        for move, change in changes.items():
            if change != 0:
                if move - lastMove > 0:
                    module.addInstruction(Op.ADD, Register.A, move - lastMove)
                elif lastMove - move > 0:
                    module.addInstruction(Op.SUB, Register.A, lastMove - move)
                module.addInstruction(Op.LOAD, Register.B, Register.A)
                module.addInstruction(Op.ADD, Register.B, change % 256)
                overflowCheck = module.addInstruction(Op.JLT, Register.B, 256)
                module.addInstruction(Op.SUB, Register.B, 256)
                store = module.addInstruction(Op.STORE, Register.A, Register.B)
                overflowCheck.jmp = Value(store.getLabel(module))
                lastMove = move
        if lastMove > curMove:
            module.addInstruction(Op.SUB, Register.A, lastMove - curMove)
        elif curMove > lastMove:
            module.addInstruction(Op.ADD, Register.A, curMove - lastMove)
        changes.clear()

    for c in code:
        if c == ">":
            curMove += 1
        elif c == "<":
            curMove -= 1
        elif c == "+":
            changes[curMove] += 1
        elif c == "-":
            changes[curMove] -= 1
        elif c == ".":
            pushChanges()
            curMove = 0
            module.addInstruction(Op.LOAD, Register.B, Register.A)
            module.addInstruction(Op.PUTC, src=Register.B)
        elif c == ",":
            pushChanges()
            curMove = 0
            module.addInstruction(Op.GETC, Register.B)
            module.addInstruction(Op.STORE, Register.A, Register.B)
        elif c == "[":
            pushChanges()
            curMove = 0
            module.addInstruction(Op.LOAD, Register.B, Register.A)
            loopStarts.append(module.addInstruction(Op.JEQ, Register.B, 0))
        elif c == "]":
            pushChanges()
            curMove = 0
            if not loopStarts:
                raise Exception("Unmatched ]")
            loopStart = loopStarts.pop()
            module.addInstruction(Op.LOAD, Register.B, Register.A)
            loopEnd = module.addInstruction(
                Op.JNE, Register.B, 0, loopStart.getLabel(module)
            )
            loopStart.jmp = Value(loopEnd.getLabel(module))

    if loopStarts:
        raise Exception("Unmatched [")

    module.addInstruction(Op.EXIT)

    return module.compile()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compiles brainfuck to ELVM EIR")
    parser.add_argument(
        "inFile",
        nargs="?",
        type=str,
        help="The brainfuck file to compile. Will use stdin instead if not provided",
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
