import PySimpleGUI as sg
import pymysql
import datetime

# Database setup and connection
conn = pymysql.connect(host='127.0.0.1', user='root', password='123456', database='acceptance_db', charset='UTF8MB4')
cur = conn.cursor()

def find_next_id():
    cur.execute('SELECT id FROM acceptances ORDER BY id')
    existing_ids = [row[0] for row in cur.fetchall()]
    next_id = 1
    while existing_ids and next_id <= max(existing_ids):
        if next_id not in existing_ids:
            return next_id
        next_id += 1
    return next_id if existing_ids else 1

def fetch_acceptance_data():
    sql = 'SELECT id, bank_name, amount, date, deadline FROM acceptances ORDER BY date ASC'
    cur.execute(sql)
    data = [list(row) for row in cur.fetchall()]
    headings = ['Acceptance ID', 'Bank Name', 'Amount', 'Date', 'Deadline']
    return data, headings

def add_acceptance(bank_name, amount, date):
    try:
        next_id = find_next_id()
        date_object = datetime.datetime.strptime(date, '%Y-%m-%d')
        deadline = date_object + datetime.timedelta(days=6*30)
        sql_insert = 'INSERT INTO acceptances (id, bank_name, amount, date, deadline) VALUES (%s, %s, %s, %s, %s)'
        cur.execute(sql_insert, (next_id, bank_name, amount, date, deadline.strftime('%Y-%m-%d')))
        conn.commit()
        sg.popup('Record added successfully!', title='Add Successful')
    except Exception as e:
        conn.rollback()
        sg.popup_error(f'Failed to add record: {e}', title='Error')

def update_acceptance(acceptance_id, bank_name, amount, date):
    try:
        date_object = datetime.datetime.strptime(date, '%Y-%m-%d')
        deadline = date_object + datetime.timedelta(days=6*30)
        sql_update = 'UPDATE acceptances SET bank_name = %s, amount = %s, date = %s, deadline = %s WHERE id = %s'
        cur.execute(sql_update, (bank_name, amount, date, deadline.strftime('%Y-%m-%d'), acceptance_id))
        conn.commit()
        sg.popup('Record updated successfully!', title='Update Successful')
    except Exception as e:
        conn.rollback()
        sg.popup_error(f'Failed to update record: {e}', title='Error')

def delete_acceptance(acceptance_id):
    confirm = sg.popup_yes_no('Are you sure you want to delete this record?', title='Confirm Delete')
    if confirm == 'Yes':
        try:
            sql_delete = 'DELETE FROM acceptances WHERE id = %s'
            cur.execute(sql_delete, (acceptance_id,))
            conn.commit()
            sg.popup('Record deleted successfully!', title='Delete Successful')
        except Exception as e:
            conn.rollback()
            sg.popup_error(f'Failed to delete record: {e}', title='Error')

def delete_all_acceptances():
    confirm = sg.popup_yes_no('Are you sure you want to delete all records?', title='Confirm Delete')
    if confirm == 'Yes':
        try:
            sql_delete_all = 'DELETE FROM acceptances'
            cur.execute(sql_delete_all)
            conn.commit()
            sg.popup('All records have been deleted.', title='Delete Successful')
        except Exception as e:
            conn.rollback()
            sg.popup_error(f'Failed to delete all records: {e}', title='Error')

def fetch_upcoming_deadlines():
    today = datetime.date.today()
    one_month_later = today + datetime.timedelta(days=30)
    sql = 'SELECT id, bank_name, amount, date, deadline FROM acceptances WHERE deadline BETWEEN %s AND %s ORDER BY deadline ASC'
    cur.execute(sql, (today.strftime('%Y-%m-%d'), one_month_later.strftime('%Y-%m-%d')))
    data = [list(row) for row in cur.fetchall()]
    return data

def create_window(theme):
    sg.theme(theme)
    layout = [
        [sg.Text('Acceptance Management System', size=(50, 1), justification='center', font=("Helvetica", 16), relief=sg.RELIEF_RIDGE, key='-TEXT HEADING-', expand_x=True)],
        [sg.Table(values=fetch_acceptance_data()[0], headings=fetch_acceptance_data()[1], max_col_width=30, auto_size_columns=True, display_row_numbers=False, justification='center', num_rows=20, key='-TABLE-', selected_row_colors='red on yellow', enable_events=True, expand_x=True, expand_y=True, vertical_scroll_only=False)],
        [sg.Text('Bank Name:'), sg.Input(s=(20, 1), enable_events=True, key='-BANK-'), sg.Text('Amount:'), sg.Input(s=(10, 1), enable_events=True, key='-AMOUNT-'), sg.Text('Date (YYYY-MM-DD):'), sg.Input(s=(10, 1), enable_events=True, key='-DATE-')],
        [sg.Button('Add'), sg.Button('Update'), sg.Button('Delete'), sg.Button('Remind'), sg.Button('Show All'), sg.Button('Delete All')],
    ]

    window = sg.Window('Acceptance Management System', layout)
    selected_row = None

    while True:
        event, values = window.read(timeout=100)

        if event in (None, 'Exit'):
            break
        elif event == '-TABLE-':
            selected_row = values['-TABLE-'][0] if values['-TABLE-'] else None
        elif event == 'Add':
            bank_name = values['-BANK-']
            amount = values['-AMOUNT-']
            date = values['-DATE-']
            add_acceptance(bank_name, amount, date)
            window['-TABLE-'].update(values=fetch_acceptance_data()[0])  # Refresh the table
        elif event == 'Update':
            if selected_row is not None:
                acceptance_id = fetch_acceptance_data()[0][selected_row][0]
                bank_name = values['-BANK-']
                amount = values['-AMOUNT-']
                date = values['-DATE-']
                confirm = sg.popup_yes_no('Are you sure you want to update this record?', title='Confirm Update')
                if confirm == 'Yes':
                    update_acceptance(acceptance_id, bank_name, amount, date)
                    window['-TABLE-'].update(values=fetch_acceptance_data()[0])  # Refresh the table
        elif event == 'Delete':
            if selected_row is not None:
                acceptance_id = fetch_acceptance_data()[0][selected_row][0]
                delete_acceptance(acceptance_id)
                window["-TABLE-"].update(values=fetch_acceptance_data()[0])
        elif event == 'Delete All':
            delete_all_acceptances()
            window['-TABLE-'].update(values=fetch_acceptance_data()[0])  # Refresh the table after deletion
        elif event == 'Remind':
            upcoming_data = fetch_upcoming_deadlines()
            window['-TABLE-'].update(values=upcoming_data)
        elif event == 'Show All':
            window['-TABLE-'].update(values=fetch_acceptance_data()[0])  # Reset the table to show all records

    window.close()
    cur.close()
    conn.close()

if __name__ == '__main__':
    create_window(sg.theme())
