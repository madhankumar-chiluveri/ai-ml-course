import pandas as pd

# string_data = ["A","B","C"]
# number_data =[1,2,3]
# Boolean_Data = [True,False,True]
# List_data = [[1,2],[3,4],[5,6]]

# sdata=pd.Series(string_data)
# ndata=pd.Series(number_data)
# bdata=pd.Series(Boolean_Data)
# ldata=pd.Series(List_data)

# print(sdata,"\n")
# print(ndata,"\n")
# print(bdata,"\n")
# print(ldata,"\n")

df_csv =pd.read_csv("C:/Users/rohit_25iuc97/Downloads/people-100.csv",index_col="First Name")

# df_json =pd.read_json("C:/Users/rohit_25iuc97/Downloads/Users.json")

# print(df_csv["First Name"].to_string())

# print(df_csv[df_csv["Job Title"]=="Games developer"].to_string())

print(df_csv.loc[["Lori","Steve"],["Phone","Job Title"]])

# Name=input("Enter a Name : ")

# try:
    # print(df_csv.loc[])
# except:
    # print("Name not found ",Name)

# print(df_csv.head())
# print(df_json.head())
