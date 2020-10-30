#!/usr/bin/env python3

from elvm import *

import argparse
import re
import sys

CHUNK_SIZE = 5
STACK_START_LOC = 1 << 23

def chunkCaresAboutVisited(chunk: str) -> bool:
    return '8' in chunk or 'C' in chunk

def validChunk(chunk: str) -> bool:
    return re.match(r'^[0-9A-F]{5}$', chunk)

def compileOp(module: Module, op: str) -> Instruction:
    if op == '0':
        module.addInstruction(Op.STORE, Register.SP, Register.A)
        first = module.addInstruction(Op.ADD, Register.SP, 1)
        module.addInstruction(Op.GETC, Register.A)
    elif op == '1':
        first = module.addInstruction(Op.PUTC, Register.A)
        module.addInstruction(Op.SUB, Register.SP, 1)
        module.addInstruction(Op.LOAD, Register.A, Register.SP)
    elif op == '2':
        first = module.addInstruction(Op.SUB, Register.SP, 1)
        module.addInstruction(Op.LOAD, Register.A, Register.SP)
    elif op == '3':
        first = module.addInstruction(Op.STORE, Register.SP, Register.A)
        module.addInstruction(Op.ADD, Register.SP, 1)
    elif op == '4':
        first = module.addInstruction(Op.SUB, Register.SP, 1)
        module.addInstruction(Op.LOAD, Register.B, Register.SP)
        module.addInstruction(Op.STORE, Register.SP, Register.A)
        module.addInstruction(Op.MOV, Register.A, Register.B)
        module.addInstruction(Op.ADD, Register.SP, 1)
    elif op == '5':
        first = module.addInstruction(Op.ADD, Register.A, 1)
    elif op == '6':
        first = module.addInstruction(Op.SUB, Register.A, 1)
    elif op == '7':
        first = module.addInstruction(Op.SUB, Register.SP, 1)
        module.addInstruction(Op.LOAD, Register.B, Register.SP)
        module.addInstruction(Op.ADD, Register.A, Register.B)
    elif op == '8':
        first = module.addInstruction(Op.JNE, Register.C, 1)
    elif op == '9':
        first = module.addInstruction(Op.SUB, Register.SP, 1)
        module.addInstruction(Op.STORE, Register.BP, Register.A)
        module.addInstruction(Op.LOAD, Register.A, Register.SP)
        module.addInstruction(Op.SUB, Register.BP, 1)
    elif op == 'A':
        first = module.addInstruction(Op.JMP)
    elif op == 'B':
        first = module.addInstruction(Op.EXIT)
    elif op == 'C':
        first = module.addInstruction(Op.JEQ, Register.C, 1)
    elif op == 'D':
        first = module.addInstruction(Op.DUMP)
    elif op == 'E':
        first = module.addInstruction(Op.SUB, Register.SP, 1)
        module.addInstruction(Op.LOAD, Register.B, Register.SP)
        check = module.addInstruction(Op.JGT, Register.B, Register.A)
        module.addInstruction(Op.SUB, Register.A, Register.B)
        jump = module.addInstruction(Op.JMP)
        bIsBigger = module.addInstruction(Op.SUB, Register.B, Register.A)
        check.jmp = Value(bIsBigger.getLabel(module))
        module.addInstruction(Op.MOV, Register.A, Register.B)
        end = module.addInstruction(Op.DUMP)
        jump.jmp = Value(end.getLabel(module))
    elif op == 'F':
        first = module.addInstruction(Op.DUMP)
    return first

def compileChunk(module: Module, chunk: str, stackJumpStart: Label) -> Label:
    if chunkCaresAboutVisited(chunk):
        visitedBit = module.addData(0)
        firstInstruction = module.addInstruction(Op.LOAD, Register.C, visitedBit)
    else:
        firstInstruction = module.addInstruction(Op.DUMP)

    commandStarts: List[Instruction] = []

    for c in chunk:
        commandStarts.append(compileOp(module, c))

    if chunkCaresAboutVisited(chunk):
        lastInst = module.addInstruction(Op.MOV, Register.C, 1)
        module.addInstruction(Op.STORE, visitedBit, Register.C)

        for i in range(CHUNK_SIZE):
            if chunkCaresAboutVisited(chunk[i]):
                if i + 2 >= CHUNK_SIZE:
                    commandStarts[i].jmp = Value(lastInst.getLabel(module))
                else:
                    commandStarts[i].jmp = Value(commandStarts[i + 2].getLabel(module))
            elif chunk[i] == 'A':
                commandStarts[i].jmp = Value(lastInst.getLabel(module))
    else:
        for i in range(CHUNK_SIZE):
            if chunk[i] == 'A':
                commandStarts[i].jmp = Value(stackJumpStart)

    module.addInstruction(Op.JMP, jmp=stackJumpStart)

    return firstInstruction.getLabel(module)

def compileToEir(code: str) -> str:
    module = Module()

    module.addInstruction(Op.MOV, Register.SP, STACK_START_LOC)
    module.addInstruction(Op.MOV, Register.BP, STACK_START_LOC - 1)

    stackJumpStart = module.addInstruction(Op.MOV, Register.B)
    module.addInstruction(Op.ADD, Register.B, Register.A)
    module.addInstruction(Op.LOAD, Register.B, Register.B)
    module.addInstruction(Op.JMP, jmp=Register.B)

    chunks = code.split()
    chunkLabels: List[Label] = []

    for chunk in chunks:
        if not validChunk(chunk):
            raise Exception(f'Invalid chunk: "{chunk}"')

        chunkLabels.append(compileChunk(module, chunk, stackJumpStart.getLabel(module)))

    jumpLabel = module.addData(chunkLabels)
    stackJumpStart.src = Value(jumpLabel)

    return module.compile()

def main() -> int:
    parser = argparse.ArgumentParser(description="Compiles XRF to ELVM EIR")
    parser.add_argument(
        "inFile",
        nargs="?",
        type=str,
        help="The XRF file to compile. Will use stdin instead if not provided",
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
