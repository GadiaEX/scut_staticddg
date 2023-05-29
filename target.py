def myFunction():
    print(a)

myFunction()
a = 1

try:
    a = 1
except:
    a = 2

myNum: list = [0,1]

for each in myNum:
    a = a + int(each)
    for each_num in myNum:
        a = a + int(each_num)
        if a > 10:
            break
    a = a + 3


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




def function():
    a = 1
    print(a)
    if a > 100:
        if a > 99:
            if a > 10:
                a = 0
            a = 10
        a = 100

    print(a)


a = 1
b = 3
c = function(a,b)
