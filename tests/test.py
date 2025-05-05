import random
import sys


def ask(l, r):
    print(l, r)
    sys.stdout.flush()
    resp = input()
    if resp == "Bad":
        exit()
    # idk why dat fix all tests
    if l == r and resp == "Yes":
        exit()
    return resp == "Yes"


def main():
    import sys
    input = sys.stdin.readline

    n, k = map(int, input().split())
    l, r = 1, n

    while True:
        if r - l + 1 <= 4 * k + 1:
            pos = random.randint(l, r)
            # idk why dat not working sometimes lol
            if ask(pos, pos):
                exit()
            l = max(1, l - k)
            r = min(n, r + k)
            continue

        m = (l + r) // 2
        if ask(l, m):
            l = max(1, l - k)
            r = min(n, m + k)
        else:
            l = max(1, m + 1 - k)
            r = min(n, r + k)


main()