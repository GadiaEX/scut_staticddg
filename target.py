try:
    a = 1
except:
    a = 2

if a > 10:
    if a > 90:
        b = a + 1
elif a > 5:
    b = a - 1
else:
    b = 0

a = b + 1
while a < 10:
    a = a + 1
    if a > 20:
        break
    while a > 10:
        a = a + 1
        if a > 15:
            break
x: dict = {}
for key, value in x.items():
    a = a + 1
c = 10
b = c + 1
print(a)


def test_function(a1: int):
    """

    :param a1:
    :return:
    """
    print(a1)
