import csv
import numpy as np

with open('initial_data/embeddings.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            industries = np.array(row[3].split(',')).tolist()
            investment_rounds = np.array(row[4].split(',')).tolist()
            break
            # website = row[1]
            # website = row[1]
            # name = row[2]
            # industries = row[3]
            # investment_rounds = row[4]

            # print(np.array(industries)[1])
            # break
