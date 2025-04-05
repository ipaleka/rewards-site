import pandas as pd

input_file = 'contributions.xlsx'
output_file = 'contributions.csv'
legacy_contributions = 'legacy_contributions.csv'

def convert_and_clean_excel(input_file, output_file, legacy_contributions):
    df = pd.read_excel(input_file, sheet_name=3, header=None).iloc[2:]
    
    df.fillna('NULL', inplace=True)
    
    df.drop(columns=[4, 11, 12, 13, 14, 15, 16], inplace=True)
    
    df = df[~df[0].str.startswith("Period below")]

    df = df.map(lambda x: str(x).replace(' 00:00:00', ''))

    df.loc[df[1] == '45276', 1] = '2023-12-16'
    df.loc[df[2] == '45303', 2] = '2024-01-12'
    df.loc[df[2] == 'Legal entity research', 6] = '[AT] Admin Task'
    df.loc[df[2] == 'Legal entity research', 2] = 'NULL'
    df.loc[df[1] == 'NULL', 1] = '2021-12-10' # Legal entity, add date (assign to cycle)
    df.loc[df[2] == 'NULL', 2] = '2021-12-31' # Legal entity, add date (assign to cycle)


    df = df[~df[0].str.startswith("NULL")] # Clean rows where first column is 'NULL'

    # in this part we are moving a historic cycle appended at the end of the file to where it should be, chronologically
    MOVED_CYCLE_LENGTH = 66 # constant length of the historic cycle
    df_len = len(df.index) - 1

    replacement_index = df_len - MOVED_CYCLE_LENGTH
    
    print("DF length: " + str(len(df.index)))

    df1 = df.iloc[:855] # start part
    df2 = df.iloc[replacement_index:] # Part to cut and insert
    df3 = df.iloc[855:replacement_index] # final part

    df = pd.concat([df1, df2, df3])
    df[0] = df[0].str.strip()  # Remove leading and trailing spaces from column 0

    # full csv export for debugging
    df.to_csv('fullcsv.csv', index=False, header=None, na_rep='NULL')

    # FINAL EXPORT

    legacy_df = df.iloc[:82]
    df = df.iloc[82:]

    df.to_csv(output_file, index=False, header=None, na_rep='NULL')
    legacy_df.to_csv(legacy_contributions, index=False, header=None, na_rep='NULL')

convert_and_clean_excel(input_file, output_file, legacy_contributions)