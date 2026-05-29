# Вопрос 6 (понимание изменяемых объектов)


# task1 ={"title": "купить молоко", "done": False}
# task2 = task1
# task2["title"] = "Купить хлеб"

# print(task1["title"])

# print(task1 is task2)
# print(id(task1), id(task2)) 


# Вопрос 7 (отличие параметров функций)

# def test(a, b):
#     a = a + 1
#     b.append(100)
#     # print(a,b)
    
# x = 5
# y = [1,2,3]
# test(x,y)
# print(x,y)

# c = x + 10
# d = [5,6,7]

# test(c,d)


# def change(c, d):
#     c = 100
#     d.append(200)

# m = 10
# n = [1, 2, 3]
# change(m, n)
# print(m, n)  # что выведет?


# def change(c, d):
#     c = c + 1
#     d = d + [99]
#     # print(c,d)


# x = 5
# y = [1, 2, 3]
# change(x, y)
# print(x, y)

# a = 100
# b = [10, 20, 30]
# change(a, b)
# print(a,b)

# def test(arr):
#     arr = arr + [99]
#     print(my_list)

# my_list = [1, 2, 3]
# test(my_list)
# print(my_list)


# def find_task_by_title(title):
#     for task in tasks:
#         if task["title"] == title:
#             return task
#     return None

# tasks = [
#     {"title": "купить молоко", "done": False},
#     {"title": "выучить Python", "done": False}
# ]

# result1 = find_task_by_title("купить молоко")
# result2 = find_task_by_title("несуществующая задача")

# print(result1)
# print(result2)
# print(result2 is None)

# def get_first_incomplete():
#     for task in tasks:
#         if not task["done"]:
#             return task
#     return None

# tasks = [
#     {"title": "задача 1", "done": True},
#     {"title": "задача 2", "done": False},
#     {"title": "задача 3", "done": False}
# ]

# first = get_first_incomplete()
# if first is None:
#     print("Нет невыполненных задач")
# else:
#     print(f"Первая невыполненная: {first['title']}")