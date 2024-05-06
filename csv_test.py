import csv

with open('initial_data/venture_capital.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
                website = row[1]
                name = row[2]
                contacts = json.dumps(row[3])
                industries = json.dumps(row[4])
                investment_rounds = json.dumps(row[5])

                insert_vc = '''
                INSERT INTO venture_capital (website, name, contacts, industries, investment_rounds)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (website) DO UPDATE 
                SET name = EXCLUDED.name, 
                    contacts = EXCLUDED.contacts, 
                    industries = EXCLUDED.industries, 
                    investment_rounds = EXCLUDED.investment_rounds;
                '''
                cur.execute(insert_vc, (website, name, contacts, industries, investment_rounds))
                conn.commit()
