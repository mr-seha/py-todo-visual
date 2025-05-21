from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import numpy as np
import sqlite3


root = Tk()
root.title('Todo List')


user_id = -1
username = ''
db_path = 'data.sqlite'

conn = sqlite3.connect(db_path)
curs = conn.cursor()
query = '''CREATE TABLE IF NOT EXISTS "users"
        ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "username" varchar(255) NOT NULL UNIQUE,
        "password" varchar(255) NOT NULL);

        CREATE TABLE IF NOT EXISTS "tasks"
        ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        "title" varchar(255) NOT NULL,
        "date" TEXT NOT NULL,
        "duration" integer NOT NULL,
        "done_time" integer NOT NULL,
        "user_id" bigint NOT NULL
        REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED);'''


curs.executescript(query)
conn.commit()


def get_state(duration, done_time):
    x = float(done_time) / float(duration)
    if x == 1:
        return "Done"
    else:
        return "Undone"


def end_program():
    conn.close()
    exit(0)


def get_today_date():
    return str(datetime.now()).split()[0]


def get_user_tasks():
    query = f'''SELECT id,title,date,duration,done_time
    FROM tasks WHERE user_id={user_id} ORDER BY date'''
    return curs.execute(query).fetchall()


def first_page():
    root.geometry('400x250')

    def is_username_or_pass_empty():
        if username_entry.get().strip() and pass_entry.get().strip():
            return False
        messagebox.showerror('', 'Username or password is empty!')
        return True

    def get_user_info():
        query = f'''SELECT * FROM users WHERE username="{username_entry.get()}"
        AND password="{pass_entry.get()}" LIMIT 1'''
        return curs.execute(query).fetchone()

    def set_logged_in_user():
        global user_id, username
        user = get_user_info()
        if not user:
            messagebox.showwarning(message='Username or password is wrong!')
        else:
            user_id = user[0]
            username = user[1]
            second_page()

    def register_new_user():
        try:
            query = f'''INSERT INTO users(username, password)
                VALUES("{username_entry.get()}", "{pass_entry.get()}")'''

            curs.execute(query)
            conn.commit()
            messagebox.showinfo(message='New user registered successfully.')

        except sqlite3.IntegrityError as msg:
            messagebox.showerror(message=msg)

    def login_btn_command():
        if not is_username_or_pass_empty():
            set_logged_in_user()

    def register_btn_command():
        if not is_username_or_pass_empty():
            if not get_user_info():
                register_new_user()
            else:
                messagebox.showwarning('', 'Sorry, entered username exists.')

    for i in root.winfo_children():
        i.destroy()

    frame1 = Frame(root)
    frame1.pack()

    Label(frame1, text='Username:').pack()
    username_entry = Entry(frame1)
    username_entry.pack()

    Label(frame1, text='Password:').pack()
    pass_entry = Entry(frame1)
    pass_entry.pack()

    Button(frame1, text='Login', command=login_btn_command).pack(pady=10)

    Button(frame1, text='Register', command=register_btn_command).pack()

    Button(frame1, text='Exit', command=end_program).pack()


