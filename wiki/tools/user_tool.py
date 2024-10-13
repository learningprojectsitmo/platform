import io
import sys
import csv

file_name = "bachelor.csv"  # change on your file path
role = "Bachelor"  # Admin  Master Lecturer Bachelor
HEADER = "name,number_groups,email,login, academic_degree, ear,  Groups,telegram_url\n"
groups = ""
filedata = ""
academic_degree = "bachelor"  # bachelor, master, aspirant

if role == "Admin":
    groups = "Learning projects / Admin"
elif role == "Master":
    groups = "Learning projects / Master"
    academic_degree = "master"
elif role == "Lecturer":
    groups = "Learning projects / Lecturer"
else:
    groups = "Learning projects / Bachelor"
    academic_degree = "bachelor"

ear = 2023

with open(file_name, 'r') as f:
    reader = csv.reader(f, delimiter=',')
    filedata += HEADER
    for i, line in enumerate(reader):
        if line[0] == 'ФИО':
            continue
            print(line[0])

        fio = line[0].split(",")[0]
        email = line[1].split(",")[0]
        tg = line[2].split(",")[0]
        number_gr = line[3].split(",")[0]

        set = "1"
        # HEADER ="name,number_groups,email,login, academic_degree, ear,  Groups\n"
        set = fio + ","
        set += number_gr + ","
        set += email + ","
        set += email + ","
        set += academic_degree + ","
        set += str(ear) + ","
        set += groups + ","
        set += tg.replace("@", "https://t.me/")

        if set != "1":
            filedata += set + "\n"

# Write the file out again
with open("odoo-19-{}.csv".format(role), 'w') as file:
    file.write(filedata)
file.close()
