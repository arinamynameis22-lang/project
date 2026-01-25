model = ""
color = ""
price = 0
buyer = []

print('''
    Добрый день, у Вас есть несколько команд.\n
    1. Поступление нового автомобиля.\n
    2. Перемещение автомобиля со склада в дилерский центр.\n
    3. Продажа автомобиля.\n
    4. Отчет о продажах.\n
    5. Остатки на складе.\n
    6.Информация о продажах.\n
    
    Пример ввода команды: Введите команду: 1
    ''')

my_command = input("Введите команду: ")

while not my_command.isdigit():
    try:
        if my_command.isdgit():
            if 1 <= int(my_command) <= 6:
                my_command = int(my_command)
            elif int(my_command) < 1 and int(my_command) > 6:
                print("Надо ввести число от 1 до 6")
                my_command = input(my_command)
        else:
            print("Надо ввести число от 1 до 6")
                my_command = input(my_command)
    except ValueError:
        print("Ошибка: нужно ввести число.")