def second_page():
    root.geometry('1280x800')

    def create_plot():
        fig = Figure(figsize=(12, 4))

        done_count = curs.execute(f'''SELECT COUNT(*) FROM tasks WHERE
            user_id={user_id} AND duration=done_time''')\
            .fetchone()[0]

        undone_count = curs.execute(f'''SELECT COUNT(*) FROM tasks WHERE
            user_id={user_id} AND done_time<duration''')\
            .fetchone()[0]

        plot1 = fig.add_subplot(131, yticks=range(undone_count+done_count+1))

        def func(pct, allvals):
            absolute = int(np.round(pct/100.*np.sum(allvals)))
            return f"{pct:.1f}% ({absolute:d})"

        plot1.pie((done_count, undone_count+0.000001),
                  autopct=lambda pct: func(
                      pct, (done_count, undone_count+0.000001)),
                  labels=('done', 'undone'),  colors=('skyblue', 'tan'))

        dates = []
        state_count = {
            'Done': [],
            'Undone': [],
        }

        sum = {
            'Undone time': [],
            'Done time': [],
        }

        maximum_days = 3
        tasks = get_user_tasks()
        for i in range(len(tasks)-1, -1, -1):
            task_date = tasks[i][2]
            state = get_state(tasks[i][3], tasks[i][4])
            op_state = 'Done' if state == 'Undone' else 'Undone'
            if task_date not in dates:
                if len(dates) < maximum_days:
                    dates.append(task_date)
                    state_count[state].append(1)
                    state_count[op_state].append(0)

                    sum['Undone time'].append(
                        float(tasks[i][3]) - float(tasks[i][4]))
                    sum['Done time'].append(float(tasks[i][4]))
            else:
                index = dates.index(task_date)
                state_count[state][index] += 1
                sum['Undone time'][index] += float(tasks[i]
                                                   [3] - float(tasks[i][4]))
                sum['Done time'][index] += float(tasks[i][4])

        dates.reverse()
        state_count['Done'].reverse()
        state_count['Undone'].reverse()

        sum['Undone time'].reverse()
        sum['Done time'].reverse()

        colors = {'Undone time': 'coral', 'Done time': 'chartreuse'}

        x = np.arange(len(dates))
        width = 0.2
        multiplier = 0

        plot2 = fig.add_subplot(132,
                                yticks=range(0,
                                             int(max(sum['Undone time'])+max(sum['Done time']))+2, 2))

        bottom = np.zeros(len(dates))

        for state, state_hours in sum.items():
            p = plot2.bar(dates, state_hours, 0.5,
                          label=state, bottom=bottom, color=colors[state])
            bottom += state_hours

            plot2.bar_label(p, label_type='center')

        plot2.set_title('State time per date')

        plot2.set_ylabel('Hours')
        plot2.set_xlabel('Date')

        plot3 = fig.add_subplot(133, yticks=range(
            undone_count+done_count+1))

        for attribute, measurement in state_count.items():
            offset = width * multiplier
            rects = plot3.bar(x + offset, measurement, width, label=attribute)
            plot3.bar_label(rects, padding=3)
            multiplier += 1

        plot3.set_ylabel('Count')
        plot3.set_xlabel('Date')
        plot3.set_title('State per date')
        plot3.set_xticks(x + width, dates)
        plot3.legend(loc='upper left', ncols=2)
        plot3.set_ylim(
            0, max(state_count['Done'] + state_count['Undone'] + [1])+1)

        canvas = FigureCanvasTkAgg(fig, master=frame2)
        canvas.draw()

        canvas.get_tk_widget().grid(row=1, column=0, columnspan=2)

    def delete_item():
        try:
            item_id = tasks_treeview.selection()[0]

            tasks_treeview.delete(item_id)

            curs.execute(f'DELETE FROM tasks WHERE id={item_id}')
            conn.commit()
            create_plot()
            messagebox.showinfo('', 'Selected item deleted successfully.')

        except IndexError:
            messagebox.showerror('', 'Please select an item.')

    def add_item():
        title = title_entry.get().strip()
        duration = duration_entry.get().strip()
        done_time = done_time_entry.get().strip()
        if not done_time:
            done_time = '0'

        if not title:
            messagebox.showwarning('', 'Please enter title.')

        elif not duration:
            messagebox.showwarning('', 'Please enter duration.')

        elif duration.isdigit() and done_time.isdigit():
            if float(done_time) <= float(duration):
                today = get_today_date()

                query = f'''INSERT INTO tasks(title,date,duration,done_time,user_id)
                VALUES("{title}","{today}",{duration},{done_time},{user_id})'''
                curs.execute(query)
                conn.commit()

                inserted_id = curs.lastrowid

                tasks_treeview.insert('', END, iid=inserted_id,
                                      values=(title, get_state(duration, done_time),
                                              duration, done_time, today))
                title_entry.delete(0, 'end')
                duration_entry.delete(0, 'end')
                done_time_entry.delete(0, 'end')
                create_plot()
                messagebox.showinfo('', 'New item added successfully.')

            else:
                messagebox.showwarning(
                    '', 'Time of duration should be bigger than done time.')

        else:
            messagebox.showwarning(
                '', 'Enter number in duration or done time field.')

    def delete_all():
        result = messagebox.askyesno(
            'Delete All', 'Are you sure you want to delete all tasks?')
        if result:
            for item in tasks_treeview.get_children():
                tasks_treeview.delete(item)

            curs.execute(f'DELETE FROM tasks WHERE user_id={user_id}')
            conn.commit()
            if curs.rowcount:
                create_plot()
                messagebox.showinfo('', 'All items deleted successfully.')
            else:
                messagebox.showwarning('', 'There is nothing to delete.')

    def set_done():
        try:
            item_id = tasks_treeview.selection()[0]

            curs.execute(
                f'UPDATE tasks SET done_time=duration WHERE id={item_id}')
            conn.commit()

            item = curs.execute(
                f'SELECT * from tasks WHERE id={item_id}').fetchone()

            tasks_treeview.item(item_id, value=(item[1], get_state(item[3], item[4]),
                                                item[3], item[4], item[2]))
            create_plot()

        except IndexError:
            messagebox.showerror('', 'Please select an item.')

    def change_done_time():
        try:
            item_id = tasks_treeview.selection()[0]

            done_time = done_time_entry.get().strip()

            if not done_time:
                done_time = '0'

            if done_time.isdigit():
                item = curs.execute(
                    f'SELECT * from tasks WHERE id={item_id}').fetchone()

                if float(done_time) <= float(item[3]):
                    curs.execute(
                        f'UPDATE tasks SET done_time={done_time} WHERE id={item_id}')
                    conn.commit()

                    item = curs.execute(
                        f'SELECT * from tasks WHERE id={item_id}').fetchone()

                    tasks_treeview.item(item_id, value=(item[1], get_state(item[3], item[4]),
                                                        item[3], item[4], item[2]))
                    create_plot()
                else:
                    messagebox.showwarning(
                        '', 'Time of duration should be bigger than done time.')
            else:
                messagebox.showwarning(
                    '', 'Please enter a number in done time.')

        except IndexError:
            messagebox.showerror('', 'Please select an item.')

    for i in root.winfo_children():
        i.destroy()
    frame2 = Frame(root)

    frame2.pack()

    left_frame = Frame(frame2)
    left_frame.grid(row=0, column=0, padx=15)

    Label(left_frame, text='title:').pack()

    title_entry = Entry(left_frame)
    title_entry.pack(pady=5)

    Label(left_frame, text='Duration:').pack()

    duration_entry = Entry(left_frame)
    duration_entry.pack(pady=5)

    Label(left_frame, text='Done time:').pack()

    done_time_entry = Entry(left_frame)
    done_time_entry.pack(pady=5)

    Button(left_frame, text='Add', command=add_item).pack(pady=5)

    Button(left_frame, text='Done', command=set_done).pack(pady=5)

    Button(left_frame, text='Change done time',
           command=change_done_time).pack(pady=5)

    Button(left_frame, text='Delete', command=delete_item).pack(pady=5)

    Button(left_frame, text='Delete all', command=delete_all).pack(pady=5)

    Button(left_frame, text='Logout', command=first_page).pack(pady=5)

    tasks_treeview = ttk.Treeview(frame2, selectmode='browse')
    tasks_treeview.grid(row=0, column=1, pady=20)


    tasks_treeview['columns'] = ('1', '2', '3', '4', '5')
    tasks_treeview['show'] = 'headings'

    tasks_treeview.column('1', width=450, anchor='c')
    tasks_treeview.column('2', width=120, anchor='c')
    tasks_treeview.column('3', width=100, anchor='c')
    tasks_treeview.column('4', width=100, anchor='c')
    tasks_treeview.column('5', width=120, anchor='c')

    tasks_treeview.heading('1', text='Title')
    tasks_treeview.heading('2', text='State')
    tasks_treeview.heading('3', text='Duration')
    tasks_treeview.heading('4', text='Done time')
    tasks_treeview.heading('5', text='Date')

    tasks_scrollbar = Scrollbar(frame2, orient='vertical',
                                command=tasks_treeview.yview)
    tasks_scrollbar.grid(row=0, column=2, sticky='ns')

    tasks_treeview.configure(yscrollcommand=tasks_scrollbar.set)

    tasks = get_user_tasks()
    for k in range(len(tasks)):
        tasks_treeview.insert('', END, iid=tasks[k][0],
                              values=(tasks[k][1], get_state(tasks[k][3], tasks[k][4]),
                                      tasks[k][3], tasks[k][4], tasks[k][2]))

    create_plot()


first_page()
root.mainloop()
