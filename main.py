#! /usr/bin/env python3

import requests
import os
import csv
import json
import colorama
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from colorama import Fore, Style
from bs4 import BeautifulSoup as soup


class Scrape_Site:

    def __init__(self, url):
        self.url = url

    def make_request(self):
        try:
            with requests.get(self.url) as response:
                response.raise_for_status()
                if response.status_code == 200:
                    return soup(response.text, 'html.parser')

        except requests.exceptions.ConnectionError as errc:
            print(Fore.RED, f'[!!] Connection Error! {errc}', Style.RESET_ALL)


class Distro_Watch:

    def __init__(self, locator):
        self.locator = locator

    def ranks(self):
        selection_data = {}
        for values in self.locator.findAll('select', {'name': 'dataspan'}):
            for index, option in enumerate(values.findAll('option'), start=1):
                selection_data[index] = (option['value'], option.text)

        value = Distro_Watch(self.locator).select_dataspan(selection_data)
        return Distro_Watch(self.locator).show_ranks(
                    value[0], value[1],f'https://distrowatch.com/index.php?dataspan={value[0]}')

    def select_dataspan(self, data_set):
        try:
            for element in data_set:
                print(f"{element} - {data_set[element][1]}")
            while True:
                selection = int(input('Select an index: '))
                if selection in data_set:
                    return data_set[selection]
        except KeyboardInterrupt:
            print('\nStopped!')

    def show_ranks(self, span_value, span_name, dataspan_link):
        import pandas as pd
        with open(f"{span_name}.csv", 'w', encoding='utf-8') as f:
            headers = ['Rank', 'Distribution', 'Rating', 'Link']
            writer = csv.writer(f, dialect='excel')

            writer.writerow(headers)
            content = Distro_Watch(Scrape_Site(dataspan_link).make_request()).get_ranks(span_value)

            extracted_data = []
            for distro in content['distributions']:
                extracted_data.append([distro['rank'], distro['name'], distro['rating'], distro['url']])

            writer.writerows(extracted_data)

        df = pd.read_csv(os.path.join(os.getcwd(), f'{span_name}.csv'), index_col=0)
        pd.set_option('display.max_rows', None)
        df.drop(['Link'], axis=1, inplace=True)
        print(df)

    def get_ranks(self, dataspan_value):
        distro_dict = {'info': [], 'distributions': []}
        for table in self.locator.findAll('table', {'style': 'direction: ltr'}):
            for index, tr_attr in enumerate(table.findAll('tr')[3:], start=1):
                distro_dict['distributions'].append({
                        'name': ' '.join(tr_attr.text.split()[1:-1]),
                        'rank': index,
                        'rating': tr_attr.text.split()[-1],
                        'url': f"https://distrowatch.com/table.php?distribution={tr_attr.find('a')['href']}"
                    })
        distro_dict['info'].append({
                'dataspan': dataspan_value,
                'total': len(distro_dict['distributions'])
            })
        with open('DistroRank.json', 'w', encoding='utf-8') as f_source:
            json.dump(distro_dict, f_source, indent=2)
        return distro_dict


if __name__ == '__main__':
    colorama.init()
    
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            description="View Linux Distribution Ranks")

    parser.add_argument('--delete-ranks',
                        action='store_true',
                        help='deletes csv files that are just clutter.')
    
    args = parser.parse_args()
    if args.delete_ranks:
        deleted = []
        for file in os.listdir():
            if file.endswith('.csv'):
                deleted.append(file)
                os.remove(file)
                print(f'Removed: {file}')
        if deleted == []:
            print('There is nothing to delete')
    else:
        Distro_Watch(Scrape_Site('https://distrowatch.com/').make_request()).ranks()
