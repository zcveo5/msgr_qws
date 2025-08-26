import tkinter as tk


def get_absolute_position(widget):

    # Вычисляем позицию относительно окна
    relative_x = widget.winfo_rootx() - widget.winfo_toplevel().winfo_rootx()
    relative_y = widget.winfo_rooty() - widget.winfo_toplevel().winfo_rooty()

    return relative_x, relative_y


# Пример использования
root = tk.Tk()
root.title("Абсолютные координаты")
root.geometry("400x300")

# Создаем цепочку контейнеров
frame1 = tk.Frame(root, bg="red", width=300, height=200)
frame1.pack(pady=20)

canvas = tk.Canvas(frame1, bg="yellow", width=250, height=150)
canvas.pack(pady=10)

frame2 = tk.Frame(canvas, bg="blue", width=200, height=100)
frame2.pack()

button = tk.Button(frame2, text="Узнать координаты")
button.pack(pady=20)


def show_coordinates():
    x, y = get_absolute_position(button)
    print(f"Абсолютные координаты кнопки относительно окна: x={x}, y={y}")


button.configure(command=show_coordinates)

root.mainloop()