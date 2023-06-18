import pandas as pd
import json
from datetime import datetime

def convert_excel_to_json(file_path, output_file_path):
    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(file_path, skiprows=[0])
    print(df)
    

    date_format = '%Y-%m-%d Kl. %H'
    
    prices = {}
    for _, row in df.iterrows():
        # Make sence out of data 2022-12-01 Kl. 00-01
        # Time expecpt -01
        time = row.iloc[0][:-3]
        print(time)
        # 01
        time_to_base = row.iloc[0][-2:]
        # set time from
        time_from = datetime.strptime(time, date_format)
        print(time_from)
        # set time to
        time_to = datetime.strptime(time[:-2] + time_to_base, date_format)
        print(time_to)
        price = {
        "from": time_from.isoformat(),
        "to" : time_to.isoformat(),
        "NO1": row.iloc[1],
        "NO2": row.iloc[2],
        "NO3": row.iloc[3],
        "NO4": row.iloc[4],
        "NO5": row.iloc[5],
        }
        prices[price['from']] = price
    # Convert the DataFrame to JSON
    #json_data = df.to_json(orient='records', indent=2)
    # Save the JSON data to a file
    with open(output_file_path, 'w') as f:
        json.dump(prices,f, indent=4, sort_keys=True)

    return prices

json_data = convert_excel_to_json('data/spotpriser.xlsx', 'data/spotpriser.json')
#print(json_data)