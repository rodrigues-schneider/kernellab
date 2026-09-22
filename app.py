import ttkbootstrap as ttk
from ttkbootstrap.constants import *

app = ttk.Window(title="Teste ttkbootstrap", themename="darkly")
app.geometry("400x200")

label = ttk.Label(app, text="Interface pronta no Linux!", font=("Helvetica", 14))
label.pack(pady=20)

btn = ttk.Button(app, text="Clique Aqui", bootstyle=SUCCESS)
btn.pack(pady=10)

app.mainloop()