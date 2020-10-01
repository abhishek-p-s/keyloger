from tkinter import *
import tkinter .messagebox as mb

class loginak(Frame):
    def __init__(self,master):
        super().__init__(master)
        self.label_username=Label(self,text='username',font=("Times new roman",15) )
        self.label_password = Label(self, text='password', font=("Times new roman", 15))

        self.entry_username=Entry(self)
        self.entry_password = Entry(self)

        self.label_username.grid(row=0,sticky=E)
        self.label_password.grid(row=1, sticky=E)
        self.label_username.grid(row=0, column=1)
        self.label_username.grid(row=1, column=1)


        self.button=Button(self,text='login',command=self.login)
        self.button.grid(columnspan=2)

        self.pack()

        def login(self):
            username=self.entry_username.get()
            password = self.entry_password.get()

            if(username=='abhishek' and password=="abhishek"):
                mb.showinfo('login', "login successfully...")

            else:
                mb.showinfo('login',"login failed")



ak=Tk()
login = loginak(ak)
ak.mainloop()



