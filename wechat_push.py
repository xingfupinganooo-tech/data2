import os
import sys

print("="*50)
print("?? 环境变量测试")
print("="*50)

A = os.getenv('A')
B = os.getenv('B')
C = os.getenv('C')

print(f"A = {A}")
print(f"B = {B}")
print(f"C = {C}")

if not A or not B or not C:
    print("? 缺少环境变量")
    sys.exit(1)
else:
    print("? 所有环境变量都存在")
    print(f"A 长度: {len(A)}")
    print(f"B 长度: {len(B)}")
    print(f"C 长度: {len(C)}")
